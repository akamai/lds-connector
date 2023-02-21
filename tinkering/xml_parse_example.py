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

import xml.etree.ElementTree as ET

if __name__ == '__main__':
    LIST_XML_RESPONSE = '''<?xml version="1.0" encoding="ISO-8859-1"?>
    <list>
        <file type="dir" name="1234/example/"/>
        <file type="dir" name="1234/example/directory/"/>
        <file type="dir" name="1234/example/directory/dir/"/>
        <file type="symlink" name="1234/example/foo"/>
        <file type="file" name="1234/example/passwd" size="2604" md5="9b04178910b52bca293f78f947d79686" mtime="1626900592"/>
        <file type="dir" name="1234/example/passwd/"/>
    </list>'''

    root = ET.fromstring(LIST_XML_RESPONSE)

    assert root.tag == 'list'
    for child in root:
        assert child.tag == 'file'

        print('Type: ' + str(child.get('type')))
        print('Name: ' + str(child.get('name')))
        print('Size: ' + str(child.get('size')))
        print('MD5: ' + str(child.get('md5')))
        print()

