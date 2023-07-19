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

import itertools
import unittest
from unittest.mock import MagicMock, patch
from os import path
import socket
import json
from typing import Any, Dict

from test import test_data

from lds_connector.splunk import Splunk
from lds_connector.json import CustomJsonEncoder
from lds_connector.config import Config


class SplunkTest(unittest.TestCase):
    _TEST_LOG_FILENAME = path.abspath(path.join(path.dirname(__file__), 'data/test_logs.txt'))

    def test_publish_logs(self):
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        config.splunk.lds_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

        log_event = test_data.get_dns_log_events()[0]

        splunk.add_log_line(log_event)
        self.assertTrue(splunk.publish_log_lines())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_lds_hec_token"}
        expected_event = json.dumps({
            'time': log_event.timestamp.timestamp(),
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_event.log_line,
            'sourcetype': config.splunk.lds_hec.source_type,
            'index': config.splunk.lds_hec.index
        })
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json = expected_event
        )

    @patch('lds_connector.splunk.requests')
    def test_publish_logs_retry(self, mock_requests):
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        config.splunk.lds_hec.event_batch_size = 1

        splunk = Splunk(config)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_bad_response = MagicMock()
        mock_bad_response.status_code = 404
        mock_requests.post.side_effect = itertools.chain([ConnectionError(), mock_bad_response], itertools.repeat(mock_response))

        log_event = test_data.get_dns_log_events()[0]

        splunk.add_log_line(log_event)
        self.assertTrue(splunk.publish_log_lines())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_lds_hec_token"}
        expected_event = json.dumps({
            'time': log_event.timestamp.timestamp(),
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_event.log_line,
            'sourcetype': config.splunk.lds_hec.source_type,
            'index': config.splunk.lds_hec.index
        })
        mock_requests.post.assert_called_with(
            expected_url,
            headers=expected_headers,
            data=expected_event,
            timeout=Splunk._TIMEOUT_SEC
        )

    def test_publish_records(self):
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

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
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        config.splunk.lds_hec.source_type = None
        config.splunk.lds_hec.index = None
        config.splunk.lds_hec.event_batch_size = 1
        
        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

        log_event = test_data.get_dns_log_events()[0]

        splunk.add_log_line(log_event)
        self.assertTrue(splunk.publish_log_lines())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_lds_hec_token"}
        expected_event = json.dumps({
            'time': log_event.timestamp.timestamp(),
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_event.log_line
        })
        splunk._post.assert_called_once_with(
            url=expected_url,
            headers=expected_headers,
            events_json = expected_event
        )

    def test_publish_records_no_optionals(self):
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.source_type = None
        config.splunk.edgedns_hec.index = None
        config.splunk.edgedns_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

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
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        config.splunk.lds_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

        self.assertFalse(splunk.publish_log_lines())

        splunk._post.assert_not_called()

    def test_publish_records_no_events(self):
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 1

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

        self.assertFalse(splunk.publish_dns_records())

        splunk._post.assert_not_called()

    def test_publish_logs_not_full_batch(self):
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        config.splunk.lds_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

        log_event1 = test_data.get_dns_log_events()[0]
        splunk.add_log_line(log_event1)
        self.assertFalse(splunk.publish_log_lines())

        log_event2 = test_data.get_dns_log_events()[1]
        splunk.add_log_line(log_event2)
        self.assertFalse(splunk.publish_log_lines())

        splunk._post.assert_not_called()

    def test_publish_records_not_full_batch(self):
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

        dns_record = test_data.create_dns_record1()

        splunk.add_dns_record(dns_record)
        self.assertFalse(splunk.publish_dns_records())

        splunk.add_dns_record(dns_record)
        self.assertFalse(splunk.publish_dns_records())

        splunk._post.assert_not_called()

    def test_publish_logs_full_batch(self):
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        config.splunk.lds_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

        log_event = test_data.get_dns_log_events()[0]
        splunk.add_log_line(log_event)
        self.assertFalse(splunk.publish_log_lines())

        splunk.add_log_line(log_event)
        self.assertFalse(splunk.publish_log_lines())

        splunk.add_log_line(log_event)
        self.assertTrue(splunk.publish_log_lines())

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_lds_hec_token"}
        expected_event = {
            'time': log_event.timestamp.timestamp(),
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_event.log_line,
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
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

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
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        config.splunk.lds_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

        log_event = test_data.get_dns_log_events()[0]
        splunk.add_log_line(log_event)
        self.assertFalse(splunk.publish_log_lines())

        splunk.add_log_line(log_event)
        self.assertTrue(splunk.publish_log_lines(force=True))

        expected_url = 'http://127.0.0.1:8088/services/collector/event'
        expected_headers = {'Authorization': "Splunk test_lds_hec_token"}
        expected_event = {
            'time': log_event.timestamp.timestamp(),
            'host': socket.gethostname(),
            'source': 'lds-connector',
            'event': log_event.log_line,
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
        config = test_data.create_splunk_config()
        assert config.splunk is not None
        assert config.splunk.edgedns_hec is not None
        config.splunk.edgedns_hec.event_batch_size = 3

        splunk = Splunk(config)
        splunk._post = MagicMock(return_value=True)

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
    def create_expected_record_event(config: Config, event, optionals=True) -> Dict[str, Any]:
        assert config.splunk is not None
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
