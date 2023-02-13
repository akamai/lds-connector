import unittest
from unittest.mock import MagicMock
import os
from os import path
import shutil

from src.log_manager import LogManager, _LogNameProps, _LogFile
from src.config import Config

from test import test_data

class LogManagerTest(unittest.TestCase):

    def test_create_ns_log_path(self):
        cp_code = 123456
        storage_group = 'test_account'
        log_directory = 'dns_logs'

        expected_path = '/123456/test_account/dns_logs/'
        actual_path = LogManager._create_ns_log_path(
            cp_code=cp_code,
            storage_group=storage_group,
            log_dir=log_directory)

        self.assertEqual(expected_path, actual_path)

    def test_create_ns_log_path_empty(self):
        cp_code = 123456
        storage_group = 'test_account'
        log_directory = ''

        expected_path = '/123456/test_account/'
        actual_path = LogManager._create_ns_log_path(
            cp_code=cp_code,
            storage_group=storage_group,
            log_dir=log_directory)

        self.assertEqual(expected_path, actual_path) 

    def test_parse_log_name(self):
        file_name = "cam_123456.edns_U.202301030300-0400-3.gz"

        expected_name_props = _LogNameProps(
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

        file2 = _LogFile(
            ns_path_gz='123456/cam/logs/cam_123456.edns_U.202301030400-0500-0.gz',
            filename_gz='cam_123456.edns_U.202301030400-0500-0.gz',
            size=2345,
            md5='5d41402abc4b2a76b9719d911017c592',
            name_props= _LogNameProps(
                customer_id='cam',
                cp_code=123456,
                format='edns',
                sorted=False,
                start_time=1672718400.0,
                part=0,
                encoding='gz'
            ),
            local_path_gz='',
            local_path_txt=''
        )

        log_files = LogManager._parse_list_response(list_response_xml)

        self.assertEqual(log_files, [file2])


    def test_determine_next_log_fresh(self):
        lm = LogManager(test_data.create_config())

        lm._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = lm._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file1())


    def test_determine_next_log_skip_older_time(self):
        lm = LogManager(test_data.create_config())
        lm.last_log_file = test_data.get_ns_file1()

        lm._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = lm._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file2())


    def test_determine_next_log_skip_older_part(self):
        lm = LogManager(test_data.create_config())
        lm.last_log_file = test_data.get_ns_file2()

        lm._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = lm._determine_next_log()

        self.assertEqual(next_log, test_data.get_ns_file3())

    
    def test_determine_next_log_all_done(self):
        lm = LogManager(test_data.create_config())
        lm.last_log_file = test_data.get_ns_file3()

        lm._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])

        next_log = lm._determine_next_log()

        self.assertIsNone(next_log)

    
    def test_determine_next_log_none(self):
        lm = LogManager(test_data.create_config())
        lm.last_log_file = test_data.get_ns_file3()

        lm._list = MagicMock(return_value = [])

        next_log = lm._determine_next_log()

        self.assertIsNone(next_log)

        
    def test_get_next_log(self):
        config = test_data.create_config()
        config.log_download_dir = LogManagerTest._create_download_dir()
        lm = LogManager(config)

        lm._list = MagicMock(return_value = [test_data.get_ns_file1(), test_data.get_ns_file2(), test_data.get_ns_file3()])
        lm._download = MagicMock(wraps=LogManagerTest._download_file)

        log_file = lm.get_next_log()
        assert log_file != None
        
        # Assert text file exists
        expected_txt_path = os.path.join(test_data.TEMP_DIR, test_data.get_ns_file1().filename_gz.replace('.gz', '.txt'))
        self.assertEqual(log_file.local_path_txt, expected_txt_path)
        self.assertTrue(os.path.isfile(expected_txt_path))

        # Assert Gzip file was deleted
        expected_gz_path = os.path.join(test_data.TEMP_DIR, test_data.get_ns_file1().filename_gz)
        self.assertEqual(log_file.local_path_gz, expected_gz_path)
        self.assertFalse(os.path.isfile(expected_gz_path))

        os.remove(expected_txt_path)
        os.rmdir(config.log_download_dir)


    '''
    Mock method of downloading a file

    The desired log file is assumed to exist in data/ directory. 
    It's copied into the tmp/ download directory.
    This allows unit testing the Gzip deletion.
    '''
    @staticmethod
    def _download_file(log_file: _LogFile):
        source_path: str = path.join(test_data.DATA_DIR, log_file.filename_gz)
        dest_path: str = path.join(test_data.TEMP_DIR, log_file.filename_gz)
        shutil.copyfile(source_path, dest_path)

        log_file.local_path_gz = dest_path


    @staticmethod
    def _create_download_dir():
        if not path.isdir(test_data.TEMP_DIR):
            os.mkdir(test_data.TEMP_DIR)

        return test_data.TEMP_DIR


if __name__ == '__main__':
    unittest.main()

