"""Collection of client related methods for interacting with Sharefile."""
import ftplib
import netrc
import re


class SFFTPClient(object):
    """ShareFile FTP Client class for pushing/getting files"""

    def __init__(self):
        self.machine = 'citrix.sharefileftp.com'
        info = netrc.netrc("/home/sagnikd/.netrc")
        creds = info.authenticators(self.machine)
        if creds:
            (user, _, password) = creds  # pylint: disable=W0633
        else:
            print("User credentials not present in .netrc for %s"
                  % self.machine)
        self.session = ftplib.FTP(self.machine, user, password)

    def upload(self, upload_filepath, upload_path):
        """Uploads file to current directory on sharefile"""
        filename = upload_path.split('/')[-1]

        for directory in upload_path.split('/')[1:-1]:
            if directory not in self.session.nlst():
                print "Creating new dir %s" % directory
                self.session.mkd(directory)
            self.session.cwd(directory)

        print 'Uploading file %s' % filename
        print 'Upload to directory %s' % self.session.pwd()
        out = self.session.storbinary('STOR %s' % filename,
                                      open(upload_filepath, 'rb'),
                                      blocksize=8192*1024,
                                      )
        if re.search('Transfer Complete', out):
            print "Transfer Completed."
        else:
            print "Transfer was unsuccessful. Please check file size"
        self.session.close()

    def download(self, remote_path, download_path):
        """Download file to specified directory"""
        pass
