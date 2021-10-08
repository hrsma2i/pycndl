import os
from dataclasses import dataclass
from distutils.util import strtobool


@dataclass(frozen=True)
class Env:
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    JSON_LOG: bool = strtobool(os.getenv("JSON_LOG", "true"))
