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

import argparse
import gzip
import os
import shutil

from gzip import GzipFile

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog = 'uncompress_gzip_example',
        description = 'Uncompress GZip file')
    parser.add_argument('gzip_file_path', help="GZip file to uncompress")
    args = parser.parse_args()

    path, extension = os.path.splitext(args.gzip_file_path)
    new_path: str = path + ".txt"

    print("Uncompressing file " + args.gzip_file_path + " into " + new_path)

    with gzip.open(args.gzip_file_path, 'rb') as compressed_file:
        with open(new_path, 'wb') as uncompressed_file:
            assert isinstance(compressed_file, GzipFile)
            shutil.copyfileobj(compressed_file, uncompressed_file)

    print("Finished uncompressing file")
