from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import requests
from cndl.counter import Counter
from cndl.download import Input, download_loop

SAMPLE = "sample"


class MockResponse:
    def __init__(self, raise_err: bool = False):
        self.content = SAMPLE.encode("utf-8")
        self._raise_err = raise_err

    def raise_for_status(self):
        if self._raise_err:
            raise requests.ConnectionError


def mock_get(url: str, timeout: int, max_err: int) -> MockResponse:
    i = int(url.split("_")[-1].split(".")[0])
    if i < max_err:
        return MockResponse(raise_err=True)
    else:
        return MockResponse()


def test_donwload_images(
    monkeypatch: pytest.MonkeyPatch,
):
    num_contents = 5

    inputs = [Input(url=f"http://example_{i}.png") for i in range(num_contents)]

    max_err = 2
    monkeypatch.setattr(
        requests,
        "get",
        lambda url, timeout: mock_get(url, timeout, max_err),
    )

    with TemporaryDirectory() as tmp_dir:
        download_loop(
            inputs=inputs,
            out=tmp_dir,
            counter=Counter(
                total=len(inputs),
                threshold_errors=len(inputs),
            ),
        )

        paths = list(Path(tmp_dir).glob("*"))

        assert len(paths) == num_contents - max_err, "All contents weren't downloaded."

        with paths[0].open("rb") as f:
            actual = f.read().decode("utf-8")
        assert actual == SAMPLE, "Invalid content."
