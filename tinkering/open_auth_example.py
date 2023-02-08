import logging
import argparse
import yaml
import requests
from akamai.edgegrid import EdgeGridAuth
from urllib.parse import urljoin

CONFIG_KEY_OPEN = "akamai_open_token"
CONFIG_KEY_OPEN_CLIENT_SECRET = "client_secret"
CONFIG_KEY_OPEN_HOST = "host"
CONFIG_KEY_OPEN_ACCESS_TOKEN = "access_token"
CONFIG_KEY_OPEN_CLIENT_TOKEN = "client_token"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog = 'open_auth_example',
        description = 'Authorize with Akamai using OPEN and fetch edge server locations',
        epilog = 'Test epilog')
    parser.add_argument('-c', '--config', required=True, type=argparse.FileType('r'))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logging.info('Parsing configuration from file')

    config = yaml.safe_load(args.config)

    # TODO: Validate YAML file contains required fields

    open_client_secret = config[CONFIG_KEY_OPEN][CONFIG_KEY_OPEN_CLIENT_SECRET]
    open_host = config[CONFIG_KEY_OPEN][CONFIG_KEY_OPEN_HOST]
    open_access_token = config[CONFIG_KEY_OPEN][CONFIG_KEY_OPEN_ACCESS_TOKEN]
    open_client_token = config[CONFIG_KEY_OPEN][CONFIG_KEY_OPEN_CLIENT_TOKEN]

    open_session = requests.Session()
    open_session.auth = EdgeGridAuth(
        client_token=open_client_token,
        client_secret=open_client_secret,
        access_token=open_access_token
    )

    logging.info('Fetching available edge locations')

    result = open_session.get(urljoin('https://' + open_host, '/edge-diagnostics/v1/edge-locations'))
    logging.info('Result code [%d]', result.status_code)
    logging.info('Result [%s]', result.json())
