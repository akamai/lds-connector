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
from typing import Optional, List

import parse
from akamai.netstorage import Netstorage

from .config import Config
from .log_file import LogFile, LogNameProps


class LogManager:
    """
    Log manager responsible for fetching, preparing, and cleaning up log files
    """
    _RESUME_DATA_PICKLE_FILE_NAME = 'resume_data.pickle'


    def __init__(self, config: Config):
        self.current_log_file: Optional[LogFile] = None

        self.last_log_files_by_zone: dict[str, LogFile] = {}

        self.config = config

        self.netstorage = Netstorage(
            hostname=self.config.lds.ns.host,
            keyname=self.config.lds.ns.account,
            key=self.config.lds.ns.key,
            ssl=self.config.lds.ns.use_ssl
        )

        self.asc_log_files_cache: List[LogFile] = []

        self.resume_data_path = os.path.join(config.lds.log_download_dir, LogManager._RESUME_DATA_PICKLE_FILE_NAME) 

        if os.path.isfile(self.resume_data_path):
            with open(self.resume_data_path, 'rb') as file:
                self.last_log_files_by_zone = pickle.load(file)

    def update_last_log_files(self):
        """
        Save log file progress to disk

        Parameters: None
        Returns: None
        """
        assert self.current_log_file is not None
        
        self.last_log_files_by_zone[self.current_log_file.name_props.customer_id] = self.current_log_file

        logging.debug('Saving resume data: %s', self.current_log_file)

        LogManager._ensure_dir_exists(self.config.lds.log_download_dir)

        with open(self.resume_data_path, 'wb') as file:
            pickle.dump(self.last_log_files_by_zone, file)

        logging.debug('Saved resume data')

    def get_next_log(self) -> Optional[LogFile]:
        """
        Get next log file to process. Determines the next log file to process, downloads it, and uncompresses it. Will
        attempt to resume where left off when run for the first time.

        Parameters: None
        Returns:
            Optional[LogFile]: The log file to process next, if any.
        """
        if self.current_log_file is not None:
            # Normal run
            self.update_last_log_files()

        next_log_file = self._determine_next_log()
        if not next_log_file:
            logging.info('No new log files found')
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

        # Log file list cache is empty. Refresh it.
        if len(self.asc_log_files_cache) == 0:
            log_files = self._list()
            self.asc_log_files_cache = sorted(log_files, key=lambda f: (f.name_props.start_time, f.name_props.part))

        # Log file list cache still empty after refresh. No available log files.
        if len(self.asc_log_files_cache) == 0:
            logging.debug('No log files in NetStorage')
            return None

        next_log_file = None
        while len(self.asc_log_files_cache) != 0:
            log_file = self.asc_log_files_cache.pop(0)

            last_log_file_by_zone: LogFile = self.last_log_files_by_zone.get(log_file.name_props.customer_id)

            if last_log_file_by_zone:
                if log_file.name_props == last_log_file_by_zone.name_props and not last_log_file_by_zone.processed:
                    # Resume where we left off if we've previously attempted this log file before
                    log_file = last_log_file_by_zone
                elif log_file.name_props.start_time < last_log_file_by_zone.name_props.start_time:
                    # Log file's start time is before last file's start time. Skip it
                    continue
                elif log_file.name_props.start_time == last_log_file_by_zone.name_props.start_time \
                    and log_file.name_props.part <= last_log_file_by_zone.name_props.part:
                    # Log file's start time is same as last file's start time.
                    # Log file's part is before last file's part. Skip it
                    continue

            logging.debug('Determined next log file: [%s]', log_file.filename_gz)
            next_log_file = log_file
            break

        if next_log_file is None:
            logging.debug('No unprocessed log files in NetStorage')

        return next_log_file


    def _list(self) -> List[LogFile]:
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
    def _parse_list_response(response_xml: str) -> List[LogFile]:
        """
        Parse the NetStorage list API's XML response into a list of files 

        Parameters:
            response_xml (str): The NetStorage list API's XML response

        Returns:
            List[LogFile]: The available log files
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
