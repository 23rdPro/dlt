from typing import Tuple, Type
from google.oauth2 import service_account
from google.auth import default as default_credentials
from google.auth.exceptions import DefaultCredentialsError

from dlt.common.typing import StrAny
from dlt.common.configuration import make_configuration, GcpClientCredentials
from dlt.common.configuration.exceptions import ConfigEntryMissingException

from dlt.load.configuration import LoaderClientDwhConfiguration


class BigQueryClientConfiguration(LoaderClientDwhConfiguration):
    CLIENT_TYPE: str = "bigquery"


def configuration(initial_values: StrAny = None) -> Tuple[Type[BigQueryClientConfiguration], Type[GcpClientCredentials]]:

    def maybe_partial_credentials() -> Type[GcpClientCredentials]:
        try:
            return make_configuration(GcpClientCredentials, GcpClientCredentials, initial_values=initial_values)
        except ConfigEntryMissingException as cfex:
            # if config is missing check if credentials can be obtained from defaults
            try:
                default_credentials()
                # if so then return partial so we can access timeouts
                return make_configuration(GcpClientCredentials, GcpClientCredentials, initial_values=initial_values, accept_partial = True)
            except DefaultCredentialsError:
                raise cfex

    return (
        make_configuration(BigQueryClientConfiguration, BigQueryClientConfiguration, initial_values=initial_values),
        # allow partial credentials so the client can fallback to default credentials
        maybe_partial_credentials()
    )
