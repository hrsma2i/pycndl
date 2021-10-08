import threading
import traceback
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import NewType

import requests
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


Directory = NewType("Directory", str)
GcsDir = NewType("GcsDir", str)


def download_loop(
    inputs: list[Input],
    out: "Directory | GcsDir",
    counter: Counter,
    max_retry: int = 2,
) -> None:
    futures: list[Future] = []
    with ThreadPoolExecutor() as executor:
        for inp in inputs:
            future = executor.submit(
                _download,
                inp=inp,
                out=out,
                max_retry=max_retry,
                counter=counter,
            )
            futures.append(future)

    for f in as_completed(futures):
        f.result()

    logger.info(
        f"finished downloading. success/total={counter.success}/{counter.total}"  # noqa: #501
    )


def _download(
    inp: Input,
    out: "Directory | GcsDir",
    max_retry: int,
    counter: Counter,
) -> None:
    for i in range(max_retry + 1):
        try:
            url = inp.url
            basename = inp.filename or Path(url).name

            res = requests.get(url, timeout=30)
            res.raise_for_status()

            _save(res, out, basename)

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


def _save(res: Response, out: "Directory | GcsDir", basename: str):
    if out.startswith("gs://"):
        raise NotImplementedError
    else:
        with (Path(out) / basename).open("wb") as f:
            f.write(res.content)
