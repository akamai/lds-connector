import unittest
from os import path

from src.config import read_yaml_config, Config, NetStorageConfig

class ConfigTest(unittest.TestCase):

    def test_read_yaml_config(self):
        expected_config = Config(
            netstorage_config=NetStorageConfig(
                host="test_ns_host",
                account="test_ns_account",
                cp_code=123456,
                key="test_key",
                use_ssl=True
            )
        )

        basepath = path.dirname(__file__)
        config_filename = path.join(basepath, 'data', 'test_config.yaml')
        with open(config_filename, 'r') as config_file:
            config = read_yaml_config(config_file)

            print(config)
            self.assertEqual(config, expected_config)

if __name__ == '__main__':
    unittest.main()
