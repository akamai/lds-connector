from datetime import datetime, timezone
import logging
from urllib.parse import urljoin
import parse
import requests

from .config import Config


class Splunk:
    _PARSE_FORMAT_STRING = '{} - {} {timestamp},{}'
    _STRP_FORMAT_STRING = '%d/%m/%Y %H:%M:%S'
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

        hec_json = Splunk._create_hec_json(timestamp_sec, log_line)

        self._publish_hec_event(hec_json)

    def _publish_hec_event(self, hec_json: dict) -> None:
        baseurl = "http://" + self.config.splunk_config.hec_host + ":" + str(self.config.splunk_config.hec_port)
        url = urljoin(baseurl, Splunk._HEC_ENDPOINT)
        headers = {"Authorization": "Splunk " + self.config.splunk_config.hec_token}

        response = requests.post(url, headers=headers, json=hec_json, timeout=Splunk._TIMEOUT_SEC)
        if response.status_code != 200:
            logging.error('Failed sending event to Splunk HEC endpoint [%s]', hec_json)

    @staticmethod
    def _parse_timestamp(log_line: str) -> float:
        # Assume the log line is in DNS format

        # Parse timestamp substring using format string
        parse_result = parse.parse(Splunk._PARSE_FORMAT_STRING, log_line)
        assert isinstance(parse_result, parse.Result)
        timestamp_substr = parse_result['timestamp']

        # Convert timestamp substring to UNIX timestamp
        timestamp_datetime = datetime.strptime(timestamp_substr, Splunk._STRP_FORMAT_STRING)
        timestamp_datetime = timestamp_datetime.replace(tzinfo=timezone.utc)
        return timestamp_datetime.timestamp()

    @staticmethod
    def _create_hec_json(timestamp_sec: float, log_line: str):
        return {
            'time': timestamp_sec,
            'host': '',
            'source': 'splunk-lds-connector',
            'sourcetype': 'lds_log_dns',
            'index': 'main',
            'event': log_line
        }
