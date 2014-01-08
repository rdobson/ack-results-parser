#!/usr/bin/env python
import ftplib
import netrc


class SFFTPClient():

    def __init__(self):
        self.machine = 'citrix.sharefileftp.com'
        info = netrc.netrc("/home/sagnikd/.netrc")
        if info.authenticators(self.machine):
            (user, account, password) = info.authenticators(self.machine)
        else:
            print("User credentials not present in .netrc for %s"
                  % self.machine)
        self.session = ftplib.FTP(self.machine, user, password)

    def upload(self, upload_filepath, upload_path):
        """Uploads file to current directory on sharefile"""

        filename = upload_path.split('/')[-1]

        for dir in upload_path.split('/')[1:-1]:
            if dir not in self.session.nlst():
                print("Creating new dir %s" % dir)
                self.session.mkd(dir)
            self.session.cwd(dir)

        print ('Uploading file %s' % filename)
        print ('Upload to directory %s' % self.session.pwd())
        out = self.session.storbinary('STOR %s' % filename,
                                      open(upload_filepath, 'rb'),
                                      blocksize=8192*1024,
                                      )
        if re.search('Transfer Complete', out):
            print ("Transfer Completed.")
        else:
            print ("Transfer was unsuccessful. Please check file size")
        self.session.close()
