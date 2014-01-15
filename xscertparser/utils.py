"""Utils module for xscertparser"""

import os
import tarfile


def extract_file_from_tar(tarfilename, filename, dest):
    """Extract a specified file from a tar archive"""
    tarf = tarfile.open(tarfilename)  # tarfilename is path of tar
    matched_files = [filep for filep in tarf.getnames()
                     if filename == os.path.basename(filep)]
    if not matched_files:
        raise Exception("Could not find filename %s in tarfile %s" %
                        (filename, tarfilename))
    if len(matched_files) > 1:
        raise Exception("Found more than one filename for %s: %s" %
                        (filename, matched_files))
    fpath = matched_files.pop()
    tarf.extract(fpath, path=dest)
    return os.path.join(dest, fpath)
