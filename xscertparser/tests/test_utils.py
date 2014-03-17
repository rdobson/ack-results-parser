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
        'testfile4':'data4'
    }

    TAR_FILE = None

    def setUp(self):
        """Initialise the test class by creating a tarfile."""
        tmp_dir = tempfile.mkdtemp()
        self.subdir = 'subdir'
        os.mkdir("%s/%s" % (tmp_dir, self.subdir))

        self.TAR_FILE = "%s/test.tar" % tmp_dir
        tar = tarfile.open(self.TAR_FILE, 'w')

        for filename, data in self.TAR_FILES.items():
            tmp_file = "%s/%s/%s" % (tmp_dir, self.subdir, filename)
            fileh = open(tmp_file, 'w')
            fileh.write(data)
            fileh.close()
            tar.add(tmp_file)
                
        tar.close()

    def _extract_file_from_tar(self, fpath, fullpathknown=True):
        """Test the means of extracting a file"""
        tmp_dir = tempfile.mkdtemp()
        testfile = extract_file_from_tar(self.TAR_FILE, fpath,
                                         tmp_dir, fullpathknown)
        fh = open(testfile, 'r')
        data = fh.read()
        fh.close()

        self.assertEqual(data, self.TAR_FILES[key])


    def test_extraction_using_fullpath(self):
        """Test the means of extracting a file"""
        self._extract_file_from_tar('%s/testfile3' % self.subdir)
    
    def testp_extraction_using_regex(self):    
        """Postive Test to test the means of extracting a file"""
        self._extract_file_from_tar('testfile2', False)

    def testn_extraction_using_regex(self):
        """Negative Test to test the means of extracting a file"""   
        try:
            self._extract_file_from_tar('testfile', False)
        except Exception, e:
            print "Returned exception as expected for an entry with \
                   non-unique regex"
            














