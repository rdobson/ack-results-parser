import os,sys
import acklogparser
from argparse import ArgumentParser
"""
After a XS releases, we need to run ack kit on all servers in house and store the logs based
on the Products that we certify for our future references in sharefile. 
This file will help with that. 
Input requires a ack-submissions*.tar.gz
All logs that is present in logsubdir, gets copied to their respective Product names (eg. Dell PowerEdge 620)
Once this seperation is done, we can easily upload in the HCL sharefile account. 
"""
def main(options):
    logsubdir = options.logsubdir
    list = os.popen ("ls %s | grep tar.gz" % logsubdir).read().strip().split()
    for ls in list:
        tarfilename = os.path.join(logsubdir, ls)
        dict = acklogparser.result_parser(tarfilename , logsubdir)
        folderName = dict ['system-manufacturer'].strip() + " " +dict ['product'].strip()
        count = acklogparser.countTestFailures(tarfilename)
        if count == 0:
            if not os.path.isdir('Products'):
                os.popen ("mkdir Products")
            if not os.path.isdir("Products/'%s'" % folderName):
                os.popen ("mkdir Products/'%s'" % folderName)
            os.popen ("cp %s//%s Products//'%s'" % (logsubdir, ls, folderName))
    print "Passed Logs moved."
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--path", dest="logsubdir",required=True,help="Folder from where the logs are to be dragged")
    args = parser.parse_args()
    main(args)



