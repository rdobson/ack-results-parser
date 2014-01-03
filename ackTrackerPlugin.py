#!/usr/bin/env python                                                     
                                                                          
from jira.client import JIRA, GreenHopper                                 
#from creds import *                                                       
import tempfile, tarfile, os
from acklogparser import *
import ftplib, netrc
from argparse import ArgumentParser                                                                          
server_url = 'https://tracker-test.uk.xensource.com'                                                         
                                                                          
jira = JIRA(options={'server':server_url},                                
            #basic_auth=(tracker_username, tracker_password),              
           )                                                              
                                                                          
class JiraTicket(object):                                                 
                                                                          
    def __init__(self, jira, ticket_id):                                  
        self.jira = jira                                                  
        self.tid = ticket_id  
        self.issue = jira.issue(ticket_id, expand="attachment")           
        self.key = self.issue.key
        self.validate()                                                   
                                                                          
    def validate(self):                                                   
        pass                                                              
                                                                          
    def get_type(self):                                                   
        return self.issue.fields.issuetype.__dict__['name']               
                                                                          
    def get_field(self, name):                                            
        return getattr(self.issue.fields, name)                           
                                                                          
    def get_summary(self):                                                
        return self.get_field('summary')                                  
                                                                          
    def get_description(self):                                            
        return self.get_field('description')                              
    
    def get_attachment_object(self, id):
        return jira.attachment(id)                                                                      

    def get_attachment_path(self, id):                                            
        """Returns attachment file path"""
        att_obj = self.get_attachment_object(id)
        url = att_obj.raw['content']
        (fh, attachment_path) = tempfile.mkstemp()
        os.close(fh)
        os.system("curl -n %s -o %s -s" % (url,attachment_path))
        return attachment_path
    
    def get_attachmentzip_path(self, id):
        """Returns attachment file path"""
        url = "%s/secure/attachmentzip/%s.zip" % (server_url, id)
        (fh, zippath) = tempfile.mkstemp()
        os.close(fh)
        os.system("curl -n %s -o %s -s" % (url,zippath))           
        return zippath
    
    def create_issue_link(self, remote_key):
        """:param remote_key is key of the remote ticket to be linked"""
        return self.jira.create_issue_link('Related',self.key,remote_key)                                                                      

    def add_comment(self, comment):
        return self.jira.add_comment(self.key, comment)

    def create_issue(self, field_dict):
        return self.jira.create_issue(fields= field_dict)

    def assign_issue(self, user):
        print (user)
        return self.jira.assign_issue(self.key, user)

    def list_comments(self): 
        return self.jira.comments(self.key)

    def add_attachment(self, filepath, filename):
        return (self.jira.add_attachment(self.issue, filepath, filename))
        
class EpicTicket(JiraTicket):                                             
                                                                          
    def get_epic_name(self):                                              
        epic_name_field_id = 'customfield_11337'                          
        return self.issue.__dict__['raw']['fields'][epic_name_field_id]   
                                                                          
                                                                          
class HCLSubmission(JiraTicket):                                          
    def validate(self):                                                   
        if self.get_type() != 'HCL Submission':                           
            raise Exception("Not a HCL Submission! (%s)" % self.get_type())
    
    def get_ack_attachment(self):
        """Returns tuple of (ack_path, ack_filename)"""
        for file in self.issue.fields.attachment:
            if 'ack-submission' in file.filename:
                return (self.get_attachment_path(file.id), file.filename)
        print ("Error: ACK Submission Log is missing in this HCL Submission")
        return (None,None)
    
    def get_ack_attachment_dict(self, att_path):
        """if type ==Server, Prints dict and returns Dict"""
        #TODO Add type check
        result_dict = result_parser(att_path,os.getcwd())
        #TODO Remove printing Dict here :
        display_results(result_dict)
        return result_dict

    def get_sub_type(self):
        """Classify the submission into Server|Storage|NIC|HBA|CNA|GPU|DD"""
        #TODO
        
        pass

    def get_device_tested(self):
        """Derives name from Device Tested Column"""
        return self.issue.fields.customfield_10132


class DDSubmission(HCLSubmission):
    def validate(self):
        if self.get_type() != 'Driver Disk Submission':
            raise Exception("Not a DD Submission! (%s)" % self.get_type())

