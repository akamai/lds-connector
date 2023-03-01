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
import socket
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import parse
import requests

from .config import Config
from .dns_record import DnsRecord
from .handler import Handler
from .json import CustomJsonEncoder


class Splunk(Handler):
    """
    Splunk log line handler. Responsible for converting log lines to Splunk events
    """
    _HEC_ENDPOINT = '/services/collector/event'
    _TIMEOUT_SEC = 5

    def __init__(self, config: Config):
        self.config = config
        self.log_queue = []
        self.dns_queue = []

    def add_log_line(self, log_line: str) -> None:
        """
        Convert a log line to an HEC event and add it to the queue.

        Parameters:
            log_line (str): The log line.

        Returns: None
        """

        try:
            timestamp_sec = self._parse_timestamp(log_line)
        except ValueError:
            logging.warning('Failed parsing timestamp from logline [%s]', log_line)
            return

        hec_json = {
            'time': timestamp_sec,
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_line
        }
        assert self.config.splunk is not None
        if self.config.splunk.lds_hec.source_type:
            hec_json['sourcetype'] = self.config.splunk.lds_hec.source_type
        if self.config.splunk.lds_hec.index:
            hec_json['index'] = self.config.splunk.lds_hec.index

        self.log_queue.append(hec_json)

    def add_dns_record(self, dns_record: DnsRecord) -> None:
        """
        Convert a DNS record to an HEC event and add it to the queue.

        Parameters:
            dns_record (DnsRecord): The DNS record.

        Returns: None
        """

        hec_json = {
            'time': dns_record.time_fetched_sec,
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': dns_record
        }

        assert self.config.splunk is not None
        assert self.config.splunk.edgedns_hec is not None
        if self.config.splunk.edgedns_hec.source_type:
            hec_json['sourcetype'] = self.config.splunk.edgedns_hec.source_type
        if self.config.splunk.edgedns_hec.index:
            hec_json['index'] = self.config.splunk.edgedns_hec.index

        self.dns_queue.append(hec_json)

    def publish_log_lines(self, force=False) -> bool:
        """
        Publish queued log line HEC events to Splunk HEC

        Parameters:
            force (bool): If true, send queued events. Otherwise, send queued events iff queue size >= batch size.

        Returns:
            bool: If events were published, true. Otherwise, false.
        """
        assert self.config.splunk is not None
        return self._publish(
            queue=self.log_queue,
            batch_size=self.config.splunk.lds_hec.event_batch_size,
            token=self.config.splunk.lds_hec.token,
            force=force)

    def publish_dns_records(self, force=False) -> bool:
        """
        Publish queued DNS record HEC events to Splunk HEC

        Parameters:
            force (bool): If true, send queued events. Otherwise, send queued events iff queue size >= batch size.

        Returns:
            bool: If events were published, true. Otherwise, false.
        """
        assert self.config.splunk is not None
        assert self.config.splunk.edgedns_hec is not None
        return self._publish(
            queue=self.dns_queue,
            batch_size=self.config.splunk.edgedns_hec.event_batch_size,
            token=self.config.splunk.edgedns_hec.token,
            force=force)

    def clear(self):
        """
        Clear event queue

        Parameters: None
        Returns: None
        """
        self.log_queue.clear()
        self.dns_queue.clear()

    def _publish(self, queue: list[dict[str, Any]], batch_size: int, token: str, force: bool):
        logging.debug('Publishing events to Splunk')

        if len(queue) == 0:
            return False

        if len(queue) < batch_size and not force:
            return False

        assert self.config.splunk is not None
        protocol = "https://" if self.config.splunk.hec_use_ssl else "http://"
        baseurl = f'{protocol}{self.config.splunk.host}:{self.config.splunk.hec_port}'
        url = urljoin(baseurl, Splunk._HEC_ENDPOINT)
        headers = {"Authorization": "Splunk " + token}

        events_json = '\n'.join([json.dumps(event, cls=CustomJsonEncoder) for event in queue])

        self._post(url=url, headers=headers, events_json=events_json)

        queue.clear()
        logging.debug('Published events to Splunk')
        return True

    def _post(self, url, headers, events_json) -> None:
        response = requests.post(url, headers=headers, data=events_json, timeout=Splunk._TIMEOUT_SEC)
        if response.status_code != 200:
            logging.error('Splunk HEC responded with [%s]. Ignoring and moving on', response.status_code)

    def _parse_timestamp(self, log_line: str) -> float:
        """
        Parse the epoch timestamp in seconds from a log line

        Parameters:
            log_line (str): The log line to parse 

        Returns:
            float: The epoch timestamp in seconds
        """
        # Parse timestamp substring using format string
        parse_result = parse.parse(self.config.lds.timestamp_parse, log_line)
        assert isinstance(parse_result, parse.Result)
        timestamp_substr = parse_result['timestamp']

        # Convert timestamp substring to UNIX timestamp
        if self.config.lds.timestamp_strptime == '%s':
            return float(timestamp_substr)
        else:
            timestamp_datetime = datetime.strptime(timestamp_substr, self.config.lds.timestamp_strptime)
            timestamp_datetime = timestamp_datetime.replace(tzinfo=timezone.utc)
            return timestamp_datetime.timestamp()
