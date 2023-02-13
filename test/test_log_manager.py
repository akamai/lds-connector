import unittest

from src.connector import LogManager

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


