import yaml
import logging

class Config:
    KEY_OPEN = "akamai_open_token"
    KEY_OPEN_CLIENT_SECRET = "client_secret"
    KEY_OPEN_HOST = "host"
    KEY_OPEN_ACCESS_TOKEN = "access_token"
    KEY_OPEN_CLIENT_TOKEN = "client_token"

    KEY_SPLUNK = "splunk"
    KEY_SPLUNK_ADDRESS = "address"

    def __init__(self, yaml_stream):
        # TODO: Consider migrating this to a static factory. 
        # It's a smell to do too much logic in the constructor
        logging.info('Parsing configuration from YAML file')

        config = yaml.safe_load(yaml_stream)

        try:
            open_config = config[Config.KEY_OPEN]
            self.open_client_secret = open_config.get(Config.KEY_OPEN_CLIENT_SECRET)
            self.open_host = open_config[Config.KEY_OPEN_HOST]
            self.open_access_token = open_config[Config.KEY_OPEN_ACCESS_TOKEN]
            self.open_client_token = open_config[Config.KEY_OPEN_CLIENT_TOKEN]
        except KeyError as keyError:
            logging.error("Configuration file missing key %s", keyError.args[0])
            # TODO: Add termination handler to clean-up
            exit(1)

