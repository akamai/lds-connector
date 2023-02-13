import os
import gzip
from gzip import GzipFile
import shutil
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Tuple, Optional
import parse
from datetime import datetime, timezone

from requests import Response
from akamai.netstorage import Netstorage

from src.config import Config

@dataclass
class _LogNameProps:
    customer_id: str
    cp_code: int
    format: str
    sorted: bool
    start_time: float
    part: int
    encoding: str

@dataclass
class _LogFile:
    filename: str
    size: int
    md5: str
    uncompressed_filename: str
    name_props: _LogNameProps

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
        self.current_log_file: Optional[_LogFile] = None
        self.last_log_file: Optional[_LogFile] = None

        self.config = config

        self.netstorage = Netstorage(
            hostname=self.config.netstorage_config.host,
            keyname=self.config.netstorage_config.account,
            key=self.config.netstorage_config.key,
            ssl=self.config.netstorage_config.use_ssl
        )

        pass

    def get_next_log(self) -> Optional[_LogFile]:
        # Current file hasn't been completed
        if self.current_log_file != None:
            return self.current_log_file

        next_log_file = self._determine_next_log()
        if not next_log_file:
            logging.info("No log files to process")
            return None

        self._download(next_log_file)

        uncompressed_filename = os.path.splitext(next_log_file.filename)[0] + ".txt"
        self._uncompress(next_log_file.filename, uncompressed_filename)
        next_log_file.uncompressed_filename = uncompressed_filename

        # TODO: Delete GZ

        return next_log_file

    def _determine_next_log(self) -> Optional[_LogFile]:
        log_files = self._list()

        if len(log_files) == 0:
            logging.debug('No log files in NetStorage')
            return None

        ascending_log_files = sorted(log_files, key=lambda f: f.name_props.start_time)

        # No previously processed log file. Pick first available
        if self.last_log_file == None:
            logging.debug('Did not find previously processed log file. Selecting oldest') 
            logging.info('Determined next log file: [{}]', ascending_log_files[0].filename)
            return ascending_log_files[0]

        logging.debug('Previously processed log file [{}]. Selecting oldest after this')
        for log_file in ascending_log_files:
            if log_file.name_props.start_time < self.last_log_file.name_props.start_time:
                # Log file's start time is before last file's start time. Skip it
                continue

            if log_file.name_props.start_time == self.last_log_file.name_props.start_time and log_file.name_props.part <= self.last_log_file.name_props.part:
                # Log file's start time is same as last file's start time. Log file's part is before last file's part. Skip it
                continue

            logging.info('Determined next log file: [{}]', log_file.filename)
            return log_file

        logging.info('No unprocessed log files in NetStorage') 
        return None

    def _list(self) -> list[_LogFile]:
        logging.info('Listing log files from Akamai NetStorage')

        (ok, response) = self.netstorage.list('/{0}/'.format(self.config.netstorage_config.cp_code)) # TODO Choose correct directory
        if not ok or response == None:
            logging.error('Failed listing NetStorage files. %s', response.reason if response != None else "") 
            return []
        logging.debug('Finished listing available logs [%s]', response.text)

        return LogManager._parse_list_response(response)
    
    def _download(self, log_file: _LogFile) -> None:
        logging.debug('Downloading file [%s]', log_file.filename)

        # TODO Perform download to configured directory

        logging.debug('Finished downloading file [%s]', log_file.filename)

    def _uncompress(self, compressed_filename: str, uncompressed_filename: str) -> None:
        logging.debug('Uncompressing file [%s] to [%s]', compressed_filename, uncompressed_filename)

        with gzip.open(compressed_filename, 'rb') as compressed_file:
            assert isinstance(compressed_file, GzipFile)
            with open(uncompressed_filename, 'wb') as uncompressed_file:
                shutil.copyfileobj(compressed_file, uncompressed_file)

        logging.debug('Finished uncompressing file [%s] into [%s]', compressed_filename, uncompressed_filename)

    @staticmethod
    def _parse_list_response(response: Response) -> list[_LogFile]:
        root = ET.fromstring(response.text)

        if root.tag != 'list':
            logging.error("NetStorage list API returned unexpected XML")
            return []

        log_files = []
        for child in root:
            if child.tag != 'file' or child.get('type') != 'file':
                logging.debug('Ignoring non-file in NetStorage: %s %s', child.tag, child.attrib)
                continue

            try:
                filename = child.attrib['name']
                name_props = LogManager._parse_log_name(filename)

                log_files.append(
                    _LogFile(
                        filename=filename,
                        size=int(child.attrib['size']),
                        md5=child.attrib['md5'],
                        uncompressed_filename='', # File has not yet been uncompressed,
                        name_props=name_props
                    )
                )
            except Exception as e:
                logging.error("NetStorage list API response was unexpected: %s", e)
             
        return log_files

    @staticmethod
    def _parse_log_name(filename: str) -> _LogNameProps:
        # TODO: This is not robust to every log format. See https://techdocs.akamai.com/log-delivery/docs/file-names

        parse_result = parse.parse('{ident}_{cp_code:d}.{format}_{sort:l}.{start}-{end}-{part}.{encoding}', filename)
        if not isinstance(parse_result, parse.Result):
            error_message = 'Failed parsing log file name [{}]'.format(filename)
            logging.error(error_message)
            raise ValueError(error_message)

        # Parse start time. End time is ignored
        full_format = '%Y%m%d%H%M%S'
        start_dt = datetime.strptime(parse_result['start'], full_format)
        start_dt = start_dt.replace(tzinfo=timezone.utc)

        return _LogNameProps(
            customer_id=parse_result['ident'],
            cp_code=parse_result['cp_code'],
            format=parse_result['format'],
            sorted=parse_result['sort'] == 'S',
            start_time=start_dt.timestamp(),
            part=parse_result['part'],
            encoding=parse_result['encoding']
        )