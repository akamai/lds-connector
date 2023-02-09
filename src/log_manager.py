import os
import gzip
from gzip import GzipFile
import shutil
import logging
import xml.etree.ElementTree as ET

from akamai.netstorage import Netstorage

from config import Config


class _LogFile:
    def __init__(self, filename, size, md5):
        self.filename = filename,
        self.size = size
        self.md5 = md5

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
        if not next_filename:
            return ""

        self._download(next_filename)

        uncompressed_filename = os.path.splitext(next_filename)[0] + ".txt"
        self._uncompress(next_filename, uncompressed_filename)

        # TODO: Delete old files

        return uncompressed_filename

    def _determine_next_log(self) -> str:
        log_files = self._list()

        # TODO: Search through and determine next to download

        return ""

    def _list(self) -> list[_LogFile]:
        logging.info('Listing log files from Akamai NetStorage')

        (ok, response) = self.netstorage.list('/{0}/'.format(self.config.netstorage_cp_code)) # TODO Choose correct directory
        if not ok or response == None:
            logging.error('Failed listing NetStorage files. %s', response.reason if response != None else "") 
            return []
        logging.debug('Finished listing available logs [%s]', response.text)

        root = ET.fromstring(response.text)

        if root.tag != 'list':
            logging.error("NetStorage list API returned unexpected XML")
            return []

        log_files = []
        for child in root:
            if child.tag != 'file' or child.get('type') != 'file':
                logging.debug('Skipping unexpected file [%s]', child.attrib)
                continue

            log_files.append(_LogFile(
                filename=child.get('name'),
                size=child.get('size'),
                md5=child.get('md5')
            ))

        return log_files

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