class Task(HCLSubmission): 
    def validate(self):
        if self.get_type() != 'Task':
            raise Exception("Not a Task! (%s)" % self.get_type())           

class GenericSubmission(HCLSubmission):
    def validate(self):
        pass

class RemoteCopyToCRD():
    """Create remote copy in Project CRD of given ticket for update marketplace"""
    #TODO
    crd_user = 'sagnikd'
    crd_pjt_key = 'HCL'

    def add_hcl_link_comment(self, master_ticket, crd_ticket):
        for comment in master_ticket.list_comments():
            if re.search("http://", comment.body):
                crd_ticket.add_comment(comment.body)

    def get_doc_attachment(self, master_ticket):
        for file in master_ticket.issue.fields.attachment:
            if re.search ("msword",file.mimeType):
                return (master_ticket.get_attachment_path(file.id), file.filename)
        print("Error: Missing the Verification Form (doc) which is needed to update Citrix Ready for market place.")
        return (None, None)
                         
    def run(self, master_ticket):
        
        (filepath, filename) = self.get_doc_attachment(master_ticket)
        if filepath:
            t = master_ticket.create_issue( 
                        {'project'  : {'key': self.crd_pjt_key},
                         'summary'   : 'CLONE Of %s' % master_ticket.get_summary(),
                         'issuetype' : {'name':'Task'},           
                         'description': 'Please add the device to marketplace'
                         })
        
        self.crd_ticket = Task(jira,t.key)
        self.crd_ticket.create_issue_link(master_ticket.key)
        
        self.add_hcl_link_comment(master_ticket, self.crd_ticket)
        self.crd_ticket.add_attachment(filepath, filename)
        self.crd_ticket.add_comment("Hi Gaurav,\nCould you please update this to market place and attach the link.\nThanks,\nSagnik")
        self.crd_ticket.assign_issue(self.crd_user)
        return self.crd_ticket


class SFFTPClient():

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

            
    
def main(options):
    #Dictionary which maps the Folder directory with the type 
    tag_dict = {'server':'Servers','stor':'Storage Arrays','nic': 'NICs' ,'hba':'HBAs and CNAs', 'cna':'HBAs and CNAs', 'gpu':'GPUs', 'dd':'Driver Disks', 'test':'blaj'}
    
    key = options.key.split(',')[1]
    if tag_dict[key] == 'server':
        ticket = HCLSubmission(jira, options.key.split(',')[0])
    else:
        ticket = GenericSubmission(jira, options.key.split(',')[0])
    print ticket.get_summary()

    #For non HCL Submission, we need additional parameters as below
    if len(options.key.split(','))> 2:
        product_name = options.key.split(',')[3]
        version = options.key.split(',')[2]        
    
    #To display the ack-submission if there is one:
    if ticket.get_type() == 'HCL Submission':
        (ack_path, ack_filename) = ticket.get_ack_attachment()
        print ("%s found.\nExtracting Product Info.." % ack_filename)
        dict = ticket.get_ack_attachment_dict(ack_path)
        version = dict['xs_version']

        product_name = ticket.get_device_tested()  #override product name with "Device Tested" field
        #if Device Tested is empty, product name will be taken from result dict
        if not product_name:
            product_name = "%s %s" % (dict['system-manufacturer'].strip(), 
                                      dict['product'].strip())
    print ("\nDevice Tested: %s" % product_name)
    
    session = SFFTPClient().traverse_to_upload_path(version, tag_dict[key], product_name)
    #Path of zipfile that will be stored
    zippath = ticket.get_attachmentzip_path(ticket.issue.id)
    zipfile = ticket.issue.key + ".zip"
    SFFTPClient().upload_file(session, zippath, zipfile)
    
    #RemoteCopy to CRD if required. 
    t2 = RemoteCopyToCRD().run(ticket)
    if t2 is not None:
        print ("%s Created" % t2.key)
        print (t2.get_summary())

if __name__ == "__main__":
     parser = ArgumentParser()
     parser.add_argument("-t", "--ticket", dest="key",required=True,help="HCL-435,(server|stor|nic|hba|cna|gpu|dd), 6.2.0[Optional], Product_Name [Optional]")
     args = parser.parse_args() 
     main(args)

