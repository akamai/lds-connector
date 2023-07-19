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
from test import test_data, test_util
from unittest.mock import MagicMock
from typing import List

from lds_connector.connector import Connector, build_connector
from lds_connector.splunk import Splunk
from lds_connector.syslog import SysLog

class ConnectorTest(unittest.TestCase):
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
        connector = build_connector(config)

        for log_event in test_data.get_dns_log_events():
            actual_timestamp = connector._parse_timestamp(log_event.log_line)
            self.assertEqual(actual_timestamp, log_event.timestamp) 


    def test_parse_timestamp_epoch(self):
        config = test_data.create_splunk_config()
        config.lds.timestamp_parse = '{} - {timestamp} {}'
        config.lds.timestamp_strptime = '%s'
        connector = build_connector(config)

        for log_event in test_data.get_dns_log_events():
            actual_timestamp = connector._parse_timestamp(log_event.log_line)
            self.assertEqual(actual_timestamp, log_event.timestamp) 


    # Log delivery tests

    def test_log_delivery_single(self):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False

        log_file = test_data.get_ns_file1()
        test_util.download_uncompress_file(log_file)
        mock_log_manager = MagicMock()
        mock_log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        mock_event_handler = MagicMock()

        connector = Connector(config, mock_log_manager, None, mock_event_handler)

        connector.process_log_files()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, test_data.NS_FILE1_LINES)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        mock_log_manager.update_last_log_files.assert_called_once()
        self.assertEqual(mock_log_manager.get_next_log.call_count, 2)
        self.assertEqual(mock_event_handler.add_log_line.call_count, test_data.NS_FILE1_LINES)
        self.assertEqual(mock_event_handler.publish_log_lines.call_count, test_data.NS_FILE1_LINES + 1)
        for log_event in test_data.get_dns_log_events():
            mock_event_handler.add_log_line.assert_any_call(log_event)


    def test_log_delivery_batch(self):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False

        log_file = test_data.get_ns_file1()
        test_util.download_uncompress_file(log_file)
        mock_log_manager = MagicMock()
        mock_log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        mock_event_handler = MagicMock()
        mock_event_handler.publish_log_lines = MagicMock(
             side_effect=itertools.cycle(itertools.chain(itertools.repeat(False, 4), [True]))
        )

        connector = Connector(config, mock_log_manager, None, mock_event_handler)

        connector.process_log_files()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, test_data.NS_FILE1_LINES)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        mock_log_manager.update_last_log_files.assert_called_once()
        self.assertEqual(mock_log_manager.get_next_log.call_count, 2)
        self.assertEqual(mock_event_handler.add_log_line.call_count, test_data.NS_FILE1_LINES)
        self.assertEqual(mock_event_handler.publish_log_lines.call_count, test_data.NS_FILE1_LINES + 1)
        for log_event in test_data.get_dns_log_events():
            mock_event_handler.add_log_line.assert_any_call(log_event)


    def test_log_delivery_none(self):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False

        log_file = test_data.get_ns_file1()
        test_util.download_uncompress_file(log_file)
        mock_log_manager = MagicMock()
        mock_log_manager.get_next_log = MagicMock(return_value=None)
        mock_event_handler = MagicMock()

        connector = Connector(config, mock_log_manager, None, mock_event_handler)
        connector.process_log_files()

        mock_log_manager.update_last_log_files.assert_not_called()
        mock_event_handler.add_log_line.assert_not_called()


    def test_log_delivery_multiple(self):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        
        log_file1 = test_data.get_ns_file1()
        test_util.download_uncompress_file(log_file1)
        log_file2 = test_data.get_ns_file2()
        test_util.download_uncompress_file(log_file2)
        mock_log_manager = MagicMock()
        mock_log_manager.get_next_log = MagicMock(side_effect=[log_file1, log_file2, None])
        mock_event_handler = MagicMock()

        connector = Connector(config, mock_log_manager, None, mock_event_handler)

        connector.process_log_files()

        self.assertTrue(log_file1.processed)
        self.assertEqual(log_file1.last_processed_line, test_data.NS_FILE1_LINES)
        self.assertFalse(os.path.isfile(log_file1.local_path_txt))

        self.assertTrue(log_file2.processed)
        self.assertEqual(log_file2.last_processed_line, test_data.NS_FILE2_LINES)
        self.assertFalse(os.path.isfile(log_file2.local_path_txt))

        self.assertEqual(mock_log_manager.update_last_log_files.call_count, 2)
        self.assertEqual(mock_log_manager.get_next_log.call_count, 3)
        self.assertEqual(mock_event_handler.add_log_line.call_count, test_data.NS_FILE1_LINES + test_data.NS_FILE2_LINES)
        self.assertEqual(mock_event_handler.publish_log_lines.call_count, test_data.NS_FILE1_LINES + test_data.NS_FILE2_LINES + 2)

        expected_log_events = test_data.get_dns_log_events() + test_data.get_dns_log_events()
        for log_event in expected_log_events:
            mock_event_handler.add_log_line.assert_any_call(log_event)


    # Record delivery tests

    def test_record_delivery(self):
        config = test_data.create_splunk_config()
        mock_log_manager = MagicMock()
        mock_log_manager.get_next_log = MagicMock(return_value=None)
        mock_edgedns_manager = MagicMock()
        mock_edgedns_manager.get_records = MagicMock(return_value=[test_data.create_dns_record1(), test_data.create_dns_record2()])
        mock_event_handler = MagicMock()
        
        connector = Connector(config, mock_log_manager, mock_edgedns_manager, mock_event_handler)

        connector.process_dns_records()

        mock_log_manager.get_next_log.assert_not_called()
        mock_edgedns_manager.get_records.assert_called_once()
        self.assertEqual(mock_event_handler.add_dns_record.call_count, 2)
        mock_event_handler.add_dns_record.assert_any_call(test_data.create_dns_record1())
        mock_event_handler.add_dns_record.assert_any_call(test_data.create_dns_record2())
        self.assertEqual(mock_event_handler.publish_dns_records.call_count, 3)


    # Build connector tests
    
    def test_build_connector_record_delivery_disabled(self):
        config = test_data.create_splunk_config()
        config.edgedns = None
        connector = build_connector(config)
        
        assert isinstance(connector.event_handler, Splunk)
        self.assertIsNone(connector.edgedns)
        connector.event_handler = MagicMock()

        connector.process_dns_records()

        connector.event_handler.assert_not_called()

    def test_build_connector_splunk(self):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = build_connector(config)

        assert isinstance(connector.event_handler, Splunk)

    def test_build_connector_syslog(self):
        config = test_data.create_syslog_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = build_connector(config)

        assert isinstance(connector.event_handler, SysLog)

    # Other

    def test_event_handler_exception(self):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False

        log_file1 = test_data.get_ns_file1()
        test_util.download_uncompress_file(log_file1)
        log_file2 = test_data.get_ns_file2()
        test_util.download_uncompress_file(log_file2)
        mock_log_manager = MagicMock()
        mock_log_manager.get_next_log = MagicMock(side_effect=[log_file1, log_file2, None])
        mock_event_handler = MagicMock()
        mock_event_handler.publish_log_lines = MagicMock(
            side_effect=itertools.chain([True, True, ConnectionError()], itertools.repeat(True))
        )

        connector = Connector(config, mock_log_manager, None, mock_event_handler)

        connector.process_log_files()

        self.assertFalse(log_file1.processed)
        self.assertEqual(log_file1.last_processed_line, 2)
        self.assertFalse(os.path.isfile(log_file1.local_path_txt))

        self.assertTrue(log_file2.processed)
        self.assertEqual(log_file2.last_processed_line, test_data.NS_FILE2_LINES)
        self.assertFalse(os.path.isfile(log_file2.local_path_txt))

        self.assertEqual(mock_log_manager.update_last_log_files.call_count, 2)
        self.assertEqual(mock_log_manager.get_next_log.call_count, 3)
        self.assertEqual(mock_event_handler.add_log_line.call_count, 3 + test_data.NS_FILE2_LINES)
        self.assertEqual(mock_event_handler.publish_log_lines.call_count, 3 + test_data.NS_FILE2_LINES + 1)

        expected_log_events = test_data.get_dns_log_events()[0:2] + test_data.get_dns_log_events()
        for log_event in expected_log_events:
            mock_event_handler.add_log_line.assert_any_call(log_event)


    def test_log_delivery_invalid_line(self):
        '''
        Line 7 of the log file is nonsense. Skip it
        '''
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False

        log_file = test_data.get_ns_file4()
        test_util.download_uncompress_file(log_file)
        mock_log_manager = MagicMock()
        mock_log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        mock_event_handler = MagicMock()

        connector = Connector(config, mock_log_manager, None, mock_event_handler)

        connector.process_log_files()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, test_data.NS_FILE4_LINES)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        mock_log_manager.update_last_log_files.assert_called_once()
        self.assertEqual(mock_log_manager.get_next_log.call_count, 2)
        self.assertEqual(mock_event_handler.add_log_line.call_count, test_data.NS_FILE4_LINES - 1)
        self.assertEqual(mock_event_handler.publish_log_lines.call_count, test_data.NS_FILE4_LINES)
        expected_log_events = test_data.get_dns_log_events()
        expected_log_events.pop(8)
        for log_event in test_data.get_dns_log_events():
            mock_event_handler.add_log_line.assert_any_call(log_event)


    def test_log_delivery_resume_from_lines(self):
        self.log_delivery_resume_from_line(1)
        self.log_delivery_resume_from_line(7)
        self.log_delivery_resume_from_line(15)

    
    def log_delivery_resume_from_line(self, last_processed_line):
        config = test_data.create_splunk_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False

        log_file = test_data.get_ns_file1()
        log_file.last_processed_line = last_processed_line
        test_util.download_uncompress_file(log_file)
        mock_log_manager = MagicMock()
        mock_log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        mock_event_handler = MagicMock()

        connector = Connector(config, mock_log_manager, None, mock_event_handler)

        connector.process_log_files()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, test_data.NS_FILE1_LINES)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        mock_log_manager.update_last_log_files.assert_called_once()
        self.assertEqual(mock_log_manager.get_next_log.call_count, 2)
        self.assertEqual(mock_event_handler.add_log_line.call_count, test_data.NS_FILE1_LINES - last_processed_line)
        self.assertEqual(mock_event_handler.publish_log_lines.call_count, test_data.NS_FILE1_LINES - last_processed_line + 1)
        expected_log_events = test_data.get_dns_log_events()[last_processed_line:]
        for log_event in expected_log_events:
            mock_event_handler.add_log_line.assert_any_call(log_event)


if __name__ == '__main__':
    unittest.main()
