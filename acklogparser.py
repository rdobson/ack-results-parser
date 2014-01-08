#!/usr/bin/python
nics_dict ={}
hbas_dict ={}
machine_dict={"pass":[],"fail":[]} #seprates server Products PASS/FAIL
failed_dict={}
dict = {'xs_version':u'None','system-manufacturer':'None','sockets':'None','product':'None',"chassis":'None','modelname':'None','family':'None','model':'None','stepping':'None','nics':[], 'hbas':[]}

from argparse import ArgumentParser
import tarfile,os,re,xml.dom.minidom,pprint
#import models

def extract_file_from_tar(tarfilename, filename, dest):
    tf = tarfile.open(tarfilename) #tarfilename is path of tar
    path = filter(lambda x:os.path.basename(x) == filename, tf.getnames())
    if not len(path):
        path = filter(lambda x:re.search(filename, x),tf.getnames())        
    map(lambda x:tf.extract(x, path=dest), path)
    return os.path.join(dest,path[0])

def result_parser(tarfilename, logsubdir):
    bugtools_path = extract_file_from_tar(tarfilename = tarfilename, filename = "bug-report", dest = logsubdir)
    testconf_path = extract_file_from_tar (tarfilename, 'test_run.conf', logsubdir)
    dmidecode_path = extract_file_from_tar (os.path.join(logsubdir, bugtools_path), 'dmidecode.out', logsubdir)
    #xapi_db_path = extract_file_from_tar (os.path.join(logsubdir, bugtools_path), 'xapi-db.xml', logsubdir)
    lspcivv_path = extract_file_from_tar (os.path.join(logsubdir, bugtools_path), 'lspci-vv.out', logsubdir)
    #get NIC Names, CPU
    test_conf = xml.dom.minidom.parse(open(testconf_path))
    
    #XS-version
    for version in test_conf.getElementsByTagName("global_config"):
        if version._attrs.has_key('xs_version'):
            dict['xs_version'] = version._attrs['xs_version'].nodeValue

    #CPU info and HBA pci-id info
    hbaBusIdList=[]
    for device in test_conf.getElementsByTagName("device"):
        if device._attrs.has_key('family'):
            dict['family'] = device._attrs['family'].nodeValue
        if device._attrs.has_key('stepping'):
            dict['stepping'] = device._attrs['stepping'].nodeValue
        if device._attrs.has_key('model'):
            dict['model']= device._attrs['model'].nodeValue
        if device._attrs.has_key('modelname'):
            dict['modelname']= device._attrs['modelname'].nodeValue
        if device._attrs.has_key('socket_count'):
            dict['sockets'] = device._attrs['socket_count'].nodeValue
        if device._attrs.has_key('PCI_description'):
            if device._attrs['PCI_description'].nodeValue not in dict['nics']:
                dict['nics'].append(device._attrs['PCI_description'].nodeValue)
        if device._attrs.has_key('device'):
            hbaBusIdList.append(device._attrs['id'].nodeValue)
            
            
    #Chassis used info                 i
    lines = open(dmidecode_path).readlines()
    
    for i in range(len(lines)):
        if re.search('Chassis Information',lines[i]):
            for j in range(len(lines[i:])):
                if re.search("Type", lines[i+j]):
                    list = re.findall('(\w+):([\w\s\-]+)',lines[i+j])[0]
                    #print "%s" % list
                    dict['chassis']= list[1]
                    break          
            break       
    #vendor name
    for i in range(len(lines)):
        if re.search("System Information", lines[i]):
            for j in range(len(lines[i:])):
                if re.search("Manufacturer", lines[j+i]):
                    list = re.findall('([\w\s]+):([\w\s\-\[\]\.]+)',lines[i+j])[0]
                    dict['system-manufacturer'] = list[1]
                    break
            break
    #Pdt name                
    for i in range(len(lines)):    
        if re.search("System Information", lines[i]):
            for j in range(len(lines[i:])):
                if re.search("Product Name", lines[j+i]):
                    list = re.findall('([\w\s]+):([\w\s\-\[\]\.^\n]+)',lines[i+j])[0]
                    dict['product']= list[1]
                    break
            break     
    #TODO ONLY IF format of logs are from ackdownload.py, "machine" fetches exists
    machine = tarfilename.split("-ack")[0]    
    
    #lcpci -vv lines for extracting HBA data(Note: This is a workaround due to existing bug of ACK not catching the right hba pci-ids)
    lines = open(lspcivv_path).readlines()
    
    #HBAs - Storage Controllers
    string_pattern = ['SCSI storage controller', 'SATA controller', 'RAID bus controller']
    index = []
    for i in range(len(lines)):
        for string in string_pattern:
            if re.search(string, lines[i]):
                index.append(i)
    for i in index:
        dict['hbas'].append(re.findall('.*: ([\w\s\-\(\)\/\[\]]+)',lines[i])[0].strip())
    
    return dict

