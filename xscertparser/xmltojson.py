#!/usr/bin/env python

from pymongo import MongoClient
import xml.dom.minidom
import json


def get_attributes(xml_node):
    """ When given an XML node, return a dictionary object
    with all of the key/values as specified in the XML"""
    rec = {}
    if not xml_node.hasAttributes():
        return rec

    for i in range(0, xml_node.attributes.length):
        attr_node = xml_node.attributes.item(i)
        rec[attr_node.name] = attr_node.value

    return rec

def get_child_elems(xml_node):
    return [node for node in xml_node.childNodes
             if node.nodeType == node.ELEMENT_NODE]

def get_element_by_tag_name(node, tag):
    nds = node.getElementsByTagName(tag)
    assert(len(nds) == 1)
    return nds[0]

def get_text(nodelist):
    rec = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def get_test_method_record(node):
    rec = {}
    rec['name'] = get_attributes(node)['name']
    res_n = get_element_by_tag_name(node, 'result')
    for tag in get_child_elems(node):
        if tag.firstChild:
            rec[tag.tagName] = tag.firstChild.nodeValue
        elif get_attributes(tag):
            rec[tag.tagName] = get_attributes(tag)


    return rec

def get_test_class_record(node):
    #rec = {}
    #config = get_attributes(node)
    #for k, v in config.iteritems():
    #    rec[k] = v

    meths = []
    for method_node in get_child_elems(node):
        method_rec = get_test_method_record(method_node)
        meths.append(method_rec)

    #rec['methods'] = meths
    return meths

def get_device_test_record(node):
    rec = {}

    attrs = get_attributes(node)
    for k, v in attrs.iteritems():
        rec[k] = v

    cert_tests = get_child_elems(node)
    assert len(cert_tests) == 1

    tcs = []
    for test_class_node in get_child_elems(cert_tests[0]):
        test_class_rec = get_test_class_record(test_class_node)
        tcs = tcs + test_class_rec

    rec['tests'] = tcs

    return rec


def ack_xml_to_json(xml_str):
    rec = {}
    dom = xml.dom.minidom.parseString(xml_str)

    #<automated_certification_kit>
    kit_params = dom.getElementsByTagName('automated_certification_kit')[0]
    rec['kit'] = get_attributes(kit_params)

    #<globa_config>
    global_config = dom.getElementsByTagName('global_config')[0]
    rec['global_config'] = get_attributes(global_config)

    #<devices>
    devices = dom.getElementsByTagName('device')

    devs = []
    for device in devices:
        dev_rec = get_device_test_record(device)
        devs.append(dev_rec)

    rec['devices'] = devs

    return rec


def post_json_to_mongodb(uri, json):
    client = MongoClient(uri)
    db = client.certification
    sub = db.submissions
    sub_id = sub.insert(json)
    return sub_id

#j = ack_xml_to_json(xml_data)

#print j
#print json.dumps(j, indent=4, separators=(',',':'))


#client = MongoClient('mongodb://localhost:27017/')

#db = client.certification
#sub = db.submissions

#sub_id = sub.insert(j)

#print sub_id
