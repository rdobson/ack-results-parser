#!/usr/bin/env python

from jira.client import JIRA, GreenHopper

from xsjira.models import *
from sfftp.client import *

server_url = 'https://tracker-test.uk.xensource.com'

jira = JIRA(options={'server': server_url},
            )


class RemoteCopyToCRD():
    """Create remote copy in Project CRD of given ticket for
       update marketplace.
    """
    #TODO
    crd_user = 'sagnikd'
    crd_pjt_key = 'HCL'

    def add_hcl_link_comment(self, master_ticket, crd_ticket):
        for comment in master_ticket.list_comments():
            if re.search("http://", comment.body):
                crd_ticket.add_comment(comment.body)

    def get_doc_attachment(self, master_ticket):
        for file in master_ticket.issue.fields.attachment:
            if re.search('doc', file.filename):
                return (master_ticket.get_attachment_path(file.id),
                        file.filename)
        print("Error: Missing the Verification Form (doc) which is " +
              "needed to update Citrix Ready for market place.")
        return (None, None)

    def run(self, master_ticket):

        (filepath, filename) = self.get_doc_attachment(master_ticket)
        if filepath:
            t = master_ticket.create_issue(
                {
                    'project': {'key': self.crd_pjt_key},
                    'summary': 'CLONE Of %s' % master_ticket.get_summary(),
                    'issuetype': {'name': 'Task'},
                    'description': 'Please add the device to marketplace',
                }
                )

        self.crd_ticket = Task(jira, t.key)
        self.crd_ticket.create_issue_link(master_ticket.key)

        self.add_hcl_link_comment(master_ticket, self.crd_ticket)
        self.crd_ticket.add_attachment(filepath, filename)
        self.crd_ticket.add_comment(
            "Hi Gaurav,\nCould you please update this to market " +
            "place and attach the link.\nThanks,\nSagnik"
            )
        self.crd_ticket.assign_issue(self.crd_user)
        return self.crd_ticket


def main(options):
    #Dictionary which maps the Folder directory with the type
    tag_dict = {'server': 'Servers',
                'stor': 'Storage Arrays',
                'nic': 'NICs',
                'hba': 'HBAs and CNAs',
                'cna': 'HBAs and CNAs',
                'gpu': 'GPUs',
                'dd': 'Driver Disks',
                'test': 'blaj'}
    version_list = [
        'Other',
        'XenServer 5.0',
        'XenServer 5.5',
        'XenServer 5.6',
        'XenServer 5.6.x',
        'XenServer 6.0.x',
        'XenServer 6.1.0',
        'XenServer 6.2.0'
        ]

    key = options.subtype
    if tag_dict[key] == 'server':
        ticket = HCLSubmission(jira, options.ticket)
    else:
        ticket = GenericSubmission(jira, options.ticket)
    print ticket.get_summary()

    #For non HCL Submission, we need additional parameters as below
    product_name = options.name
    version = options.version

    #To display the ack-submission if there is one:
    if ticket.get_type() == 'HCL Submission':
        (ack_path, ack_filename) = ticket.get_ack_attachment()
        print ("%s found.\nExtracting Product Info.." % ack_filename)
        dict = ticket.get_ack_attachment_dict(ack_path)
        version = dict['xs_version']

        #if Device Tested is empty, product name will be taken from result dict
        if not product_name:
            product_name = ticket.get_device_tested()
        else:
            product_name = "%s %s" % (dict['system-manufacturer'].strip(),
                                      dict['product'].strip())
    print ("\nDevice Tested: %s" % product_name)

    #derive upload_path for FTP upload
    upload_path = "/XenServer HCL/Hardware Certification Logs"
    for v in version_list:
        if re.search(version, v):
            upload_path += "/%s" % v
            break
    upload_path += "/%s" % tag_dict[key]
    upload_path += "/%s" % product_name
    zipfile = ticket.issue.key + ".zip"
    upload_path += "/%s" % zipfile

    #Path of zipfile that will be stored
    zippath = ticket.get_attachmentzip_path(ticket.issue.id)
    SFFTPClient().upload(zippath, upload_path)

    #RemoteCopy to CRD if required.
    t2 = RemoteCopyToCRD().run(ticket)
    if t2 is not None:
        print ("%s Created" % t2.key)
        print (t2.get_summary())

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--ticket", dest="ticket", required=True,
                        help="HCL-435,(server|stor|nic|hba|cna|gpu|dd)," +
                        " 6.2.0[Optional], Product_Name [Optional]")
    parser.add_argument("-s", "--subtype", dest="subtype", required=True)
    parser.add_argument("-v", "--version", dest="version", required=False)
    parser.add_argument("-n", "--name", dest="name", required=False)
    args = parser.parse_args()
    main(args)
