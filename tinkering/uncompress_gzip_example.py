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
