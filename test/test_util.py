import os
from os import path
import json
import shutil

from test import test_data
from lds_connector.log_file import LogFile
from lds_connector.log_manager import LogManager


def read_json(filename: str):
    json_path = path.join(path.dirname(__file__), 'data/', filename)
    json_data = {}
    with open(json_path, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)

    return json_data


def download_file(log_file: LogFile):
    """
    Mock method of downloading a file

    The desired log file is assumed to exist in data/ directory. 
    It's copied into the tmp/ download directory.
    This allows unit testing the Gzip deletion.
    """
    source_path: str = path.join(test_data.DATA_DIR, log_file.filename_gz)
    dest_path: str = path.join(test_data.TEMP_DIR, log_file.filename_gz)
    shutil.copyfile(source_path, dest_path)

    log_file.local_path_gz = dest_path


def download_uncompress_file(log_file: LogFile):
    download_file(log_file)
    LogManager._uncompress(log_file)
    os.remove(log_file.local_path_gz)
