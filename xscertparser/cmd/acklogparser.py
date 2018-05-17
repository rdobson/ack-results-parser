"""Entry point script for parsing specified log files"""

from argparse import ArgumentParser
from xscertparser.utils import extract_file_from_tar
from xscertparser import xmltojson
import os
import re
import xml.dom.minidom
import pprint
from hwinfo.tools import inspector
import tempfile
import shutil
import tarfile
from pymongo import MongoClient
# import models

NICS_DICT = {}
HBAS_DICT = {}
MACHINE_DICT = {"pass": [], "fail": []}  # seprates server Products PASS/FAIL
FAILED_DICT = {}
SERVER_DICT = {
    'xs_version': u'None',
    'system-manufacturer': 'None',
    'sockets': 'None',
    'product': 'None',
    'chassis': 'None',
    'modelname': 'None',
    'family': 'None',
    'model': 'None',
    'stepping': 'None',
    'nics': [],
    'hbas': [],
    }


def result_parser(tarfilename, logsubdir):  # pylint: disable=R0914,R0912
    """Parse a specified log archive"""
    bugtool_path = extract_file_from_tar(tarfilepath=tarfilename,
                                         fpath="bug-report",
                                         dest=logsubdir,
                                         fullpathknown=False)
    testconf_path = extract_file_from_tar(tarfilename,
                                          'test_run.conf',
                                          logsubdir,
                                          fullpathknown=False)
    dmidecode_path = extract_file_from_tar(
        os.path.join(logsubdir, bugtool_path),
        'dmidecode.out',
        logsubdir,
        False)
    # xapi_db_path = extract_from_tar_with_bname (os.path.join(logsubdir,
    # --> bugtools_path), 'xapi-db.xml', logsubdir)
    lspcivv_path = extract_file_from_tar(
        os.path.join(logsubdir, bugtool_path),
        'lspci-vv.out',
        logsubdir,
        False)
    # get NIC Names, CPU
    test_conf = xml.dom.minidom.parse(open(testconf_path))

    # XS-version
    for version in test_conf.getElementsByTagName("global_config"):
        if 'xs_version' in version.attributes.keys():
            SERVER_DICT['xs_version'] = version.attributes['xs_version'].value

    # CPU info and HBA pci-id info
    hba_bus_id_list = []
    for device in test_conf.getElementsByTagName("device"):
        if 'family' in device.attributes.keys():
            SERVER_DICT['family'] = device.attributes['family'].value
        if 'stepping' in device.attributes.keys():
            SERVER_DICT['stepping'] = device.attributes['stepping'].value
        if 'model' in device.attributes.keys():
            SERVER_DICT['model'] = device.attributes['model'].value
        if 'modelname' in device.attributes.keys():
            SERVER_DICT['modelname'] = device.attributes['modelname'].value
        if 'socket_count' in device.attributes.keys():
            SERVER_DICT['sockets'] = device.attributes['socket_count'].value
        if 'PCI_description' in device.attributes.keys():
            if device.attributes['PCI_description'].value \
                    not in SERVER_DICT['nics']:
                SERVER_DICT['nics'].append(
                    device.attributes['PCI_description'].value
                    )
        if 'device' in device.attributes.keys():
            hba_bus_id_list.append(device.attributes['id'].value)

    # Chassis used info                 i
    lines = open(dmidecode_path).readlines()

    for i in range(len(lines)):
        if re.search('Chassis Information', lines[i]):
            for j in range(len(lines[i:])):
                if re.search("Type", lines[i+j]):
                    mlist = re.findall(r'(\w+):([\w\s\-]+)', lines[i+j])[0]
                    # print "%s" % list
                    SERVER_DICT['chassis'] = mlist[1]
                    break
            break
    # vendor name
    for i in range(len(lines)):
        if re.search("System Information", lines[i]):
            for j in range(len(lines[i:])):
                if re.search("Manufacturer", lines[j+i]):
                    mlist = re.findall(r'([\w\s]+):([\w\s\-\[\]\.]+)',
                                       lines[i+j])[0]
                    SERVER_DICT['system-manufacturer'] = mlist[1]
                    break
            break
    # Pdt name
    for i in range(len(lines)):
        if re.search("System Information", lines[i]):
            for j in range(len(lines[i:])):
                if re.search("Product Name", lines[j+i]):
                    mlist = re.findall(r'([\w\s]+):([\w\s\-\[\]\.^\n]+)',
                                       lines[i+j])[0]
                    SERVER_DICT['product'] = mlist[1]
                    break
            break
    # TODO ONLY IF format of logs are from ackdownload.py,
    # "machine" fetches exists
    # machine = tarfilename.split("-ack")[0]

    # lcpci -vv lines for extracting HBA data(Note: This is a workaround
    # due to existing bug of ACK not catching the right hba pci-ids)
    lines = open(lspcivv_path).readlines()

    # HBAs - Storage Controllers
    string_pattern = [
        'SCSI storage controller',
        'SATA controller',
        'RAID bus controller',
        ]
    index = []
    for i in range(len(lines)):
        for string in string_pattern:
            if re.search(string, lines[i]):
                index.append(i)
    for i in index:
        SERVER_DICT['hbas'].append(re.findall(r'.*: ([\w\s\-\(\)\/\[\]]+)',
                                              lines[i])[0].strip())

    return SERVER_DICT


def display_results(resdict, keys=None):
    """Print out results"""
    # Display rests
    keys = [
        'xs_version',
        'system-manufacturer',
        'product',
        'sockets',
        'chassis',
        'modelname',
        'family',
        'model',
        'stepping',
        'nics',
        'hbas',
    ]
    if keys is None:
        keys = resdict.keys()
    for key in keys:
        if type(SERVER_DICT[key]) == 'list':
            print "%50s :" % key, "%-50s" % pprint.pprint(SERVER_DICT[key])
        else:
            print "%50s : %s" % (key, SERVER_DICT[key])


