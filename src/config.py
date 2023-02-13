import yaml
import logging
import os
from dataclasses import dataclass

@dataclass
class SplunkConfig:
    hec_host: str
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

_KEY_AKAMAI = "akamai"
_KEY_NS = "netstorage"
_KEY_NS_HOST = "host"
_KEY_NS_ACCOUNT = "upload_account"
_KEY_NS_CP_CODE = "cp_code"
_KEY_NS_KEY = "key"
_KEY_NS_SSL = "use_ssl"
_KEY_NS_LOG_DIR = "log_dir"

_KEY_SPLUNK = "splunk"
_KEY_SPLUNK_HEC = "hec"
_KEY_SPLUNK_HEC_HOST = "host"
_KEY_SPLUNK_HEC_PORT = "port"
_KEY_SPLUNK_HEC_TOKEN = "token"
_KEY_SPLUNK_HEC_SSL = "use_ssl"

_KEY_CONNECTOR = "connector"
_KEY_CONNECTOR_LOG_DIR = "log_download_dir"

def read_yaml_config(yaml_stream):
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

        splunk_yaml_config = yaml_config[_KEY_SPLUNK][_KEY_SPLUNK_HEC]
        splunk_config = SplunkConfig(
            hec_host=splunk_yaml_config[_KEY_SPLUNK_HEC_HOST],
            hec_port=splunk_yaml_config[_KEY_SPLUNK_HEC_PORT],
            hec_token=splunk_yaml_config[_KEY_SPLUNK_HEC_TOKEN],
            hec_use_ssl=splunk_yaml_config[_KEY_SPLUNK_HEC_SSL]
        )

        connector_config = yaml_config[_KEY_CONNECTOR]

        return Config(
            splunk_config=splunk_config,
            netstorage_config=ns_config,
            log_download_dir=os.path.abspath(connector_config[_KEY_CONNECTOR_LOG_DIR])
        )
    except KeyError as keyError:
        logging.error("Configuration file missing key %s", keyError.args[0])
        # TODO: Add termination handler to clean-up
        exit(1)

