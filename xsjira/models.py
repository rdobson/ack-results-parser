"""Module for Jira bindings onto XS tracker instance"""

import os
import tempfile
from xscertparser.cmd.acklogparser import result_parser
from xscertparser.cmd.acklogparser import display_results


class JiraTicket(object):
    """Base jira ticket class"""

    def __init__(self, jira, ticket_id):
        self.jira = jira
        self.tid = ticket_id
        self.issue = jira.issue(ticket_id, expand="attachment")
        self.key = self.issue.key
        self.server_url = self.jira.client_info()  # TODO: set based on Jira object
        self.validate()

    def get_server_url(self):
        """Return the Jira server URL on which this issue resides"""
        return self.server_url

    def validate(self):
        """Validate the tickets contents"""
        pass

    def get_type(self):
        """Returns the tickets issue type"""
        return self.issue.fields.issuetype.__dict__['name']

    def get_field(self, name):
        """Returns the contents of a ticket field"""
        return getattr(self.issue.fields, name)

    def get_summary(self):
        """Returns the the issue summary"""
        return self.get_field('summary')

    def get_description(self):
        """Returns the issue description"""
        return self.get_field('description')

    def get_attachment_object(self, aid):
        """Returns the specified ticket attachment"""
        return self.jira.attachment(aid)

    def get_attachment_path(self, aid):
        """Returns attachment file path"""
        att_obj = self.get_attachment_object(aid)
        url = att_obj.raw['content']
        (fileh, attachment_path) = tempfile.mkstemp()
        os.close(fileh)
        os.system("curl -n %s -o %s -s" % (url, attachment_path))
        return attachment_path

    def create_issue_link(self, remote_key):
        """:param remote_key is key of the remote ticket to be linked"""
        return self.jira.create_issue_link('Related', self.key, remote_key)

    def add_comment(self, comment):
        """Add a comment to the issue"""
        return self.jira.add_comment(self.key, comment)

    def create_issue(self, field_dict):
        """Create a new Jira issue"""
        return self.jira.create_issue(fields=field_dict)

    def assign_issue(self, user):
        """Assign the issue to a specified user"""
        print user
        return self.jira.assign_issue(self.key, user)

    def list_comments(self):
        """Return a list of comments made to this issue"""
        return self.jira.comments(self.key)

    def add_attachment(self, filepath, filename):
        """Add an attachment to this issue"""
        return self.jira.add_attachment(self.issue, filepath, filename)


class EpicTicket(JiraTicket):
    """Class for representing epic tickets"""

    def get_epic_name(self):
        """Return the epic name associated with this epic issue"""
        epic_name_field_id = 'customfield_11337'
        return self.issue.__dict__['raw']['fields'][epic_name_field_id]


class HCLSubmission(JiraTicket):
    """Class for representing HCLSubmission issues"""

    def validate(self):
        """Override the validate class to ensure correct type"""
        if self.get_type() != 'HCL Submission':
            raise Exception("Not a HCL Submission! (%s)" % self.get_type())

    def get_ack_attachment(self):
        """Returns tuple of (ack_path, ack_filename)"""
        for afile in self.issue.fields.attachment:
            if 'ack-submission' in afile.filename:
                return (self.get_attachment_path(afile.id), afile.filename)
        print "Error: ACK Submission Log is missing in this HCL Submission"
        return (None, None)

    def get_ack_attachment_dict(self, att_path):  # pylint: disable=R0201
        """if type ==Server, Prints dict and returns Dict"""
        #TODO Add type check
        result_dict = result_parser(att_path, os.getcwd())
        #TODO Remove printing Dict here :
        display_results(result_dict)
        return result_dict

    def get_device_tested(self):
        """Derives name from Device Tested Column"""
        return self.issue.fields.customfield_10132

    def get_attachmentzip_path(self, aid):
        """Returns attachment file path"""
        url = "%s/secure/attachmentzip/%s.zip" % (self.get_server_url(), aid)
        (fileh, zippath) = tempfile.mkstemp()
        os.close(fileh)
        os.system("curl -n %s -o %s -s" % (url, zippath))
        return zippath


class DDSubmission(HCLSubmission):
    """Driver Disk Submission"""

    def validate(self):
        """Override validation"""
        if self.get_type() != 'Driver Disk Submission':
            raise Exception("Not a DD Submission! (%s)" % self.get_type())


class Task(HCLSubmission):
    """Task"""

    def validate(self):
        """Override validation"""
        if self.get_type() != 'Task':
            raise Exception("Not a Task! (%s)" % self.get_type())


class GenericSubmission(HCLSubmission):
    """Generic HCL Submission"""

    def validate(self):
        """Override validate"""
        pass