def count_test_failures(tarfilename):
    """From a tar file, count failures"""
    testconf_path = extract_file_from_tar(tarfilename, 'test_run.conf',
                                          os.getcwd(), fullpathknown=False)
    test_conf = xml.dom.minidom.parse(open(testconf_path))
    count = 0
    for result in test_conf.getElementsByTagName('result'):
        if result.firstChild.nodeValue != 'pass':
            count = count + 1
    # fail product lists
    return (count, test_conf)


def do_parse(options):
    """do_parse function"""
    tarfilename = options.filename  # downloadACK(runjob, runmachine)
    xenrtmachine = None  # runmachine
    global SERVER_DICT
    SERVER_DICT = result_parser(tarfilename, os.getcwd())
    # display_results(dict, keys)
    display_results(SERVER_DICT)

    (count, test_conf) = count_test_failures(tarfilename)
    testconf_path = extract_file_from_tar(tarfilename, 'test_run.conf',
                                          os.getcwd(), fullpathknown=False)
    fh = open(testconf_path, 'r')
    test_conf_data = fh.read()
    fh.close()

    test_conf = xml.dom.minidom.parseString(test_conf_data)

    if options.post:
        json = xmltojson.ack_xml_to_json(test_conf_data)
        print json

    # fail product lists
    if count > 0:
        exception_list = []
        for exception in test_conf.getElementsByTagName('exception'):
            if exception.firstChild.nodeValue not in exception_list:
                exception_list.append(exception.firstChild.nodeValue)
        # maintain MACHINE_DICT only for xenRT machines
        if xenrtmachine:
            FAILED_DICT[xenrtmachine] = exception_list

            if SERVER_DICT['product'] not in MACHINE_DICT['pass']:
                if SERVER_DICT['product'] not in MACHINE_DICT['fail']:
                    MACHINE_DICT['fail'].append(SERVER_DICT['product'])
            print "*******%s tests FAILED for %s *********" % (
                count,
                xenrtmachine,
                )
        else:
            FAILED_DICT[SERVER_DICT['product']] = exception_list
    else:
        # added check here
        if xenrtmachine:  # and SERVER_DICT['product'] not in passed_list:
            # remove duplicacy
            if SERVER_DICT['product'] not in MACHINE_DICT['pass']:
                MACHINE_DICT['pass'].append(SERVER_DICT['product'])
    if xenrtmachine:
        print "#"*30
        print "NICS LISTING HERE"
        display_results(NICS_DICT)
        print "NICS LISTING OVER"
        print "#"*30
        print "HBAs HERE"
        display_results(HBAS_DICT)
        print "HBAs listing over"
        print "#"*30
        print "MY PASSED PRODUCTS"
        pprint.pprint(MACHINE_DICT['pass'])
        print "#"*30
        print "MY FAIL PRODUCTS"
        pprint.pprint(MACHINE_DICT['fail'])
        print "#"*30, "FAILED_DICT below"
    display_results(FAILED_DICT)


def get_json_from_test_run(tar_filename):
    testconf_path = extract_file_from_tar(tar_filename, 'test_run.conf',
                                          os.getcwd(), fullpathknown=False)
    fh = open(testconf_path, 'r')
    test_conf_data = fh.read()
    fh.close()

    test_conf = xml.dom.minidom.parseString(test_conf_data)
    json = xmltojson.ack_xml_to_json(test_conf_data)
    return json


def post_json_to_mongodb(json):
    client = MongoClient('mongodb://localhost:27018/')
    db = client.certification
    sub = db.submissions
    sub_id = sub.insert(json)
    return sub_id


def validate_test_run(json):
    for dev in json['devices']:
        print ""
        if dev['tag'] == 'NA':
            print dev['PCI_description']
            print "Driver: %s %s" % (dev['Driver'], dev['Driver_version'])
            print "Firmware: %s" % dev['Firmware_version']
        if dev['tag'] == 'CPU':
            print dev['modelname']
        if dev['tag'] == 'LS':
            if 'product_version' in dev:
                print dev['PCI_description']
            else:
                print dev['driver']
        if dev['tag'] == 'OP':
            if 'product_version' in dev:
                print dev['product_version']
            else:
                print dev['version']

        passed = []
        failed = []
        ignored = []

        for test in dev['tests']:
            if test['result'] == "pass":
                passed.append(test)
            elif test['result'] == "fail":
                failed.append(test)
            else:
                ignored.append(test)

        if passed:
            print "Passed:"
        for t in passed:
            print t['test_name']
        print ""

        if failed:
            print "Failed:"
        for t in failed:
            print t['test_name']

        if ignored:
            print "Ignored (skipped/other):"
        for t in ignored:
            print t['test_name']


def parse_submission(args):
    # Extract the submission
    tmpdir = tempfile.mkdtemp()
    bugtool = inspector.find_in_tarball(args.filename, 'tar.bz2')
    tar = tarfile.open(args.filename)
    t = tar.extract(bugtool, tmpdir)

    tarball_path = "%s/%s" % (tmpdir, bugtool)
    host = inspector.HostFromTarball(tarball_path)

    inspector.print_system_info(host, ['bios', 'cpu', 'nic', 'storage'])
    shutil.rmtree(tmpdir)

    json = get_json_from_test_run(args.filename)

    # Check for failures
    validate_test_run(json)

    if args.post:
        print post_json_to_mongodb(json)


def main():
    """Entry point"""
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", dest="filename", required=True,
                        help="ACK tar file")
    parser.add_argument("-p", "--post", dest="post", action="store_true")
    args = parser.parse_args()
    parse_submission(args)
