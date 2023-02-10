import logging
import requests
from urllib.parse import urljoin
from akamai.edgegrid import EdgeGridAuth

class Connector:
    def __init__(self, config):
        self.config = config

        # Configure Akamai OPEN authorization using provided token
        self.open_session = requests.Session()
        self.open_session.auth = EdgeGridAuth(
            client_token=config.open_client_token,
            client_secret=config.open_client_secret,
            access_token=config.open_access_token
        )
    
    def run(self):
        # Query Akamai API
        logging.info('Fetching available Akamai Edge locations')
        result = self.open_session.get(urljoin('https://' + self.config.open_host, '/edge-diagnostics/v1/edge-locations'))
        logging.info('Result code [%d]', result.status_code)
        logging.info('Result [%s]', result.json())
