"""Utils module for xscertparser"""

import os, re
import tarfile

def extract_file_from_tar(tarfilepath, fpath, dest, fullpathknown=True):
    """Extract file from tar archive when partial/ full path is provided"""
    tarf = tarfile.open(tarfilepath)
    if not fullpathknown:
        fpaths = get_tarpaths_using_regex(tarfilepath, regex=fpath)
        if len(fpaths) != 1:
            raise Exception("None or more than one file found for " + 
                            "'%s': %s in tarfile %s" % (fpath, fpaths, \
                                                        tarf.name))
        else:
            fpath = fpaths.pop()
    
    tarf.extract(fpath, path=dest)
    return os.path.join(dest, fpath)

def get_tarpaths_using_regex(tarfilepath, regex):
    """Get filepaths list available in tar archive from the given regex"""
    tarf = tarfile.open(tarfilepath)
    path = filter(lambda x: re.search(regex, x), tarf.getnames())
    return path
    
