"""Tests for the utils.py module"""

import unittest
import tempfile
import tarfile
import os
from xscertparser.utils import extract_file_from_tar


class TarTestCase(unittest.TestCase):
    """Module for manipulating tar files"""

    TAR_FILES = {
        'testfile1': 'data1',
        'testfile2': 'data2',
        'testfile3': 'data3',
    }

    TAR_FILE = None

    def setUp(self):
        """Initialise the test class by creating a tarfile."""
        tmp_dir = tempfile.mkdtemp()
        subdir_n = 'files'
        os.mkdir("%s/%s" % (tmp_dir, subdir_n))

        self.TAR_FILE = "%s/test.tar" % tmp_dir
        tar = tarfile.open(self.TAR_FILE, 'w')

        for filename, data in self.TAR_FILES.items():
            tmp_file = "%s/%s/%s" % (tmp_dir, subdir_n, filename)
            fileh = open(tmp_file, 'w')
            fileh.write(data)
            fileh.close()
            tar.add(tmp_file)

        tar.close()

    def test_extract_file_from_tar(self):
        """Test the means of extracting a file"""
        tmp_dir = tempfile.mkdtemp()
        key = 'testfile3'
        testfile = extract_file_from_tar(self.TAR_FILE,
                                         key,
                                         tmp_dir)
        fh = open(testfile, 'r')
        data = fh.read()
        fh.close()

        self.assertEqual(data, self.TAR_FILES[key])
