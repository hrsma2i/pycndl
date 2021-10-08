from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import requests
from cndl.counter import Counter
from cndl.download import Input, download_loop

SAMPLE = "sample"


class MockResponse:
    def __init__(self):
        self.content = SAMPLE.encode("utf-8")
        self.raise_for_status

    def raise_for_status(self):
        pass


def test_donwload_images(monkeypatch: pytest.MonkeyPatch):
    num_contents = 5

    inputs = [Input(url=f"http://example_{i}.png") for i in range(num_contents)]

    monkeypatch.setattr(requests, "get", lambda url, timeout: MockResponse())

    with TemporaryDirectory() as tmp_dir:
        download_loop(
            inputs=inputs,
            out=tmp_dir,
            counter=Counter(total=len(inputs)),
        )
        paths = list(Path(tmp_dir).glob("*"))

        assert len(paths) == num_contents, "All contents weren't downloaded."

        with paths[0].open("rb") as f:
            actual = f.read().decode("utf-8")
        assert actual == SAMPLE, "Invalid content."
