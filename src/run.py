import logging
import argparse

from src.config import read_yaml_config
from src.connector import Connector

if __name__ == '__main__':
    # Parse command line arguments 
    parser = argparse.ArgumentParser(
        prog = 'lds_connector.py',
        description = 'Connector script to move Akamai Log Delivery Service (LDS) logs from NetStorage into Splunk')
    parser.add_argument('--config', 
        required=True,
        help='destination of the YAML configuration file',
        type=argparse.FileType('r'))
    parser.add_argument('--level',
        help='log level',
        choices=['DEBUG', 'INFO', 'DEFAULT'],
        default='DEFAULT'
    )
    args = parser.parse_args()

    # Set log level
    logging.basicConfig(level=logging.WARNING if args.level == 'DEFAULT' else args.level)


    # Parse config from YAML file stream
    config = read_yaml_config(args.config)
    args.config.close()

    # Start connector
    connector = Connector(config)
    connector.run() # TODO: call this on a timer
