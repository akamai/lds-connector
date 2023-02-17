import unittest
from os import path
from test import test_data

from lds_connector.config import read_yaml_config


class ConfigTest(unittest.TestCase):

    def test_read_yaml_config(self):
        expected_config = test_data.create_config()

        config_filename = path.join(test_data.DATA_DIR, 'test_config1.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


    def test_read_yaml_config_optional(self):
        expected_config = test_data.create_config()
        expected_config.splunk_config.hec_index = None
        expected_config.splunk_config.hec_source_type = None
        expected_config.poll_period_sec = 60

        config_filename = path.join(test_data.DATA_DIR, 'test_config2.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


if __name__ == '__main__':
    unittest.main()
