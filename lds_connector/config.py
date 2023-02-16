from dataclasses import dataclass
import logging
import os
from typing import Optional
import yaml


@dataclass
class SplunkConfig:
    host: str
    source_type: str
    index: str
    hec_port: int
    hec_token: str
    hec_use_ssl: bool


@dataclass
class NetStorageConfig:
    host: str
    account: str
    cp_code: int
    key: str
    use_ssl: bool
    log_dir: str


@dataclass
class Config:
    splunk_config: SplunkConfig
    netstorage_config: NetStorageConfig
    log_download_dir: str
    timestamp_strptime: str
    timestamp_parse: str
    poll_period_sec: int


_KEY_AKAMAI = "akamai"
_KEY_NS = "netstorage"
_KEY_NS_HOST = "host"
_KEY_NS_ACCOUNT = "upload_account"
_KEY_NS_CP_CODE = "cp_code"
_KEY_NS_KEY = "key"
_KEY_NS_SSL = "use_ssl"
_KEY_NS_LOG_DIR = "log_dir"

_KEY_SPLUNK = "splunk"
_KEY_SPLUNK_HOST = "host"
_KEY_SPLUNK_HEC = "hec"
_KEY_SPLUNK_HEC_PORT = "port"
_KEY_SPLUNK_HEC_TOKEN = "token"
_KEY_SPLUNK_HEC_SSL = "use_ssl"
_KEY_SPLUNK_SOURCE_TYPE = "source_type"
_KEY_SPLUNK_INDEX = "index"

_KEY_CONNECTOR = "connector"
_KEY_CONNECTOR_LOG_DIR = "log_download_dir"
_KEY_CONNECTOR_TIMESTAMP_PARSE = "timestamp_parse"
_KEY_CONNECTOR_TIMESTAMP_STRPTIME = "timestamp_strptime"
_KEY_CONNECTOR_LOG_POLL_PERIOD_SEC = "log_poll_period_sec"


def read_yaml_config(yaml_stream) -> Optional[Config]:
    logging.info('Parsing configuration from YAML file')

    yaml_config = yaml.safe_load(yaml_stream)

    try:
        ns_yaml_config = yaml_config[_KEY_AKAMAI][_KEY_NS]

        ns_config = NetStorageConfig(
            host=ns_yaml_config[_KEY_NS_HOST],
            account=ns_yaml_config[_KEY_NS_ACCOUNT],
            cp_code=ns_yaml_config[_KEY_NS_CP_CODE],
            key=ns_yaml_config[_KEY_NS_KEY],
            use_ssl=ns_yaml_config[_KEY_NS_SSL],
            log_dir=ns_yaml_config[_KEY_NS_LOG_DIR]
        )

        splunk_yaml_config = yaml_config[_KEY_SPLUNK]
        splunk_hec_yaml_config = splunk_yaml_config[_KEY_SPLUNK_HEC]
        splunk_config = SplunkConfig(
            host=splunk_yaml_config[_KEY_SPLUNK_HOST],
            source_type=splunk_yaml_config[_KEY_SPLUNK_SOURCE_TYPE],
            index=splunk_yaml_config[_KEY_SPLUNK_INDEX],
            hec_port=splunk_hec_yaml_config[_KEY_SPLUNK_HEC_PORT],
            hec_token=splunk_hec_yaml_config[_KEY_SPLUNK_HEC_TOKEN],
            hec_use_ssl=splunk_hec_yaml_config[_KEY_SPLUNK_HEC_SSL]
        )

        connector_yaml_config = yaml_config[_KEY_CONNECTOR]

        return Config(
            splunk_config=splunk_config,
            netstorage_config=ns_config,
            log_download_dir=os.path.abspath(connector_yaml_config[_KEY_CONNECTOR_LOG_DIR]),
            timestamp_parse=connector_yaml_config[_KEY_CONNECTOR_TIMESTAMP_PARSE],
            timestamp_strptime=connector_yaml_config[_KEY_CONNECTOR_TIMESTAMP_STRPTIME],
            poll_period_sec=connector_yaml_config[_KEY_CONNECTOR_LOG_POLL_PERIOD_SEC]
        )
    except KeyError as key_error:
        logging.error("Configuration file missing key %s", key_error.args[0])
        return None
