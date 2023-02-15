import argparse
import shutil

from lds_connector.config import read_yaml_config
from lds_connector.log_manager import LogManager

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog = 'test_log_manager_integ',
        description = 'Integration test the LogManager -> NetStorage interaction')
    parser.add_argument('-c', '--config', required=True, type=argparse.FileType('r'))
    args = parser.parse_args()

    config = read_yaml_config(args.config)
    args.config.close()
    assert config is not None

    log_manager = LogManager(config)

    log_file = log_manager.get_next_log()

    print(log_file)

    shutil.rmtree(config.log_download_dir)
