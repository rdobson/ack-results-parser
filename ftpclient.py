#!/usr/bin/env python                                                     
                                                                          
from acklogparser import *
import ftplib, netrc
                                                                          
class FTPClient():
    
    def __init__(self):
        self.machine = 'citrix.sharefileftp.com'

    def get_session(self, machine):
        info = netrc.netrc("/home/sagnikd/.netrc")
        if info.authenticators(machine):
            (user, account, password)= info.authenticators(machine)
        else:
            print("User credentials not present in .netrc for %s" % machine)
        return ftplib.FTP(machine,user,password)

    def get_ticket_type(self, attachment):
        """Determines and returns the type of submission = 'Servers'|'Storage Arrays'|'NICs'|'HBAs and CNAs'|'GPUs'|'Driver Disks'"""
        pass
            
    def traverse_to_upload_path(self, version, ticket_type, filename):
        """Returns the session created after traversing to appropriate upload path for the required XS version and ticket type"""
        session = self.get_session(self.machine)       
        #Logs are stored in /XenServer HCL/Hardware Certification Logs/XenServer *
        try:
            session.cwd('XenServer HCL')
            session.cwd('Hardware Certification Logs')
            for folder in session.nlst():
                if re.search(version, folder):
                    session.cwd(folder)
                    session.cwd(ticket_type)
                    
                    #Note filename is the product name
                    #filename =  "%s %s" % (manufacturer, product)
                    print ("\n")
                    if filename not in session.nlst():
                        session.mkd(filename)
                    else:
                        print ("Submission found to be already existing. Adding these logs in the same folder.")
                    session.cwd(filename)
                    print ("Successfully traversed to upload path: %s" % session.pwd())
                    return session
            print("Could not find the version at all")
        except:
            print ("FTP Directory doesn't exist. Must ahve been moved.")            
            session.close() 
              
    def upload_file(self, session, upload_filepath, filename):
        """Uploads file to current directory on sharefile"""
        print ('Uploading file %s' % filename)
        print ('Upload to directory %s' % session.pwd())
        out = session.storbinary('STOR %s' % filename ,open(upload_filepath, 'rb'), blocksize = 8192*1024)
        if re.search('Transfer Complete', out):
            print ("Transfer Completed.")
            return
        else:
            print ("Transfer was unsuccessful. Please check file size")

    
