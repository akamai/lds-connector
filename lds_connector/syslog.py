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

import json
import logging
from logging.handlers import SysLogHandler
import socket

from .handler import Handler
from .config import Config
from .edgedns_manager import DnsRecord
from .json import CustomJsonEncoder

class SysLog(Handler):
    _APP_NAME_ARG = 'app_name'

    def __init__(self, config: Config):
        assert config.syslog is not None

        self.config = config
        self.log_queue: list[str] = []
        self.dns_queue: list[str] = []

        self.syslogger = logging.getLogger('SysLogger')
        self.syslogger.propagate = False
        self.syslogger.setLevel(logging.INFO)
        handler = SysLogHandler(
            facility=SysLogHandler.LOG_USER,
            address=(config.syslog.host, config.syslog.port),
            socktype=socket.SOCK_STREAM if config.syslog.use_tcp else socket.SOCK_DGRAM
        )
        handler.append_nul = False
        handler.setFormatter(logging.Formatter(
            f'%(asctime)s {socket.gethostname()} %({SysLog._APP_NAME_ARG})s: %(message)s',
            datefmt='%b %d %H:%M:%S'
        ))
        self.syslogger.addHandler(handler)

    def add_log_line(self, log_line: str) -> None:
        """
        Add log line to SysLog queue

        Parameters:
            log_line (str): The log line.

        Returns: None
        """
        self.log_queue.append(log_line)

    def add_dns_record(self, dns_record: DnsRecord) -> None:
        """
        Add DNS record to SysLog queue

        Parameters:
            dns_record (DnsRecord): The DNS record.

        Returns: None
        """
        dns_json = json.dumps(dns_record, cls=CustomJsonEncoder)
        self.dns_queue.append(dns_json)


    def publish_log_lines(self, force=False) -> bool:
        """
        Publish queued log line SysLog messages to SysLog server

        Parameters:
            force (bool): If true, send queued events. Otherwise, send queued events iff queue size >= batch size.

        Returns:
            bool: If events were published, true. Otherwise, false.
        """
        if len(self.log_queue) == 0:
            return False

        logging.debug('Publishing log lines to SysLog server')
        assert self.config.syslog is not None
        extra_args = {SysLog._APP_NAME_ARG: self.config.syslog.lds_app_name}
        for log_line in self.log_queue:
            self.syslogger.info(log_line, extra=extra_args)

        self.log_queue.clear()
        logging.debug('Published log lines to SysLog server')
        return True

    def publish_dns_records(self, force=False) -> bool:
        """
        Publish queued DNS record SysLog messages to SysLog server 

        Parameters:
            force (bool): If true, send queued events. Otherwise, send queued events iff queue size >= batch size.

        Returns:
            bool: If events were published, true. Otherwise, false.
        """
        if len(self.dns_queue) == 0:
            return False

        logging.debug('Publishing DNS records to SysLog server')
        assert self.config.syslog is not None
        extra_args = {SysLog._APP_NAME_ARG: self.config.syslog.edgedns_app_name}
        for dns_record in self.dns_queue:
            self.syslogger.info(dns_record, extra=extra_args)

        self.dns_queue.clear()
        logging.debug('Published DNS records to SysLog server')
        return True

    def clear(self):
        """
        Clear event queues

        Parameters: None
        Returns: None
        """
        self.log_queue.clear()
        self.dns_queue.clear()
