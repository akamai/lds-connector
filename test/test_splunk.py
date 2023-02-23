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

import unittest
from unittest.mock import MagicMock
from os import path
from test import test_data
import socket
import json
from typing import Any

from lds_connector.splunk import Splunk
from lds_connector.json import CustomJsonEncoder
from lds_connector.config import Config

class SplunkTest(unittest.TestCase):
    _TEST_LOG_FILENAME = path.abspath(path.join(path.dirname(__file__), 'data/test_logs.txt'))

    _TIMESTAMP_TO_LOG_LINE = [
        (1672715199.0, '416458 - 1672715199 03/01/2023 03:06:39,52.37.159.152,52149,edgedns.zone,IN,CAA,E,4096,D,,300:0 issue "ca.sectigo.com" 300:0 issue "ca.digicert.com" SIGNx1 '),
        (1672715199.0, '416458 - 1672715199 03/01/2023 03:06:39,52.37.159.152,64062,2ww-nigiro.edgedns.zone,IN,A,E,4096,D,,3:NXDOMAIN '),
        (1672715199.0, '416458 - 1672715199 03/01/2023 03:06:39,52.37.159.152,43215,edgedns.zone,IN,NS,E,4096,D,,86400:a13-67.akam.net 86400:a11-66.akam.net 86400:a22-64.akam.net 86400:a24-65.akam.net 86400:a28-66.akam.net 86400:a1-247.akam.net SIGNx1 '),
        (1672713883.0, '416458 - 1672713883 03/01/2023 02:44:43,2600:1406:1a00:2::687d:da8c,44473,edgedns.zone,IN,SOA,,,,,86400:a1-247.akam.net hostmaster.edgedns.zone 2019102599 3600 600 604800 300 ')
    ]

    def test_parse_timestamp(self):
        config = test_data.create_config()
        splunk = Splunk(config)

        for (expected_timestamp, log_line) in SplunkTest._TIMESTAMP_TO_LOG_LINE:
            actual_timestamp = splunk._parse_timestamp(log_line)
            self.assertEqual(actual_timestamp, expected_timestamp)

    def test_parse_timestamp_epoch(self):
        config = test_data.create_config()
        config.timestamp_parse = '{} - {timestamp} {}'
        config.timestamp_strptime = '%s'
        splunk = Splunk(config)

        for (expected_timestamp, log_line) in SplunkTest._TIMESTAMP_TO_LOG_LINE:
            actual_timestamp = splunk._parse_timestamp(log_line)
            self.assertEqual(actual_timestamp, expected_timestamp)

    def test_parse_all_logs(self):
        # Test parsing on real log data. Ensure no exceptions are thrown
        config = test_data.create_config()
        splunk = Splunk(config)

        for log_line in SplunkTest.read_log_lines():
            splunk._parse_timestamp(log_line)

    def test_publish_logs(self):
        config = test_data.create_config()
        config.splunk.lds_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock()

        timestamp, log_line = SplunkTest._TIMESTAMP_TO_LOG_LINE[0]

        splunk.add_log_line(log_line)
        self.assertTrue(splunk.publish_log_lines())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_lds_hec_token"}
        expected_event = json.dumps({
            'time': timestamp,
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_line,
            'sourcetype': config.splunk.lds_hec.source_type,
            'index': config.splunk.lds_hec.index
        })
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json = expected_event
        )

    def test_publish_records(self):
        config = test_data.create_config()
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock()

        dns_record = test_data.create_dns_record1()

        splunk.add_dns_record(dns_record)
        self.assertTrue(splunk.publish_dns_records())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_edgedns_hec_token"}
        expected_event = SplunkTest.create_expected_record_event(config, dns_record)

        expected_events_json = json.dumps(expected_event, cls=CustomJsonEncoder)
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json=expected_events_json
        )

    def test_publish_logs_no_optionals(self):
        config = test_data.create_config()
        config.splunk.lds_hec.source_type = None
        config.splunk.lds_hec.index = None
        config.splunk.lds_hec.event_batch_size = 1
        
        splunk = Splunk(config)
        splunk._post = MagicMock()

        timestamp, log_line = SplunkTest._TIMESTAMP_TO_LOG_LINE[0]

        splunk.add_log_line(log_line)
        self.assertTrue(splunk.publish_log_lines())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_lds_hec_token"}
        expected_event = json.dumps({
            'time': timestamp,
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_line,
        })
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json = expected_event
        )

    def test_publish_records_no_optionals(self):
        config = test_data.create_config()
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.source_type = None
        config.splunk.edgedns_hec.index = None
        config.splunk.edgedns_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock()

        dns_record = test_data.create_dns_record1()

        splunk.add_dns_record(dns_record)
        self.assertTrue(splunk.publish_dns_records())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_edgedns_hec_token"}
        expected_event = SplunkTest.create_expected_record_event(config, dns_record, optionals=False)

        expected_events_json = json.dumps(expected_event, cls=CustomJsonEncoder)
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json=expected_events_json
        )

    def test_publish_logs_no_events(self):
        config = test_data.create_config()
        config.splunk.lds_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock()

        self.assertFalse(splunk.publish_log_lines())

        splunk._post.assert_not_called()

    def test_publish_records_no_events(self):
        config = test_data.create_config()
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock()

        self.assertFalse(splunk.publish_dns_records())

        splunk._post.assert_not_called()

    def test_publish_logs_not_full_batch(self):
        config = test_data.create_config()
        config.splunk.lds_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock()

        log_line = SplunkTest._TIMESTAMP_TO_LOG_LINE[0][1]

        splunk.add_log_line(log_line)
        self.assertFalse(splunk.publish_log_lines())

        splunk.add_log_line(log_line)
        self.assertFalse(splunk.publish_log_lines())

        splunk._post.assert_not_called()

    def test_publish_records_not_full_batch(self):
        config = test_data.create_config()
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock()

        dns_record = test_data.create_dns_record1()

        splunk.add_dns_record(dns_record)
        self.assertFalse(splunk.publish_dns_records())

        splunk.add_dns_record(dns_record)
        self.assertFalse(splunk.publish_dns_records())

        splunk._post.assert_not_called()

    def test_publish_logs_full_batch(self):
        config = test_data.create_config()
        config.splunk.lds_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock()

        timestamp, log_line = SplunkTest._TIMESTAMP_TO_LOG_LINE[0]

        splunk.add_log_line(log_line)
        self.assertFalse(splunk.publish_log_lines())

        splunk.add_log_line(log_line)
        self.assertFalse(splunk.publish_log_lines())

        splunk.add_log_line(log_line)
        self.assertTrue(splunk.publish_log_lines())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_lds_hec_token"}
        expected_event = {
            'time': timestamp,
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_line,
            'sourcetype': config.splunk.lds_hec.source_type,
            'index': config.splunk.lds_hec.index
        }
        expected_events = '\n'.join([json.dumps(event) for event in [expected_event, expected_event, expected_event]])
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json=expected_events
        )

    def test_publish_records_full_batch(self):
        config = test_data.create_config()
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock()

        dns_record1 = test_data.create_dns_record1()
        dns_record2 = test_data.create_dns_record2()
        dns_record3 = test_data.create_dns_record3()

        splunk.add_dns_record(dns_record1)
        self.assertFalse(splunk.publish_dns_records())

        splunk.add_dns_record(dns_record2)
        self.assertFalse(splunk.publish_dns_records())

        splunk.add_dns_record(dns_record3)
        self.assertTrue(splunk.publish_dns_records())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_edgedns_hec_token"}
        expected_events_json = [
            SplunkTest.create_expected_record_event(config, dns_record1),
            SplunkTest.create_expected_record_event(config, dns_record2),
            SplunkTest.create_expected_record_event(config, dns_record3)
        ]

        expected_events = '\n'.join([json.dumps(event, cls=CustomJsonEncoder) for event in expected_events_json])
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json=expected_events
        )

    def test_publish_logs_force_not_full_batch(self):
        config = test_data.create_config()
        config.splunk.lds_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock()

        timestamp, log_line = SplunkTest._TIMESTAMP_TO_LOG_LINE[0]

        splunk.add_log_line(log_line)
        self.assertFalse(splunk.publish_log_lines())

        splunk.add_log_line(log_line)
        self.assertTrue(splunk.publish_log_lines(force=True))

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_lds_hec_token"}
        expected_event = {
            'time': timestamp,
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_line,
            'sourcetype': config.splunk.lds_hec.source_type,
            'index': config.splunk.lds_hec.index
        }
        expected_events = '\n'.join([json.dumps(event) for event in [expected_event, expected_event]])
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json = expected_events
        )

    def test_publish_records_force_not_full_batch(self):
        config = test_data.create_config()
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock()

        dns_record1 = test_data.create_dns_record1()
        dns_record2 = test_data.create_dns_record2()

        splunk.add_dns_record(dns_record1)
        self.assertFalse(splunk.publish_dns_records())

        splunk.add_dns_record(dns_record2)
        self.assertTrue(splunk.publish_dns_records(force=True))

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_edgedns_hec_token"}
        expected_events_json = [
            SplunkTest.create_expected_record_event(config, dns_record1),
            SplunkTest.create_expected_record_event(config, dns_record2)
        ]

        expected_events = '\n'.join([json.dumps(event, cls=CustomJsonEncoder) for event in expected_events_json])
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json=expected_events
        )

    @staticmethod
    def read_log_lines() -> list[str]:
        with open(SplunkTest._TEST_LOG_FILENAME, 'r', encoding='utf-8') as file:
            return file.readlines()

    @staticmethod
    def create_expected_record_event(config: Config, event, optionals=True) -> dict[str, Any]:
        assert config.splunk.edgedns_hec is not None
        event = {
            'time': 0,
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': event,
        }

        if optionals:
            event['sourcetype'] = config.splunk.edgedns_hec.source_type
            event['index'] = config.splunk.edgedns_hec.index

        return event


if __name__ == '__main__':
    unittest.main()
