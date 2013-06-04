#!/usr/bin/python

from argparse import ArgumentParser
import tarfile
import models

def extract_file_from_tar(tarfilename, filename, dest):
    print "About to open '%s'" % tarfilename
    tar = tarfile.open(tarfilename)
    tar.extract(filename, dest)
    tar.close()
    return "%s/%s" % (dest, filename)


def main(options):
    xml_file = extract_file_from_tar(options.filename, \
                          'opt/xensource/packages/files/auto-cert-kit/' \
                          'test_run.conf', '/tmp/') 

    ack_run = models.parse_xml(xml_file)
    p, f, w = ack_run.get_status()
    
    if f !=0 and w != 0:
        print "Fail"
    elif p > 0:
        print "Pass"
    else:
        raise Exception("Error: %d, %d, %d" % (p, f, w))
            
    

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-f", "--file", dest="filename",
                        required=True,
                        help="ACK tar file")

    args = parser.parse_args()
    main(args)