def display_results(dict, keys = None):
    #Display rests
    keys = ['xs_version','system-manufacturer','product','sockets','chassis','modelname','family','model','stepping','nics','hbas']
    if keys is None:
        keys = dict.keys()
    for key in keys:
        if type(dict[key]) =='list':
            print "%50s :" % key, "%-50s" % pprint.pprint(dict[key])
        else:
            print "%50s : %s" % (key, dict[key])

def countTestFailures(tarfilename):
    testconf_path = extract_file_from_tar(tarfilename, 'test_run.conf', os.getcwd())
    test_conf = xml.dom.minidom.parse(open(testconf_path))
    count = 0
    for result in test_conf.getElementsByTagName('result'):
        if result.firstChild.nodeValue != 'pass':
            count = count + 1
    #fail product lists
    return (count,test_conf)       
    

def main(options):
    tarfilename = options.filename #downloadACK(runjob, runmachine)
    xenrtmachine=None #runmachine
    dict = result_parser(tarfilename,os.getcwd())
    #keys = ['system-manufacturer','product','chassis','sockets','family','model','stepping','nics', 'hbas']
    #print dict    
    #display_results(dict, keys)
    display_results(dict)
    
    (count, test_conf) = countTestFailures(tarfilename)
    testconf_path = extract_file_from_tar(tarfilename, 'test_run.conf', os.getcwd())
    test_conf = xml.dom.minidom.parse(open(testconf_path))

    #fail product lists
    if count > 0 :
        exception_list=[]
        for exception in test_conf.getElementsByTagName('exception'):
            if exception.firstChild.nodeValue not in exception_list:
                exception_list.append(exception.firstChild.nodeValue)
        #maintain machine_dict only for xenRT machines
        if xenrtmachine:
            failed_dict[xenrtmachine]= exception_list

            if dict['product'] not in machine_dict['pass']:
                if dict['product'] not in machine_dict['fail']:    
                    machine_dict['fail'].append(dict['product'])
            print ("*******%s tests FAILED for %s *********" % (count,runmachine))
        else:
            failed_dict[dict['product']] = exception_list
    else:
        if xenrtmachine and dict['product'] not in passed_list : #added check here
            if dict['product'] not in machine_dict['pass']: #remove duplicacy 
                machine_dict['pass'].append(dict['product'])
    if xenrtmachine:
        print ("#"*30)
        print ("NICS LISTING HERE")
        display_results(nics_dict)
        print ("NICS LISTING OVER")
        print ("#"*30)
        print ("HBAs HERE")
        display_results(hbas_dict)
        print ("HBAs listing over")
        print ("#"*30)
        print ("MY PASSED PRODUCTS")
        pprint.pprint(machine_dict['pass'])
        print ("#"*30)
        print ("MY FAIL PRODUCTS")
        pprint.pprint(machine_dict['fail'])
        print ("#"*30,"failed_dict below")
    display_results(failed_dict)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", dest="filename",required=True,help="ACK tar file")
    args = parser.parse_args()
    main(args)
