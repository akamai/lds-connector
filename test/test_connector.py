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
import os
import shutil
import unittest
from os import path
from test import test_data
from unittest.mock import MagicMock

from lds_connector.connector import Connector
from lds_connector.splunk import Splunk
from lds_connector.syslog import SysLog

class ConnectorTest(unittest.TestCase):
    _TEST_LOG_FILENAME = path.abspath(path.join(path.dirname(__file__), 'data/test_logs.txt'))

    def setUp(self) -> None:
        super().setUp()

        if path.isdir(test_data.TEMP_DIR):
            shutil.rmtree(test_data.TEMP_DIR)

        os.mkdir(test_data.TEMP_DIR)

    def tearDown(self) -> None:
        super().tearDown()

        if path.isdir(test_data.TEMP_DIR):
            shutil.rmtree(test_data.TEMP_DIR)

    # Timestamp parsing tests

    def test_parse_timestamp(self):
        config = test_data.create_splunk_config()
        connector = Connector(config)

        for i, log_line in enumerate(test_data.DNS_LOG_LINES):
            actual_timestamp = connector._parse_timestamp(log_line)
            self.assertEqual(actual_timestamp.timestamp(), test_data.DNS_LOG_TIMESTAMPS[i]) 

    def test_parse_timestamp_epoch(self):
        config = test_data.create_splunk_config()
        config.lds.timestamp_parse = '{} - {timestamp} {}'
        config.lds.timestamp_strptime = '%s'
        connector = Connector(config)

        for i, log_line in enumerate(test_data.DNS_LOG_LINES):
            actual_timestamp = connector._parse_timestamp(log_line)
            self.assertEqual(actual_timestamp.timestamp(), test_data.DNS_LOG_TIMESTAMPS[i])

    def test_parse_all_logs(self):
        # Test parsing on real log data. Ensure no exceptions are thrown
        config = test_data.create_splunk_config()
        connector = Connector(config)

        for log_line in ConnectorTest.read_log_lines():
            connector._parse_timestamp(log_line)

    # Splunk tests

    def test_splunk_single_log(self):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        connector.log_manager.update_last_log_files = MagicMock()
        assert isinstance(connector.event_handler, Splunk)
        connector.event_handler._post = MagicMock()

        connector.process_log_files()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, test_data.NS_FILE1_LINES)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        connector.log_manager.update_last_log_files.assert_called_once()
        connector.event_handler._post.assert_called()

    def test_splunk_multiple_logs(self):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file1 = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file1)

        log_file2 = test_data.get_ns_file2()
        test_data.download_uncompress_file(log_file2)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file1, log_file2, None])
        connector.log_manager.update_last_log_files = MagicMock()
        assert isinstance(connector.event_handler, Splunk)
        connector.event_handler._post = MagicMock()

        connector.process_log_files()

        self.assertTrue(log_file1.processed)
        self.assertEqual(log_file1.last_processed_line, test_data.NS_FILE1_LINES)
        self.assertFalse(os.path.isfile(log_file1.local_path_txt))

        self.assertTrue(log_file2.processed)
        self.assertEqual(log_file2.last_processed_line, test_data.NS_FILE2_LINES)
        self.assertFalse(os.path.isfile(log_file2.local_path_txt))

        connector.log_manager.update_last_log_files.assert_called()
        self.assertEqual(connector.log_manager.update_last_log_files.call_count, 2)
        connector.event_handler._post.assert_called()
        self.assertEqual(connector.event_handler._post.call_count, 4)

    def test_splunk_records(self):
        config = test_data.create_splunk_config()
        connector = Connector(config)

        connector.log_manager.get_next_log = MagicMock(return_value=None)
        assert isinstance(connector.event_handler, Splunk)
        connector.event_handler._post = MagicMock()
        assert connector.edgedns is not None
        connector.edgedns.get_records = MagicMock(return_value=[test_data.create_dns_record1(), test_data.create_dns_record2()])

        connector.process_dns_records()

        self.assertTrue(connector.edgedns.get_records.assert_called_once)
        self.assertEqual(connector.event_handler._post.call_count, 1)

    # SysLog tests

    def test_syslog_single_log(self):
        config = test_data.create_syslog_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        connector.log_manager.update_last_log_files = MagicMock()
        assert isinstance(connector.event_handler, SysLog)
        connector.event_handler.syslogger = MagicMock()

        connector.process_log_files()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, test_data.NS_FILE1_LINES)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        connector.log_manager.update_last_log_files.assert_called_once()
        connector.event_handler.syslogger.log_info.assert_called()

    def test_syslog_records(self):
        config = test_data.create_syslog_config()
        connector = Connector(config)

        connector.log_manager.get_next_log = MagicMock(return_value=None)
        assert isinstance(connector.event_handler, SysLog)
        connector.event_handler.syslogger = MagicMock()
        assert connector.edgedns is not None
        connector.edgedns.get_records = MagicMock(return_value=[test_data.create_dns_record1(), test_data.create_dns_record2()])

        connector.process_dns_records()

        self.assertTrue(connector.edgedns.get_records.assert_called_once)
        self.assertEqual(connector.event_handler.syslogger.log_info.call_count, 2)

    # Generic tests

    def test_dns_records_disabled(self):
        config = test_data.create_splunk_config()
        config.edgedns = None
        connector = Connector(config)

        connector.log_manager.get_next_log = MagicMock(return_value=None)
        assert isinstance(connector.event_handler, Splunk)
        connector.event_handler._post = MagicMock()

        connector.process_dns_records()

        self.assertIsNone(connector.edgedns)

    def test_logs_none_available(self):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        connector.log_manager.get_next_log = MagicMock(return_value=None)
        connector.log_manager.update_last_log_files = MagicMock()
        assert isinstance(connector.event_handler, Splunk)
        connector.event_handler._post = MagicMock()

        connector.process_log_files()

        connector.log_manager.update_last_log_files.assert_not_called()
        connector.event_handler._post.assert_not_called()

    def test_event_handler_exception(self):
        '''
        An unexpected error occurs in the second invocation of event handler.
        The log event batch size is 8.
        '''
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file1 = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file1)

        log_file2 = test_data.get_ns_file2()
        test_data.download_uncompress_file(log_file2)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file1, log_file2, None])
        connector.log_manager.update_last_log_files = MagicMock()
        assert isinstance(connector.event_handler, Splunk)
        connector.event_handler._post = MagicMock(
            side_effect=itertools.chain([True, False], itertools.repeat(True)))

        connector.process_log_files()

        self.assertTrue(log_file1.processed)
        self.assertEqual(log_file1.last_processed_line, test_data.NS_FILE1_LINES)
        self.assertFalse(os.path.isfile(log_file1.local_path_txt))

        self.assertTrue(log_file2.processed)
        self.assertEqual(log_file2.last_processed_line, test_data.NS_FILE2_LINES)
        self.assertFalse(os.path.isfile(log_file2.local_path_txt))

        connector.log_manager.update_last_log_files.assert_called()
        self.assertEqual(connector.log_manager.update_last_log_files.call_count, 2)

        connector.event_handler._post.assert_called()
        self.assertEqual(connector.event_handler._post.call_count, 5)

    def test_log_line_format_error(self):
        '''
        Line 7 of the log file is nonsense. Skip it
        '''
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file = test_data.get_ns_file4()
        test_data.download_uncompress_file(log_file)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        connector.log_manager.update_last_log_files = MagicMock()
        assert isinstance(connector.event_handler, Splunk)
        connector.event_handler._post = MagicMock()

        connector.process_log_files()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, test_data.NS_FILE4_LINES)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        connector.log_manager.update_last_log_files.assert_called_once()
        connector.event_handler._post.assert_called()

    def test_logs_resume_from_line_number(self):
        lines_already_processed = 7

        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file = test_data.get_ns_file1()
        log_file.last_processed_line = lines_already_processed
        test_data.download_uncompress_file(log_file)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        connector.log_manager.update_last_log_files = MagicMock()
        assert isinstance(connector.event_handler, Splunk)
        connector.event_handler._post = MagicMock()

        connector.process_log_files()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, test_data.NS_FILE1_LINES)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        connector.log_manager.update_last_log_files.assert_called_once()
        connector.event_handler._post.assert_called()
        self.assertEqual(connector.event_handler._post.call_count, 1)
        
    @staticmethod
    def read_log_lines() -> list[str]:
        with open(ConnectorTest._TEST_LOG_FILENAME, 'r', encoding='utf-8') as file:
            return file.readlines()

if __name__ == '__main__':
    unittest.main()
