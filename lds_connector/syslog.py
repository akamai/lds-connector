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
from datetime import datetime, timezone

from .config import *
from .dns_record import DnsRecord
from .handler import Handler
from .json import CustomJsonEncoder
from .log_file import LogEvent
from .syslogger import SysLogger


class SysLog(Handler):
    _ARG_APP_NAME = 'app_name'
    _ARG_LOG_TIME = 'log_time'
    _TIME_FORMAT = '%b %d %H:%M:%S'


    def __init__(self, config: Config):
        assert config.syslog is not None

        self.config: Config = config
        self.log_queue: list[LogEvent] = []
        self.dns_queue: list[str] = []

        protocol = None
        if config.syslog.protocol == SYSLOG_PROTOCOL_UDP:
            protocol = SysLogger.PROTOCOL_UDP
        elif config.syslog.protocol == SYSLOG_PROTOCOL_TCP:
            protocol = SysLogger.PROTOCOL_TCP
        elif config.syslog.protocol == SYSLOG_PROTOCOL_TCP_TLS:
            protocol = SysLogger.PROTOCOL_TCP_TLS
        else:
            assert False, 'Unexpected state. Syslog protocol was unknown: ' + config.syslog.protocol

        delimiter_method = SysLogger.DELIM_NONE
        if config.syslog.delimiter_method == SYSLOG_DELIM_NONE:
            delimiter_method = SysLogger.DELIM_NONE
        elif config.syslog.delimiter_method == SYSLOG_DELIM_LF:
            delimiter_method = SysLogger.DELIM_LF
        elif config.syslog.delimiter_method == SYSLOG_DELIM_CRLF:
            delimiter_method = SysLogger.DELIM_CRLF
        elif config.syslog.delimiter_method == SYSLOG_DELIM_NULL:
            delimiter_method = SysLogger.DELIM_NULL
        elif config.syslog.delimiter_method == SYSLOG_DELIM_OCTET:
            delimiter_method = SysLogger.DELIM_OCTET
        else:
            assert False, 'Unexpected state. Syslog delimiter method was unknown: ' + config.syslog.delimiter_method

        self.syslogger = SysLogger(
            protocol=protocol,
            address=(config.syslog.host, config.syslog.port),
            syslog_flavor=SysLogger.SYSLOG_RFC3164, # TODO Add config option
            facility=SysLogger.FAC_USER,
            delimiter_method=delimiter_method,
            from_host = config.syslog.from_host,
            tls_ca_file=None if config.syslog.tls is None else config.syslog.tls.ca_file,
            tls_check_hostname = True if config.syslog.tls is None else config.syslog.tls.verify
        )


    def add_log_line(self, log_event: LogEvent) -> None:
        """
        Add log line to SysLog queue

        Parameters:
            log_line (str): The log line.

        Returns: None
        """
        self.log_queue.append(log_event)


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
        for log_event in self.log_queue:
            self.syslogger.log_info(self.config.syslog.lds_app_name, log_event.timestamp, log_event.log_line)

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
        assert self.config.syslog.edgedns_app_name is not None
        for dns_record in self.dns_queue:
            self.syslogger.log_info(self.config.syslog.edgedns_app_name, datetime.now(timezone.utc), dns_record)

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
