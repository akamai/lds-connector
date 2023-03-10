# Original author: Cam Mackintosh <cmackint@akamai.com>
# For more information visit https://developer.akamai.com

# Copyright 2023 Akamai Technologies, Inc. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import gzip
import logging
import os
import pickle
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from gzip import GzipFile
from typing import Optional

import parse
from akamai.netstorage import Netstorage

from .config import Config
from .log_file import LogFile, LogNameProps


class LogManager:
    """
    Log manager responsible for fetching, preparing, and cleaning up log files
    """
    _RESUME_PICKLE_FILE_NAME = 'resume.pickle'

    def __init__(self, config: Config):
        self.current_log_file: Optional[LogFile] = None
        self.last_log_file: Optional[LogFile] = None
        self.resume_log_file: Optional[LogFile] = None

        self.config = config

        self.netstorage = Netstorage(
            hostname=self.config.lds.ns.host,
            keyname=self.config.lds.ns.account,
            key=self.config.lds.ns.key,
            ssl=self.config.lds.ns.use_ssl
        )

        self.resume_path = os.path.join(config.lds.log_download_dir, LogManager._RESUME_PICKLE_FILE_NAME)

        if os.path.isfile(self.resume_path):
            with open(self.resume_path, 'rb') as file:
                self.resume_log_file = pickle.load(file)

    def save_resume_data(self):
        """
        Save log file progress to disk

        Parameters: None
        Returns: None
        """
        assert self.current_log_file is not None

        logging.debug('Saving resume data: %s', self.current_log_file)

        LogManager._ensure_dir_exists(self.config.lds.log_download_dir)

        with open(self.resume_path, 'wb') as file:
            pickle.dump(self.current_log_file, file)

        logging.debug('Saved resume data: %s')

    def get_next_log(self) -> Optional[LogFile]:
        """
        Get next log file to process. Determines the next log file to process, downloads it, and uncompresses it. Will
        attempt to resume where left off when run for the first time.

        Parameters: None
        Returns:
            Optional[LogFile]: The log file to process next, if any.
        """
        logging.info('Getting next log file')

        if self.resume_log_file is not None:
            # First run. Resume log file found
            if self.resume_log_file.processed:
                # Resume log file was fully processed. Use it as last
                logging.info('Found resume data. Last log file fully processed. Resuming processing after it.')
                self.last_log_file = self.resume_log_file
                self.current_log_file = None
                self.resume_log_file = None
            elif os.path.isfile(self.resume_log_file.local_path_txt):
                # Resume log file wasn't fully processed. Use it as current
                logging.info('Found resume data. Last log file wasn\'t fully processed. Resuming processing it.')
                self.last_log_file = None
                self.current_log_file = self.resume_log_file
                self.resume_log_file = None
                return self.current_log_file
            else:
                # Resume log file wasn't fully processed, but log file not found
                # TODO: Consider attempting to re-download the missing file
                logging.warning('Found resume data. Log file was missing. Ignoring resume data. [%s]', 
                    self.resume_log_file.local_path_txt)
                self.last_log_file = None
                self.current_log_file = None
                self.resume_log_file = None
        elif self.current_log_file is not None:
            # Normal run
            self.save_resume_data()
            self.last_log_file = self.current_log_file
            self.current_log_file = None

        next_log_file = self._determine_next_log()
        if not next_log_file:
            logging.info('No log files to process')
            return None

        self._download(next_log_file)

        LogManager._uncompress(next_log_file)

        self._delete_gzip(next_log_file)

        self.current_log_file = next_log_file

        logging.info('Got next log file: %s', next_log_file.filename_gz)

        return next_log_file

    def _determine_next_log(self) -> Optional[LogFile]:
        """
        Determines next log file to process.

        Parameters: None
        Returns:
            Optional[LogFile]: The log file to process next, if any.
        """
        logging.debug('Determining next log file')

        log_files = self._list()

        if len(log_files) == 0:
            logging.debug('No log files in NetStorage')
            return None

        ascending_log_files = sorted(log_files, key=lambda f: (f.name_props.start_time, f.name_props.part))

        # No previously processed log file. Pick first available
        if self.last_log_file is None:
            logging.debug('No previously processed log file. Selecting oldest')
            logging.debug('Determined next log file: [%s]', ascending_log_files[0].filename_gz)
            return ascending_log_files[0]

        logging.debug('Previously processed log file. Selecting oldest after this')
        for log_file in ascending_log_files:
            if log_file.name_props.start_time < self.last_log_file.name_props.start_time:
                # Log file's start time is before last file's start time. Skip it
                continue

            if log_file.name_props.start_time == self.last_log_file.name_props.start_time \
                and log_file.name_props.part <= self.last_log_file.name_props.part:
                # Log file's start time is same as last file's start time.
                # Log file's part is before last file's part. Skip it
                continue

            logging.debug('Determined next log file: [%s]', log_file.filename_gz)
            return log_file

        logging.debug('No unprocessed log files in NetStorage')
        return None

    def _list(self) -> list[LogFile]:
        """
        List available log file in NetStorage.

        Parameters: None
        Returns:
            list[LogFile]: The available log files.
        """
        logging.debug('Fetching available log files list from NetStorage')

        ls_path = f'/{self.config.lds.ns.cp_code}'
        if self.config.lds.ns.log_dir:
            ls_path += f'/{self.config.lds.ns.log_dir}'

        _, response = self.netstorage.list(ls_path)
        if response is None or response.status_code != 200:
            logging.error('Failed listing NetStorage files. %s', response.reason if response is not None else "")
            return []
        logs = LogManager._parse_list_response(response.text)
        logging.debug('Fetched available log files list from NetStorage')
        return logs

    def _download(self, log_file: LogFile) -> None:
        """
        Download a log file from NetStorage

        Parameters:
            log_file (LogFile): The log file to download

        Returns: None
        """
        logging.debug('Downloading log file from NetStorage: [%s]', log_file.filename_gz)

        LogManager._ensure_dir_exists(self.config.lds.log_download_dir)

        local_path_gz = os.path.join(self.config.lds.log_download_dir, log_file.filename_gz)
        self.netstorage.download(log_file.ns_path_gz, local_path_gz)
        log_file.local_path_gz = local_path_gz

        logging.debug('Downloaded log file file from NetStorage: [%s]', log_file.filename_gz)

    @staticmethod
    def _uncompress(log_file: LogFile) -> None:
        """
        Uncompress a log file. 

        Parameters:
            log_file (LogFile): The log file to uncompress. It must have been downloaded.

        Returns: None
        """
        local_path_txt = os.path.splitext(log_file.local_path_gz)[0] + ".txt"

        logging.debug('Uncompressing log file [%s] to [%s]', log_file.local_path_gz, local_path_txt)

        with gzip.open(log_file.local_path_gz, 'rb') as gz_file:
            assert isinstance(gz_file, GzipFile)
            with open(local_path_txt, 'wb') as txt_file:
                shutil.copyfileobj(gz_file, txt_file)

        log_file.local_path_txt = local_path_txt
        logging.debug('Finished uncompressing log file')

    @staticmethod
    def _delete_gzip(log_file: LogFile) -> None:
        os.remove(log_file.local_path_gz)

    @staticmethod
    def _parse_list_response(response_xml: str) -> list[LogFile]:
        """
        Parse the NetStorage list API's XML response into a list of files 

        Parameters:
            response_xml (str): The NetStorage list API's XML response

        Returns:
            list[LogFile]: The available log files
        """

        root = ET.fromstring(response_xml)

        if root.tag != 'list':
            logging.error('NetStorage list API returned unexpected XML: %s', response_xml)
            return []

        log_files = []
        for child in root:
            if child.tag != 'file' or child.get('type') != 'file':
                logging.debug('Ignoring non-file in NetStorage: %s %s', child.tag, child.attrib)
                continue

            try:
                file_path = '/' + child.attrib['name']
                filename = file_path[file_path.rfind('/') + 1:] # TODO: This isn't robust to slashes in the file name
                name_props = LogManager._parse_log_name(filename)

                log_files.append(
                    LogFile(
                        ns_path_gz=file_path,
                        filename_gz=filename,
                        size=int(child.attrib['size']),
                        md5=child.attrib['md5'],
                        name_props=name_props,
                        local_path_gz='',
                        local_path_txt='',
                        last_processed_line=-1,
                        processed=False
                    )
                )
            except KeyError as key_error:
                logging.error('NetStorage list API file was missing key [%s]: %s', key_error, child.attrib)

        return log_files

    @staticmethod
    def _parse_log_name(filename: str) -> LogNameProps:
        """
        Parse the log file names into various properties. The LDS logs are saved with a standard naming convention,
        including properties such as time range, log format, compression type, etc

        Parameters:
            filename (str): The log filename

        Returns:
            LogNameProps: The log file name properties
        """

        # TODO: This is not robust to every log format. See https://techdocs.akamai.com/log-delivery/docs/file-names

        parse_result = parse.parse('{ident}_{cp_code:d}.{format}_{sort:l}.{start}-{end}-{part:d}.{encoding}', filename)
        if not isinstance(parse_result, parse.Result):
            error_message = f'Failed parsing log file name [{filename}]'
            logging.error(error_message)
            raise ValueError(error_message)

        # Parse start time. End time is ignored
        full_format = '%Y%m%d%H%M%S'
        start_dt = datetime.strptime(parse_result['start'], full_format)
        start_dt = start_dt.replace(tzinfo=timezone.utc)

        return LogNameProps(
            customer_id=parse_result['ident'],
            cp_code=parse_result['cp_code'],
            format=parse_result['format'],
            sorted=parse_result['sort'] == 'S',
            start_time=start_dt.timestamp(),
            part=parse_result['part'],
            encoding=parse_result['encoding']
        )
    
    @staticmethod
    def _ensure_dir_exists(path: str):
        if not os.path.isdir(path):
            logging.debug('Creating missing directory: %s', path)
            os.makedirs(path)
