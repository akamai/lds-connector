import logging
import socket
from datetime import datetime, timezone
from urllib.parse import urljoin

import parse
import requests

from .config import Config


class Splunk:
    _HEC_ENDPOINT = '/services/collector/event'
    _TIMEOUT_SEC = 5

    def __init__(self, config: Config):
        self.config = config

    def handle_logline(self, log_line: str) -> None:
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
        if self.config.splunk_config.hec_source_type:
            hec_json['sourcetype'] = self.config.splunk_config.hec_source_type
        if self.config.splunk_config.hec_index:
            hec_json['index'] = self.config.splunk_config.hec_index

        self._publish_hec_event(hec_json)

    def _publish_hec_event(self, hec_json: dict) -> None:
        protocol = "https://" if self.config.splunk_config.hec_use_ssl else "http://"
        baseurl = f'{protocol}{self.config.splunk_config.host}:{self.config.splunk_config.hec_port}'
        url = urljoin(baseurl, Splunk._HEC_ENDPOINT)
        headers = {"Authorization": "Splunk " + self.config.splunk_config.hec_token}

        response = requests.post(url, headers=headers, json=hec_json, timeout=Splunk._TIMEOUT_SEC)
        if response.status_code != 200:
            logging.error('Failed sending event to Splunk HEC endpoint [%s]', hec_json)

    def _parse_timestamp(self, log_line: str) -> float:
        # Parse timestamp substring using format string
        parse_result = parse.parse(self.config.timestamp_parse, log_line)
        assert isinstance(parse_result, parse.Result)
        timestamp_substr = parse_result['timestamp']

        # Convert timestamp substring to UNIX timestamp
        timestamp_datetime = datetime.strptime(timestamp_substr, self.config.timestamp_strptime)
        timestamp_datetime = timestamp_datetime.replace(tzinfo=timezone.utc)
        return timestamp_datetime.timestamp()
