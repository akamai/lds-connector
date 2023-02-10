import os
import gzip
from gzip import GzipFile
import shutil
import logging
from akamai.netstorage import Netstorage

from config import Config

'''
LogManager is responsible for the following
- Determining the next log file to download
- Downloading the log file
- Uncompressing the log file
- Cleaning up old files
'''
class LogManager:

    def __init__(self, config: Config):
        # TODO: Persist this to file so script is robust
        self.current_file = None
        self.last_file = None

        self.config = config

        self.netstorage = Netstorage(
            hostname=self.config.netstorage_host,
            keyname=self.config.netstorage_upload_account,
            key=self.config.netstorage_key,
            ssl=self.config.netstorage_use_ssl
        )

        pass

    def get_next_log(self) -> str:
        next_filename = self._determine_next_log()
        self._download(next_filename)

        uncompressed_filename = os.path.splitext(next_filename)[0] + ".txt"
        self._uncompress(next_filename, uncompressed_filename)

        # TODO: Delete old files

        return uncompressed_filename

    def _determine_next_log(self) -> str:
        # TODO
        return ""

    def _list(self): 
        logging.info('Listing log files from Akamai NetStorage')

        (ok, response) = self.netstorage.list('/{0}/'.format(self.config.netstorage_cp_code)) # TODO Choose correct directory
        if not ok or response == None:
            logging.error('Failed listing NetStorage files. %s', response.reason if response != None else "") 
            return
        logging.debug('Finished listing available logs [%s]', response.text)

        # TODO Return list of files

    def _download(self, filename) -> None:
        logging.debug('Downloading file [%s]', filename)

        # TODO Perform download to configured directory

        logging.debug('Finished downloading file [%s]', filename)

    def _uncompress(self, compressed_filename, uncompressed_filename) -> None:
        logging.debug('Uncompressing file [%s] to [%s]', compressed_filename, uncompressed_filename)

        with gzip.open(compressed_filename, 'rb') as compressed_file:
            assert isinstance(compressed_file, GzipFile)
            with open(uncompressed_filename, 'wb') as uncompressed_file:
                shutil.copyfileobj(compressed_file, uncompressed_file)

        logging.debug('Finished uncompressing file [%s] into [%s]', compressed_filename, uncompressed_filename)
