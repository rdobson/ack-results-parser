"""Entry point script for parsing specified log files"""

from argparse import ArgumentParser
from xscertparser.utils import extract_file_from_tar
import os
import re
import xml.dom.minidom
import pprint
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
    test_conf = xml.dom.minidom.parse(open(testconf_path))

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


def main():
    """Entry point"""
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", dest="filename", required=True,
                        help="ACK tar file")
    args = parser.parse_args()
    do_parse(args)
