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

import os
import shutil
import unittest
from os import path
from test import test_data, test_util
from unittest.mock import MagicMock
import pickle

from lds_connector.log_manager import LogManager, LogFile, LogNameProps


class LogManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

        if path.isdir(test_data.TEMP_DIR):
            shutil.rmtree(test_data.TEMP_DIR)

        os.mkdir(test_data.TEMP_DIR)

    def tearDown(self) -> None:
        super().tearDown()

        if path.isdir(test_data.TEMP_DIR):
            shutil.rmtree(test_data.TEMP_DIR)

    @staticmethod
    def set_last_processed(log_manager: LogManager, log_file: LogFile):
        log_file.processed = True
        log_manager.last_log_files_by_zone = {'cam': log_file}

    @staticmethod
    def set_log_file_paths(log_file: LogFile):
        log_file.local_path_txt = \
            os.path.join(test_data.TEMP_DIR, log_file.filename_gz.replace('.gz', '.txt'))
        log_file.local_path_gz = os.path.join(test_data.TEMP_DIR, log_file.filename_gz)

    def test_parse_log_name(self):
        """
        If the log file name is valid
        Then the log manager parses out the metadata
        """
        file_name = "cam_123456.edns_U.202301030300-0400-3.gz"

        expected_name_props = LogNameProps(
            customer_id='cam',
            cp_code=123456,
            format='edns',
            sorted=False,
            start_time=1672714800.0,
            part=3,
            encoding='gz'
        )

        name_props = LogManager._parse_log_name(file_name)

        self.assertEqual(expected_name_props, name_props)

    def test_parse_list_response(self):
        """
        If the NetStorage list API XML response is valid
        Then the log manager parses out the log file metadata for each
        """
        log_files = LogManager._parse_list_response(test_data.NS_LIST_RESPONSE)

        self.assertEqual(log_files, [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

    def test_parse_list_response_error(self):
        """
        If the NetStorage list API XML response contains files missing some metadata (md5 hash)
        Then the log manager skips these files
        """
        list_response_xml = """<?xml version="1.0" encoding="ISO-8859-1"?>
<list>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030300-0400-0.gz" size="1234"/>
    <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030400-0500-0.gz" size="2345" md5="5d41402abc4b2a76b9719d911017c592"/>
</list>"""

        file2 = LogFile(
            ns_path_gz='/123456/cam/logs/cam_123456.edns_U.202301030400-0500-0.gz',
            filename_gz='cam_123456.edns_U.202301030400-0500-0.gz',
            size=2345,
            md5='5d41402abc4b2a76b9719d911017c592',
            name_props= LogNameProps(
                customer_id='cam',
                cp_code=123456,
                format='edns',
                sorted=False,
                start_time=1672718400.0,
                part=0,
                encoding='gz'
            ),
            local_path_gz='',
            local_path_txt='',
            processed=False,
            last_processed_line=-1
        )

        log_files = LogManager._parse_list_response(list_response_xml)

        self.assertEqual(log_files, [file2])

    def test_determine_next_log_fresh(self):
        """
        If the log manager hasn't processed any log files
        Then the log manager selects the first log file chronologically
        """
        log_manager = LogManager(test_data.create_splunk_config())

        log_manager._list = MagicMock(return_value = [test_data.get_ns_file2(), test_data.get_ns_file1(), test_data.get_ns_file3()])

        next_log = log_manager._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file1())

    def test_determine_next_log_skip_older_time(self):
        """
        If the log manager has processed the first log file
        Then the log manager selects the second log file chronologically
        """
        log_manager = LogManager(test_data.create_splunk_config())
        LogManagerTest.set_last_processed(log_manager, test_data.get_ns_file1())

        log_manager._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = log_manager._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file2())

    def test_determine_next_log_skip_older_part(self):
        """
        Considering that the second and third log file have the same time, but different parts
        If the log manager has processed the second log file
        Then the log manager selects the third log file
        """
        log_manager = LogManager(test_data.create_splunk_config())
        LogManagerTest.set_last_processed(log_manager, test_data.get_ns_file2())

        log_manager._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = log_manager._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file3())

    def test_determine_next_log_all_done(self):
        """
        If the log manager has processed all log files returned from NetStorage 
        Then the log manager doesn't select any log file
        """
        log_manager = LogManager(test_data.create_splunk_config())
        LogManagerTest.set_last_processed(log_manager, test_data.get_ns_file3())

        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = log_manager._determine_next_log()

        self.assertIsNone(next_log)

    def test_determine_next_log_none(self):
        """
        If NetStorage returns no log files
        Then the log manager doesn't select any log file
        """
        log_manager = LogManager(test_data.create_splunk_config())
        LogManagerTest.set_last_processed(log_manager, test_data.get_ns_file3())

        log_manager._list = MagicMock(return_value = [])

        next_log = log_manager._determine_next_log()

        self.assertIsNone(next_log)

    def test_determine_next_log_choose_first_part(self):
        """
        Considering that the second and third log file have the same time, but parts 0 and 1 respectively
        If the log manager has processed the first log file
        Then the log manager will select the second log file
        Event if NetStorage returns the parts out-of-order
        """
        log_manager = LogManager(test_data.create_splunk_config())
        LogManagerTest.set_last_processed(log_manager, test_data.get_ns_file1())

        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file1(), test_data.get_ns_file3(), test_data.get_ns_file2()])

        next_log = log_manager._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file2())

    def test_determine_next_log_cache_populated(self):
        log_manager = LogManager(test_data.create_splunk_config())

        log_manager._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = log_manager._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file1())
        self.assertEqual(log_manager._list.call_count, 1)

        next_log = log_manager._determine_next_log()
        self.assertEqual(next_log, test_data.get_ns_file2())
        self.assertEqual(log_manager._list.call_count, 1)

    def test_get_next_log(self):
        """
        If the log manager hasn't processed any log files
        Then the log manager fetches/unzips the first log file chronologically
        """
        config = test_data.create_splunk_config()
        config.lds.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)

        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file2(), test_data.get_ns_file1(), test_data.get_ns_file3()])
        log_manager._download = MagicMock(wraps=test_util.download_file)

        log_file = log_manager.get_next_log()

        expected_log_file = test_data.get_ns_file1()
        LogManagerTest.set_log_file_paths(expected_log_file)

        assert log_file is not None
        self.assertEqual(log_file, expected_log_file)
        self.assertTrue(os.path.isfile(expected_log_file.local_path_txt))
        self.assertFalse(os.path.isfile(expected_log_file.local_path_gz))

    def test_get_next_log_multiple_zones(self):
        """
        If there are multiple zones with the same timestamp,
        Then the log manager returns the log files chronologically

        If the log file cache is exhausted
        Then fully-processed log files aren't reprocessed.
        """
        config = test_data.create_splunk_config()
        config.lds.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)
        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file2(), test_data.get_ns_file1(), test_data.get_ns_file3(), test_data.get_ns_file5()])
        log_manager._download = MagicMock(wraps=test_util.download_file)

        log_file = log_manager.get_next_log()
        expected_log_file = test_data.get_ns_file1()
        LogManagerTest.set_log_file_paths(expected_log_file)
        self.assertEqual(log_file, expected_log_file)
        log_file.processed = True

        log_file = log_manager.get_next_log()
        expected_log_file = test_data.get_ns_file5()
        LogManagerTest.set_log_file_paths(expected_log_file)
        self.assertEqual(log_file, expected_log_file)
        log_file.processed = True

        log_file = log_manager.get_next_log()
        expected_log_file = test_data.get_ns_file2()
        LogManagerTest.set_log_file_paths(expected_log_file)
        self.assertEqual(log_file, expected_log_file)
        log_file.processed = True

        log_file = log_manager.get_next_log()
        expected_log_file = test_data.get_ns_file3()
        LogManagerTest.set_log_file_paths(expected_log_file)
        self.assertEqual(log_file, expected_log_file)
        log_file.processed = True

        log_file = log_manager.get_next_log()
        self.assertIsNone(log_file)


    def test_get_next_log_none(self):
        config = test_data.create_splunk_config()
        config.lds.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)
        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file2(), test_data.get_ns_file1(), test_data.get_ns_file3()])
        log_manager._download = MagicMock(wraps=test_util.download_file)

        self.assertIsNotNone(log_manager.get_next_log())
        self.assertIsNotNone(log_manager.get_next_log())
        self.assertIsNotNone(log_manager.get_next_log())

        log_manager._list = MagicMock(return_value = [])
        self.assertIsNone(log_manager.get_next_log())

    def test_get_next_log_sequence(self):
        """
        If the log manager processes the first two log files 
        And the second log file is marked processed and saved
        Then the resume file will be updated

        If the log manager is reinitialized
        Then the log manager will read the resume file
        And the log manager will select the third log file
        """
        config = test_data.create_splunk_config()
        config.lds.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)
        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file2(), test_data.get_ns_file1(), test_data.get_ns_file3()])
        log_manager._download = MagicMock(wraps=test_util.download_file)

        log_file1 = log_manager.get_next_log()
        log_file2 = log_manager.get_next_log()

        assert log_file1 is not None
        self.assertEqual(log_file1.filename_gz, test_data.get_ns_file1().filename_gz)
        assert log_file2 is not None
        self.assertEqual(log_file2.filename_gz, test_data.get_ns_file2().filename_gz)

        log_file2.processed = True
        log_manager.update_last_log_files()

        # Reinitialize log manager to simulate script restart
        log_manager = LogManager(config)
        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file2(), test_data.get_ns_file1(), test_data.get_ns_file3()])
        log_manager._download = MagicMock(wraps=test_util.download_file)

        log_file3 = log_manager.get_next_log()
        assert log_file3 is not None
        self.assertEqual(log_file3.filename_gz, test_data.get_ns_file3().filename_gz)

    def test_read_resume_data(self):
        """
        If there is a resume pickle file
        Then the log manager reads it on init
        """
        resume_data = test_data.get_ns_file1()
        resume_data.processed = True
        resume_data.last_processed_line = 4

        with open(test_data.RESUME_DATA_PATH, 'wb') as file:
            pickle.dump({'cam': resume_data}, file)

        config = test_data.create_splunk_config()
        config.lds.log_download_dir = test_data.TEMP_DIR

        log_manager = LogManager(config)

        self.assertEqual(log_manager.last_log_files_by_zone, {'cam': resume_data})

    def test_resume_unfinished_log(self):
        """
        If the log manager has resume data indicating the first log file was partially processed
        Then the log manager continues processing it at the next line
        """
        resume_file = test_data.get_ns_file1()
        resume_file.processed = False
        resume_file.last_processed_line = 2
        test_util.download_file(resume_file)
        LogManager._uncompress(resume_file)
        with open(test_data.RESUME_DATA_PATH, 'wb') as file:
            pickle.dump({'cam': resume_file}, file)

        config = test_data.create_splunk_config()
        config.lds.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)
        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])
        log_manager._download = MagicMock(wraps=test_util.download_file)

        log_file = log_manager.get_next_log()

        self.assertEqual(log_file, resume_file)
        self.assertEqual(log_manager.current_log_file, resume_file)

    def test_resume_finished_log(self):
        """
        If the log manager has resume data indicating the first log file was fully processed
        Then the log manager fetches/unzips the next log file chronologically
        """
        resume_file = test_data.get_ns_file1()
        resume_file.processed = True
        resume_file.last_processed_line = 4
        with open(test_data.RESUME_DATA_PATH, 'wb') as file:
            pickle.dump({'cam': resume_file}, file)

        config = test_data.create_splunk_config()
        config.lds.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)

        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])
        log_manager._download = MagicMock(wraps=test_util.download_file)

        log_file = log_manager.get_next_log()

        expected_log_file = test_data.get_ns_file2()
        expected_log_file.local_path_txt = \
            os.path.join(test_data.TEMP_DIR, expected_log_file.filename_gz.replace('.gz', '.txt'))
        expected_log_file.local_path_gz = os.path.join(test_data.TEMP_DIR, expected_log_file.filename_gz)

        assert log_file is not None
        self.assertEqual(log_file, expected_log_file)
        self.assertTrue(os.path.isfile(log_file.local_path_txt))
        self.assertFalse(os.path.isfile(log_file.local_path_gz))

    def test_parse_list_response_ignore_outside_files(self):
        """
        If the NetStorage list API contains files outside of the requested directory
        Then the log manager will ignore those files.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response_text = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <list>
            <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030300-0400-0.gz" size="1234" md5="098f6bcd4621d373cade4e832627b4f6"/>
            <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030400-0500-0.gz" size="2345" md5="5d41402abc4b2a76b9719d911017c592"/>
            <file type="file" name="123456/other/logs/cam_123456.edns_U.202301030400-0500-0.gz" size="3456" md5="d850f04cdb48312a9be171e214c0b4ee"/>
            <file type="file" name="123456/logs/cam_123456.edns_U.202301030400-0500-0.gz" size="3456" md5="d850f04cdb48312a9be171e214c0b4ee"/>
            <file type="file" name="123456/cam/logs/cam_123456.edns_U.202301030400-0500-1.gz" size="3456" md5="d850f04cdb48312a9be171e214c0b4ee"/>
        </list>"""
        mock_response.text = mock_response_text

        config = test_data.create_splunk_config()
        log_manager = LogManager(config)

        log_manager.netstorage = MagicMock()
        log_manager.netstorage.list = MagicMock(return_value=(True, mock_response))

        actual_log_files = log_manager._list()
        self.assertEqual(len(actual_log_files), 3)
        self.assertEqual(actual_log_files, [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])


if __name__ == '__main__':
    unittest.main()
