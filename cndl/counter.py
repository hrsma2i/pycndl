import multiprocessing as mp
import time
from threading import Condition


class TooManyErrorsOccured(Exception):
    pass


class Counter:
    def __init__(
        self,
        total: int,
        log_interval: int = 1,
        threshold_errors: "int | None" = None,
    ) -> None:
        self._processed = 0
        self._success = 0
        self._log_interval = log_interval
        self._total = total
        self._start_at = time.perf_counter()
        self._cond_processed = Condition()
        self._cond_success = Condition()
        self._threshold_errors = threshold_errors or int(total / 2)

    @property
    def processed(self) -> int:
        return self._processed

    @property
    def success(self) -> int:
        return self._success

    @property
    def start_at(self) -> float:
        return self._start_at

    @property
    def total(self) -> int:
        return self._total

    @property
    def percent(self) -> float:
        return self.rate * 100

    @property
    def rate(self) -> float:
        return self.processed / self._total

    @property
    def throughput(self) -> float:
        return self.processed / self.elapsed_sec

    @property
    def elapsed_sec(self) -> float:
        return time.perf_counter() - self.start_at

    @property
    def eta(self) -> str:
        eta = (self._total - self.processed) / self.throughput
        ss = int((eta % 60))
        mm = int((eta / 60) % 60)
        hh = int(eta // (60 * 60))
        return f"ETA={hh:02}:{mm:02}:{ss:02}"

    @property
    def progress(self) -> str:
        return f"{self.percent:.1f}[%]={self.processed}/{self._total}"

    def __repr__(self) -> str:
        return f"{self.progress}, " f"{1/self.throughput:.3f}[sec/iter], " f"{self.eta}"

    def log_progress(self, log_fn=print) -> None:
        if self.processed % self._log_interval == 0 or self.processed == self.total:
            log_fn(self)

    def update_processed(self, d: int) -> None:
        with self._cond_processed:
            self._processed += d

    def update_success(self, d: int) -> None:
        with self._cond_success:
            self._success += d

    def raise_for_many_errors(self) -> None:
        if self.processed - self.success > self._threshold_errors:
            raise TooManyErrorsOccured


class InterProcessCounter(Counter):
    # https://stackoverflow.com/questions/2080660/python-multiprocessing-and-a-shared-counter  # noqa: E501
    def __init__(
        self,
        total: int,
        threshold_errors: "int | None" = None,
    ) -> None:
        self._total = total
        self._processed = mp.Value("i", 0)  # type: ignore
        self._success = mp.Value("i", 0)  # type: ignore
        self._start_at = time.perf_counter()
        self._threshold_errors = threshold_errors or int(total / 2)

    @property
    def processed(self) -> int:
        return self._processed.value  # type: ignore

    @property
    def success(self) -> int:
        return self._success.value  # type: ignore

    def update_processed(self, d: int) -> None:
        with self._processed.get_lock():  # type:ignore
            self._processed.value += d  # type: ignore

    def update_success(self, d: int) -> None:
        with self._success.get_lock():  # type:ignore
            self._success.value += d  # type:ignore
