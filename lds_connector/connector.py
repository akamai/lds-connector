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

import logging
import os
from typing import Optional

from .config import Config
from .edgedns_manager import EdgeDnsManager, create_edgedns_manager
from .handler import Handler
from .log_file import LogFile
from .log_manager import LogManager
from .splunk import Splunk
from .syslog import SysLog


class Connector:
    """
    Connector script entry-point
    """

    def __init__(self, config: Config):
        self.config = config
        self.log_manager: LogManager = LogManager(config)
        self.edgedns: Optional[EdgeDnsManager] = create_edgedns_manager(config)
        self.event_handler: Handler

        if config.splunk is not None:
            self.event_handler = Splunk(config)
        if config.syslog is not None:
            self.event_handler = SysLog(config)
        assert self.event_handler is not None

    def process_dns_records(self) -> None:
        """
        Process available DNS records
        """
        if self.edgedns is None:
            return

        logging.info('Processing DNS records')

        records = self.edgedns.get_records()
        # TODO: get_records should return records page-by-page

        for record in records:
            self.event_handler.add_dns_record(record)
            self.event_handler.publish_dns_records()

        self.event_handler.publish_dns_records(force=True)

        logging.info('Processed DNS records')

    def process_log_files(self) -> None:
        """
        Process all available log files
        """
        logging.info('Processing any available log files')

        log_file = self.log_manager.get_next_log()

        if log_file is None:
            logging.info('No available log files')
            return

        while log_file is not None:
            self._process_log_file(log_file)
            log_file = self.log_manager.get_next_log()

        logging.info('Finished processing any available log files')

    def _process_log_file(self, log_file: LogFile) -> None:
        """
        Process a single log file

        Parameters:
            log_file (LogFile): The log file to process

        Returns: None
        """
        logging.info('Processing log file %s', log_file.local_path_txt)
        try:
            with open(log_file.local_path_txt, 'r', encoding='utf-8') as file:
                log_line = file.readline()
                line_number = 0
                while log_line:
                    if not log_line[-1] == '\n':
                        logging.warning('Log line was missing new line. Adding it')
                        log_line += '\n'
                    line_number += 1
                    if line_number > log_file.last_processed_line:
                        # Only handle lines that haven't been processed already

                        self.event_handler.add_log_line(log_line)
                        if self.event_handler.publish_log_lines():
                            log_file.last_processed_line = line_number

                    log_line = file.readline()

                # Publish remaining log lines
                if self.event_handler.publish_log_lines(force=True):
                    log_file.last_processed_line = line_number
                log_file.processed = True

            os.remove(log_file.local_path_txt)
        except Exception as exception:
            logging.error('An unexpected error has occurred processing log file. [%s]. Ignoring and moving on', exception)
        finally:
            if log_file.last_processed_line != -1:
                # Only update resume save file if some lines were processed
                # If multiple log files fail (say Splunk is down), we want to resume at the first failing log file
                self.log_manager.save_resume_data()
            self.event_handler.clear()
            logging.info('Processed log file %s. Finished processing: %s. Last line processed: %d', \
                log_file.local_path_txt, log_file.processed, log_file.last_processed_line)
