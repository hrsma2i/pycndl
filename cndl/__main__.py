import io
import threading
import traceback
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, fields
from pathlib import Path
from typing import NewType

import pandas as pd
import requests
import typer
from google.cloud.storage import Blob, Client
from requests.models import Response

from cndl.counter import Counter
from cndl.json_log_formatter import JsonLogFormatter, get_logger


class _JsonLogFormatter(JsonLogFormatter):
    def add_fields(self, log_record, record, message_dict) -> None:  # type: ignore
        log_record["tid"] = threading.get_ident()

        super().add_fields(log_record, record, message_dict)


logger = get_logger(__name__, formatter=_JsonLogFormatter(json_ensure_ascii=False))


@dataclass(frozen=True)
class Input:
    url: str
    filename: "str | None" = None

    @classmethod
    def from_dict(cls, d: dict) -> "Input":
        # safely unpack
        # https: //stackoverflow.com/questions/50873976/how-to-safely-unpack-dict-in-python # noqa: E501
        return cls(*(d.get(f.name) for f in fields(cls)))


Directory = NewType("Directory", str)
GcsDir = NewType("GcsDir", str)


def main() -> None:
    typer.run(download_from_json)


def download_from_json(
    input_json: Path = typer.Argument(
        ..., help="JSON(Lines) which must have url(, filename) as its fields."
    ),
    out: str = typer.Argument(..., help="local directory path or GCS URI"),
    max_retry: int = typer.Option(2),
    max_threads: int = typer.Option(
        100,
        help="ThreadPoolExecutor.max_workers. "
        "The Default value is decided by a performance tuning.",
    ),
) -> None:
    """
    Example:

        cndl input.json ./downloaded/ 2>&1 | tee log-`date +%Y%m%d%H%M%S`.jsonlines

        cndl input.json gs://bucket/downloaded 2>&1 | tee log-`date +%Y%m%d%H%M%S`.jsonlines


    Retry:

        cat log-YYYYmmddHHMMSS.jsonlines | grep 'failed to retry downloading' | jq -c {"url": .url} > input-`date +%Y%m%d%H%M%S`.jsonlines\n
        cndl input-YYYYmmddHHMMSS.jsonlines ./downloaded/ 2>&1 | tee log-`date +%Y%m%d%H%M%S`.jsonlines

    input.json:

        [\n
            {\n
                "url": "http://example_1.jpg"\n
            },\n
            {\n
                "url": "http://example_2.png"\n
            },\n
            ...\n
        ]\n

    More Details:

        https://github.com/hrsma2i/pycndl
    """  # noqa: E501
    df = pd.read_json(input_json, lines="jsonl" in input_json.suffix)
    inputs: list[Input] = df.apply(lambda row: Input.from_dict(row), axis=1).tolist()

    if not out.startswith("gs://"):
        Path(out).mkdir(parents=True, exist_ok=True)

    concurrent_download(
        inputs=inputs,
        out=out,
        counter=Counter(total=len(inputs), progress_interval=100),
        max_retry=max_retry,
        max_threads=max_threads,
    )


def concurrent_download(
    inputs: list[Input],
    out: "Directory | GcsDir",
    counter: Counter,
    max_retry: int = 2,
    max_threads: int = 100,
) -> None:
    client = _get_client()

    futures: list[Future] = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for inp in inputs:
            future = executor.submit(
                download_single,
                inp=inp,
                out=out,
                max_retry=max_retry,
                counter=counter,
                client=client,
            )
            futures.append(future)

    for f in as_completed(futures):
        f.result()

    logger.info(
        f"finished downloading. success/total={counter.success}/{counter.total}"  # noqa: #501
    )


def download_single(
    inp: Input,
    out: "Directory | GcsDir",
    max_retry: int,
    counter: Counter,
    client: Client,
) -> None:
    for i in range(max_retry + 1):
        try:
            url = inp.url
            basename = inp.filename or Path(url).name

            res = requests.get(url, timeout=30)
            res.raise_for_status()

            _save(res, out, basename, client)

            counter.update_success(1)
            break
        except Exception:
            msg = (
                "failed to download" if i < max_retry else "failed to retry downloading"
            )
            logger.warning(
                msg,
                extra={"url": url, "traceback": traceback.format_exc(), "retry": i},
            )

    counter.update_processed(1)

    counter.log_progress(log_fn=logger.info)

    counter.raise_for_many_errors()


def _save(
    res: Response,
    out: "Directory | GcsDir",
    basename: str,
    client: Client = None,
):
    if out.startswith("gs://"):
        blob: Blob = Blob.from_string(f"{out.rstrip('/')}/{basename}")
        buf = io.BytesIO(res.content)
        blob.upload_from_file(buf, client=client)
    else:
        with (Path(out) / basename).open("wb") as f:
            f.write(res.content)


def _get_client() -> Client:
    # Avoid Connection pool is full, discarding connection.
    # https://github.com/googleapis/python-storage/issues/253
    client = Client()
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=128, pool_maxsize=128, max_retries=3, pool_block=True
    )
    client._http.mount("https://", adapter)
    client._http._auth_request.session.mount("https://", adapter)
    return client


if __name__ == "__main__":
    main()
