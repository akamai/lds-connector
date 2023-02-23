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
import socket
from datetime import datetime, timezone
from urllib.parse import urljoin
import json

import parse
import requests

from .config import Config


class Splunk:
    """
    Splunk log line handler. Responsible for converting log lines to Splunk events
    """
    _HEC_ENDPOINT = '/services/collector/event'
    _TIMEOUT_SEC = 5

    def __init__(self, config: Config):
        self.config = config
        self.queue = []

    def handle_logline(self, log_line: str) -> None:
        pass


    def add(self, log_line: str) -> None:
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
            'source': 'splunk-lds-connector',
            'event': log_line
        }
        if self.config.splunk.lds_hec.source_type:
            hec_json['sourcetype'] = self.config.splunk.lds_hec.source_type
        if self.config.splunk.lds_hec.index:
            hec_json['index'] = self.config.splunk.lds_hec.index

        self.queue.append(hec_json)

    def publish(self, force=False) -> bool:
        """
        Publish queued HEC events to Splunk HEC

        Parameters:
            force (bool): If true, send queued events. Otherwise, send queued events iff queue size >= batch size.

        Returns:
            bool: If events were published, true. Otherwise, false.
        """
        logging.debug('Publishing events to Splunk')

        if len(self.queue) == 0:
            return False

        if len(self.queue) < self.config.splunk.lds_hec.event_batch_size and not force:
            return False

        self._publish(self.queue)

        self.queue = []
        logging.debug('Published events to Splunk')
        return True

    def clear(self):
        """
        Clear event queue

        Parameters: None
        Returns: None
        """
        self.queue.clear()

    def _publish(self, events) -> None:
        """
        Publish events to Splunk HEC. 

        Parameters:
            events (list[str]): The events to send

        Returns: None
        """
        protocol = "https://" if self.config.splunk.hec_use_ssl else "http://"
        baseurl = f'{protocol}{self.config.splunk.host}:{self.config.splunk.hec_port}'
        url = urljoin(baseurl, Splunk._HEC_ENDPOINT)
        headers = {"Authorization": "Splunk " + self.config.splunk.lds_hec.token}

        events_json = '\n'.join([json.dumps(event) for event in events])

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
        parse_result = parse.parse(self.config.timestamp_parse, log_line)
        assert isinstance(parse_result, parse.Result)
        timestamp_substr = parse_result['timestamp']

        # Convert timestamp substring to UNIX timestamp
        if self.config.timestamp_strptime == '%s':
            return float(timestamp_substr)
        else:
            timestamp_datetime = datetime.strptime(timestamp_substr, self.config.timestamp_strptime)
            timestamp_datetime = timestamp_datetime.replace(tzinfo=timezone.utc)
            return timestamp_datetime.timestamp()
