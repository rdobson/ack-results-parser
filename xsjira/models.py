#!/usr/bin/env python

import os


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
        os.system("curl -n %s -o %s -s" % (url, attachment_path))
        return attachment_path

    def create_issue_link(self, remote_key):
        """:param remote_key is key of the remote ticket to be linked"""
        return self.jira.create_issue_link('Related', self.key, remote_key)

    def add_comment(self, comment):
        return self.jira.add_comment(self.key, comment)

    def create_issue(self, field_dict):
        return self.jira.create_issue(fields=field_dict)

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
        return (None, None)

    def get_ack_attachment_dict(self, att_path):
        """if type ==Server, Prints dict and returns Dict"""
        #TODO Add type check
        result_dict = result_parser(att_path, os.getcwd())
        #TODO Remove printing Dict here :
        display_results(result_dict)
        return result_dict

    def get_device_tested(self):
        """Derives name from Device Tested Column"""
        return self.issue.fields.customfield_10132

    def get_attachmentzip_path(self, id):
        """Returns attachment file path"""
        url = "%s/secure/attachmentzip/%s.zip" % (server_url, id)
        (fh, zippath) = tempfile.mkstemp()
        os.close(fh)
        os.system("curl -n %s -o %s -s" % (url, zippath))
        return zippath


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
