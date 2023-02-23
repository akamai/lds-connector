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

    def test_run_single_log(self):
        config = test_data.create_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk._post = MagicMock()

        connector.run()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, 15)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        connector.log_manager.save_resume_data.assert_called_once()
        connector.splunk._post.assert_called()
        # TODO: Assert call count

    def test_run_multiple_logs(self):
        config = test_data.create_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file1 = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file1)

        log_file2 = test_data.get_ns_file2()
        test_data.download_uncompress_file(log_file2)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file1, log_file2, None])
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk._post = MagicMock()

        connector.run()

        self.assertTrue(log_file1.processed)
        self.assertEqual(log_file1.last_processed_line, 15)
        self.assertFalse(os.path.isfile(log_file1.local_path_txt))

        self.assertTrue(log_file2.processed)
        self.assertEqual(log_file2.last_processed_line, 15)
        self.assertFalse(os.path.isfile(log_file2.local_path_txt))

        connector.log_manager.save_resume_data.assert_called()
        self.assertEqual(connector.log_manager.save_resume_data.call_count, 2)
        connector.splunk._post.assert_called()
        self.assertEqual(connector.splunk._post.call_count, 4)

    def test_run_no_logs(self):
        config = test_data.create_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        connector.log_manager.get_next_log = MagicMock(return_value=None)
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk._post = MagicMock()

        connector.run()

        connector.log_manager.save_resume_data.assert_not_called()
        connector.splunk._post.assert_not_called()

    def test_run_unexpected_error(self):
        config = test_data.create_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file1 = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file1)

        log_file2 = test_data.get_ns_file2()
        test_data.download_uncompress_file(log_file2)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file1, log_file2, None])
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk._post = MagicMock(
            side_effect=itertools.chain([None, ConnectionError()], itertools.repeat(None)))

        connector.run()

        self.assertFalse(log_file1.processed)
        self.assertEqual(log_file1.last_processed_line, 8)
        self.assertTrue(os.path.isfile(log_file1.local_path_txt))

        self.assertTrue(log_file2.processed)
        self.assertEqual(log_file2.last_processed_line, 15)
        self.assertFalse(os.path.isfile(log_file2.local_path_txt))

        connector.log_manager.save_resume_data.assert_called()
        self.assertEqual(connector.log_manager.save_resume_data.call_count, 2)

        connector.splunk._post.assert_called()
        self.assertEqual(connector.splunk._post.call_count, 4)

    def test_resume_from_line_number(self):
        lines_already_processed = 7
        total_lines = 15

        config = test_data.create_config()
        assert config.edgedns is not None
        config.edgedns.send_records = False
        connector = Connector(config)

        log_file = test_data.get_ns_file1()
        log_file.last_processed_line = lines_already_processed
        test_data.download_uncompress_file(log_file)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk._post = MagicMock()

        connector.run()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, total_lines)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        connector.log_manager.save_resume_data.assert_called_once()
        connector.splunk._post.assert_called()
        self.assertEqual(connector.splunk._post.call_count, 1)

    def test_process_dns_records(self):
        config = test_data.create_config()
        connector = Connector(config)

        connector.log_manager.get_next_log = MagicMock(return_value=None)
        connector.splunk._post = MagicMock()
        assert connector.edgedns is not None
        connector.edgedns.get_records = MagicMock(return_value=[test_data.create_dns_record1, test_data.create_dns_record2])

        connector.run()

        self.assertTrue(connector.edgedns.get_records.assert_called_once)


if __name__ == '__main__':
    unittest.main()
