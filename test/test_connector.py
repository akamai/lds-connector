import itertools
import os
import shutil
import unittest
from os import path
from test import test_data
from unittest.mock import MagicMock

from src.connector import Connector
from src.log_manager import LogManager


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
        connector = Connector(config)

        log_file = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk.handle_logline = MagicMock()

        connector.run()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, 15)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        connector.log_manager.save_resume_data.assert_called_once()
        connector.splunk.handle_logline.assert_called()


    def test_run_multiple_logs(self):
        config = test_data.create_config()
        connector = Connector(config)

        log_file1 = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file1)

        log_file2 = test_data.get_ns_file2()
        test_data.download_uncompress_file(log_file2)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file1, log_file2, None])
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk.handle_logline = MagicMock()

        connector.run()

        self.assertTrue(log_file1.processed)
        self.assertEqual(log_file1.last_processed_line, 15)
        self.assertFalse(os.path.isfile(log_file1.local_path_txt))

        self.assertTrue(log_file2.processed)
        self.assertEqual(log_file2.last_processed_line, 15)
        self.assertFalse(os.path.isfile(log_file2.local_path_txt))

        connector.log_manager.save_resume_data.assert_called()
        self.assertEqual(connector.log_manager.save_resume_data.call_count, 2)
        connector.splunk.handle_logline.assert_called()

    def test_run_no_logs(self):
        config = test_data.create_config()
        connector = Connector(config)

        connector.log_manager.get_next_log = MagicMock(return_value=None)
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk.handle_logline = MagicMock()

        connector.run()

        connector.log_manager.save_resume_data.assert_not_called()
        connector.splunk.handle_logline.assert_not_called()

    def test_run_unexpected_error(self):
        config = test_data.create_config()
        connector = Connector(config)

        log_file1 = test_data.get_ns_file1()
        test_data.download_uncompress_file(log_file1)

        log_file2 = test_data.get_ns_file2()
        test_data.download_uncompress_file(log_file2)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file1, log_file2, None])
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk.handle_logline = MagicMock(
            side_effect=itertools.chain([None, ConnectionError()], itertools.repeat(None)))

        connector.run()

        self.assertFalse(log_file1.processed)
        self.assertEqual(log_file1.last_processed_line, 1)
        self.assertTrue(os.path.isfile(log_file1.local_path_txt))

        self.assertTrue(log_file2.processed)
        self.assertEqual(log_file2.last_processed_line, 15)
        self.assertFalse(os.path.isfile(log_file2.local_path_txt))

        connector.log_manager.save_resume_data.assert_called()
        self.assertEqual(connector.log_manager.save_resume_data.call_count, 2)

        connector.splunk.handle_logline.assert_called()

    def test_resume_from_line_number(self):
        lines_already_processed = 7
        total_lines = 15

        config = test_data.create_config()
        connector = Connector(config)

        log_file = test_data.get_ns_file1()
        log_file.last_processed_line = lines_already_processed
        test_data.download_uncompress_file(log_file)

        connector.log_manager.get_next_log = MagicMock(side_effect=[log_file, None])
        connector.log_manager.save_resume_data = MagicMock()
        connector.splunk.handle_logline = MagicMock()

        connector.run()

        self.assertTrue(log_file.processed)
        self.assertEqual(log_file.last_processed_line, total_lines)
        self.assertFalse(os.path.isfile(log_file.local_path_txt))

        connector.log_manager.save_resume_data.assert_called_once()
        connector.splunk.handle_logline.assert_called() 
        self.assertEqual(connector.splunk.handle_logline.call_count, total_lines - lines_already_processed)

if __name__ == '__main__':
    unittest.main()
