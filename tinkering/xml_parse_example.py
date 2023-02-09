import xml.etree.ElementTree as ET

if __name__ == '__main__':

    list_xml_response = '''<?xml version="1.0" encoding="ISO-8859-1"?>
    <list>
        <file type="dir" name="1234/example/"/>
        <file type="dir" name="1234/example/directory/"/>
        <file type="dir" name="1234/example/directory/dir/"/>
        <file type="symlink" name="1234/example/foo"/>
        <file type="file" name="1234/example/passwd" size="2604" md5="9b04178910b52bca293f78f947d79686" mtime="1626900592"/>
        <file type="dir" name="1234/example/passwd/"/>
    </list>'''

    root = ET.fromstring(list_xml_response)

    assert root.tag == 'list'
    for child in root:
        assert child.tag == 'file'

        print('Type: ' + str(child.get('type')))
        print('Name: ' + str(child.get('name')))
        print('Size: ' + str(child.get('size')))
        print('MD5: ' + str(child.get('md5')))
        print()

