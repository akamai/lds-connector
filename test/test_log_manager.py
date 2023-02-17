import os
import shutil
import unittest
from os import path
from test import test_data
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

    def test_parse_log_name(self):
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
        log_files = LogManager._parse_list_response(test_data.NS_LIST_RESPONSE)

        self.assertEqual(log_files, [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

    def test_parse_list_response_error(self):
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
        log_manager = LogManager(test_data.create_config())

        log_manager._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = log_manager._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file1())

    def test_determine_next_log_skip_older_time(self):
        log_manager = LogManager(test_data.create_config())
        log_manager.last_log_file = test_data.get_ns_file1()

        log_manager._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = log_manager._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file2())

    def test_determine_next_log_skip_older_part(self):
        log_manager = LogManager(test_data.create_config())
        log_manager.last_log_file = test_data.get_ns_file2()

        log_manager._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = log_manager._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file3())

    def test_determine_next_log_all_done(self):
        log_manager = LogManager(test_data.create_config())
        log_manager.last_log_file = test_data.get_ns_file3()

        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = log_manager._determine_next_log()

        self.assertIsNone(next_log)

    def test_determine_next_log_none(self):
        log_manager = LogManager(test_data.create_config())
        log_manager.last_log_file = test_data.get_ns_file3()

        log_manager._list = MagicMock(return_value = [])

        next_log = log_manager._determine_next_log()

        self.assertIsNone(next_log)

    def test_determine_next_log_choose_first_part(self):
        log_manager = LogManager(test_data.create_config())
        log_manager.last_log_file = test_data.get_ns_file1()

        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file1(), test_data.get_ns_file3(), test_data.get_ns_file2()])

        next_log = log_manager._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file2())

    def test_get_next_log(self):
        config = test_data.create_config()
        config.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)

        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file2(), test_data.get_ns_file1(), test_data.get_ns_file3()])
        log_manager._download = MagicMock(wraps=test_data.download_file)

        log_file = log_manager.get_next_log()

        expected_log_file = test_data.get_ns_file1()
        expected_log_file.local_path_txt = \
            os.path.join(test_data.TEMP_DIR, expected_log_file.filename_gz.replace('.gz', '.txt'))
        expected_log_file.local_path_gz = os.path.join(test_data.TEMP_DIR, expected_log_file.filename_gz)

        assert log_file is not None
        self.assertEqual(log_file, expected_log_file)
        self.assertTrue(os.path.isfile(expected_log_file.local_path_txt))
        self.assertFalse(os.path.isfile(expected_log_file.local_path_gz))

    def test_read_resume_data(self):
        resume_data = test_data.get_ns_file1()
        resume_data.processed = True
        resume_data.last_processed_line = 4

        with open(test_data.RESUME_PATH, 'wb') as file:
            pickle.dump(resume_data, file)

        config = test_data.create_config()
        config.log_download_dir = test_data.TEMP_DIR

        log_manager = LogManager(config)

        self.assertEqual(log_manager.resume_log_file, resume_data)

    def test_resume_unfinished_log(self):
        resume_data = test_data.get_ns_file1()
        resume_data.processed = False
        resume_data.last_processed_line = 2
        test_data.download_file(resume_data)
        LogManager._uncompress(resume_data)
        with open(test_data.RESUME_PATH, 'wb') as file:
            pickle.dump(resume_data, file)

        config = test_data.create_config()
        config.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)

        log_file = log_manager.get_next_log()

        self.assertEqual(log_file, resume_data)
        self.assertIsNone(log_manager.resume_log_file)
        self.assertEqual(log_manager.current_log_file, resume_data)
        self.assertIsNone(log_manager.last_log_file)

    def test_resume_finished_log(self):
        resume_data = test_data.get_ns_file1()
        resume_data.processed = True
        resume_data.last_processed_line = 4
        with open(test_data.RESUME_PATH, 'wb') as file:
            pickle.dump(resume_data, file)

        config = test_data.create_config()
        config.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)

        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])
        log_manager._download = MagicMock(wraps=test_data.download_file)

        log_file = log_manager.get_next_log()

        expected_log_file = test_data.get_ns_file2()
        expected_log_file.local_path_txt = \
            os.path.join(test_data.TEMP_DIR, expected_log_file.filename_gz.replace('.gz', '.txt'))
        expected_log_file.local_path_gz = os.path.join(test_data.TEMP_DIR, expected_log_file.filename_gz)

        assert log_file is not None
        self.assertEqual(log_file, expected_log_file)
        self.assertTrue(os.path.isfile(log_file.local_path_txt))
        self.assertFalse(os.path.isfile(log_file.local_path_gz))

    def test_resume_unfinished_log_missing(self):
        resume_data = test_data.get_ns_file2()
        resume_data.processed = False
        resume_data.last_processed_line = 2

        with open(test_data.RESUME_PATH, 'wb') as file:
            pickle.dump(resume_data, file)

        config = test_data.create_config()
        config.log_download_dir = test_data.TEMP_DIR
        log_manager = LogManager(config)

        log_manager._list = MagicMock(return_value = \
            [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])
        log_manager._download = MagicMock(wraps=test_data.download_file)

        log_file = log_manager.get_next_log()

        expected_log_file = test_data.get_ns_file1()
        expected_log_file.local_path_txt = \
            os.path.join(test_data.TEMP_DIR, expected_log_file.filename_gz.replace('.gz', '.txt'))
        expected_log_file.local_path_gz = os.path.join(test_data.TEMP_DIR, expected_log_file.filename_gz)

        assert log_file is not None
        self.assertEqual(log_file, expected_log_file)
        self.assertTrue(os.path.isfile(expected_log_file.local_path_txt))
        self.assertFalse(os.path.isfile(expected_log_file.local_path_gz))

if __name__ == '__main__':
    unittest.main()
