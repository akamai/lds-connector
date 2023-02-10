import yaml
import logging
from dataclasses import dataclass

@dataclass
class NetStorageConfig:
    host: str
    account: str
    cp_code: int
    key: str
    use_ssl: bool

@dataclass
class Config:
    netstorage_config: NetStorageConfig

_KEY_AKAMAI = "akamai"
_KEY_NS = "netstorage"
_KEY_NS_HOST = "host"
_KEY_NS_ACCOUNT = "upload_account"
_KEY_NS_CP_CODE = "cp_code"
_KEY_NS_KEY = "key"
_KEY_NS_SSL = "use_ssl"

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
            use_ssl=ns_yaml_config[_KEY_NS_SSL]
        )

        return Config(
            netstorage_config=ns_config
        )
    except KeyError as keyError:
        logging.error("Configuration file missing key %s", keyError.args[0])
        # TODO: Add termination handler to clean-up
        exit(1)

