import unittest
from os import path
from test import test_data

from src.config import read_yaml_config


class ConfigTest(unittest.TestCase):

    def test_read_yaml_config(self):
        expected_config = test_data.create_config()

        basepath = path.dirname(__file__)
        config_filename = path.join(basepath, 'data', 'test_config.yaml')
        with open(config_filename, 'r', encoding='utf-8') as config_file:
            config = read_yaml_config(config_file)
            self.assertEqual(config, expected_config)


if __name__ == '__main__':
    unittest.main()
