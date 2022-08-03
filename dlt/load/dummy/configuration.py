from typing import Type

from dlt.common.typing import StrAny
from dlt.common.configuration import make_configuration
from dlt.common.dataset_writers import TLoaderFileFormat

from dlt.load.configuration import LoaderClientConfiguration


class DummyClientConfiguration(LoaderClientConfiguration):
    CLIENT_TYPE: str = "dummy"
    LOADER_FILE_FORMAT: TLoaderFileFormat = "jsonl"
    FAIL_PROB: float = 0.0
    RETRY_PROB: float = 0.0
    COMPLETED_PROB: float = 0.0
    TIMEOUT: float = 10.0


def configuration(initial_values: StrAny = None) -> Type[DummyClientConfiguration]:
    return make_configuration(DummyClientConfiguration, DummyClientConfiguration, initial_values=initial_values)
