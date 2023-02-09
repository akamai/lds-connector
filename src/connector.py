import logging
import requests
from urllib.parse import urljoin
from akamai.edgegrid import EdgeGridAuth
from akamai.netstorage import Netstorage, NetstorageError

from config import Config

class Connector:
    def __init__(self, config: Config):
        self.config = config

        # Configure Akamai OPEN authorization using provided token
        # TODO: NetStorage doesn't use OPEN. Remove this
        self.open_session = requests.Session()
        self.open_session.auth = EdgeGridAuth(
            client_token=config.open_client_token,
            client_secret=config.open_client_secret,
            access_token=config.open_access_token
        )

        self.netstorage = Netstorage(
            hostname=self.config.netstorage_host,
            keyname=self.config.netstorage_upload_account,
            key=self.config.netstorage_key,
            ssl=self.config.netstorage_use_ssl
        )
    
    def run(self):
        # Query Akamai API
        logging.info('Fetching available Akamai Edge locations')
        response = self.open_session.get(urljoin('https://' + self.config.open_host, '/edge-diagnostics/v1/edge-locations'))
        logging.info('Response code [%d]', response.status_code)
        logging.info('Response [%s]', response.json())

        # Get file from NetStorage
        logging.info('Fetching available files from Akamai NetStorage')
        (ok, response) = self.netstorage.list('/{0}/'.format(self.config.netstorage_cp_code))
        logging.info('Response ok [%b]', ok) 
        logging.info('Response [%s]', response.text if response != None else None)


