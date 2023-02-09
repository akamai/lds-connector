import yaml
import logging

class Config:
    # NetStorage has a usage API and a configuration API. 
    # The usage API uses it's own authorization. These keys are managed by NetStorage
    # The configuration API uses the normal OPEN authorization. These keys are managed by Identity + Access Management
    # The NetStorage configuration API isn't likely needed
    KEY_OPEN = "akamai_open_token"
    KEY_OPEN_CLIENT_SECRET = "client_secret"
    KEY_OPEN_HOST = "host"
    KEY_OPEN_ACCESS_TOKEN = "access_token"
    KEY_OPEN_CLIENT_TOKEN = "client_token"

    KEY_NS = "netstorage"
    KEY_NS_HOST = "host"
    KEY_NS_ACCOUNT = "upload_account"
    KEY_NS_CP_CODE = "cp_code"
    KEY_NS_KEY = "key"
    KEY_NS_SSL = "use_ssl"

    KEY_SPLUNK = "splunk"
    KEY_SPLUNK_HEC = "hec"
    KEY_SPLUNK_HEC_HOST = "host"
    KEY_SPLUNK_HEC_PORT = "port"
    KEY_SPLUNK_HEC_TOKEN = "port"
    KEY_SPLUNK_HEC_SSL = "use_ssl"

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

            ns_config = config[Config.KEY_NS]
            self.netstorage_host = ns_config[Config.KEY_NS_HOST]
            self.netstorage_upload_account = ns_config[Config.KEY_NS_ACCOUNT]
            self.netstorage_cp_code = ns_config[Config.KEY_NS_CP_CODE]
            self.netstorage_key = ns_config[Config.KEY_NS_CP_CODE]
            self.netstorage_use_ssl = ns_config[Config.KEY_NS_SSL]

            hec_config = config[Config.KEY_SPLUNK][Config.KEY_SPLUNK_HEC]
            self.hec_host = hec_config[Config.KEY_SPLUNK_HEC_HOST]
            self.hec_port = hec_config[Config.KEY_SPLUNK_HEC_PORT]
            self.hec_token = hec_config[Config.KEY_SPLUNK_HEC_TOKEN]
            self.hec_use_ssl = hec_config[Config.KEY_SPLUNK_HEC_SSL]
        except KeyError as keyError:
            logging.error("Configuration file missing key %s", keyError.args[0])
            # TODO: Add termination handler to clean-up
            exit(1)

