#!/usr/bin/python

# Copyright 2015 WebEffects Network, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# system imports
import sys
import optparse
import textwrap
import time
import datetime
import os
from jinja2 import * 
# urllib2 sucks when you need to use POST and you don't know beforehand
# that you need to use POST. we use 'requests' instead so that we
# can let the modules define themselves
import requests
from requests.auth import HTTPBasicAuth
from optparse import OptionParser
import json as myjson

# vyvyan imports
from vyvyan.configure import *
from vyvyan.common import *


# our exception class
class VyvyanCLIError(Exception):
    pass


# swap a dict around
def swap_dict(odict):
    return dict([(v, k) for (k, v) in odict.iteritems()])


# if someone runs: vyv
def get_commands(cfg, module_map):
    try:
        response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+'API_userdata/metadata', auth=(cfg.api_admin_user, cfg.api_admin_pass))
        mmeta = myjson.loads(response.content)
        buf = ""
        if mmeta['status'] != 0:
            raise VyvyanCLIError("Error output:\n%s" % mmeta['msg'])
        buf += "Available commands:\n\n"
        for k in sorted(mmeta['data']['methods'].keys()):
            buf += "%s (%s) - %s" % (mmeta['data']['methods'][k]['short'], k, mmeta['data']['methods'][k]['description'])
            buf += "\n"
        buf += "\nRun \"vyv <command>\" for more information"
        return buf
    except Exception, e:
        raise VyvyanCLIError("Error: %s" % e)


# if someone runs: vyv <command>
def get_command_args(cfg, module_map):
    try:
        # create a reverse module map...for reasons
        revmodule_map = swap_dict(module_map)

        # fetch our metadata, set some vars
        response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+'API_userdata/metadata', auth=(cfg.api_admin_user, cfg.api_admin_pass))
	module = "API_userdata"
        call = sys.argv[1]
        mmeta = myjson.loads(response.content)

        # map short aliases to calls
        callmap = {}
        for ccall in mmeta['data']['methods'].keys():
            callmap[mmeta['data']['methods'][ccall]['short']] = ccall
        if call in callmap.keys():
            call = callmap[call]

        # init a buffer to hold things
        buf = ""

        # couldn't get metadata back
        if mmeta['status'] != 0:
            raise VyvyanCLIError("Error:\n%s" % mmeta['msg'])

        # call does not appear in valid methods
        if not call in mmeta['data']['methods'].keys():
            raise VyvyanCLIError("Invalid command issued: %s" % sys.argv[1])

        # no args defined, just run the thing
        if not 'args' in mmeta['data']['methods'][call]['optional_args'] and not 'args' in mmeta['data']['methods'][call]['required_args']:
            call_command(cfg, module_map)
            # stop processing
            sys.exit(0)

        # add description
        if 'description' in mmeta['data']['methods'][call]:
            buf += mmeta['data']['methods'][call]['description']
            buf += "\n\n"

        # add required args to usage output
        if 'args' in mmeta['data']['methods'][call]['required_args']:
            buf += "Required arguments:\n"
            for k in sorted(mmeta['data']['methods'][call]['required_args']['args'].keys()):
                buf += "--%s (-%s): %s" % (k, mmeta['data']['methods'][call]['required_args']['args'][k]['ol'], mmeta['data']['methods'][call]['required_args']['args'][k]['desc'])
                buf += "\n"

        # add optional args to usage output
        if 'args' in mmeta['data']['methods'][call]['optional_args']:
            buf += "\nOptional arguments, supply a minimum of %s and a maximum of %s of the following:\n" % (mmeta['data']['methods'][call]['optional_args']['min'], mmeta['data']['methods'][call]['optional_args']['max'])
            for k in sorted(mmeta['data']['methods'][call]['optional_args']['args'].keys()):
                buf += "--%s (-%s): %s" % (k, mmeta['data']['methods'][call]['optional_args']['args'][k]['ol'], mmeta['data']['methods'][call]['optional_args']['args'][k]['desc'])
                buf += "\n"

        # once we're done constructing things, return data
        return buf

    # explode violently
    except Exception, e:
        raise VyvyanCLIError(e)


# if someone runs: vyv <command> --option1=bleh -o2 foo
def call_command(cfg, module_map):
    try:
        revmodule_map = swap_dict(module_map)
        module = "API_userdata"
        call = sys.argv[1]
        buf = "" # our argument buffer for urlencoding
        if module in revmodule_map.keys():
            module = revmodule_map[module] 
        elif 'API_'+module in module_map.keys():
            module = 'API_'+module 
        elif module in module_map.keys():
            pass
        else:
            log.debug("Malformed module: %s" % module)
            raise VyvyanCLIError("Malformed module: %s" % module)
        response = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+module+'/metadata', auth=(cfg.api_admin_user, cfg.api_admin_pass))
        mmeta = myjson.loads(response.content)
        if mmeta['status'] != 0:
            raise VyvyanCLIError("Error output:\n%s" % mmeta['msg'])

        # map short aliases to calls
        callmap = {}
        for ccall in mmeta['data']['methods'].keys():
            callmap[mmeta['data']['methods'][ccall]['short']] = ccall
        if call in callmap.keys():
            call = callmap[call]

        # set up our command line options through optparse. will
        # change this to argparse if we upgrade past python 2.7
        if 'description' in  mmeta['data']['methods'][call]:
            usage = "Usage: vyv %s [options]\n\n%s" % (call, mmeta['data']['methods'][call]['description'])
        else:
            usage = "Usage: vyv %s [options]" % (call)
        parser = OptionParser(usage=usage)
        arglist = {}
        if 'args' in mmeta['data']['methods'][call]['required_args']:
            for k in sorted(mmeta['data']['methods'][call]['required_args']['args'].keys()):
                if mmeta['data']['methods'][call]['required_args']['args'][k]['vartype'] != "bool":
                    parser.add_option('-'+mmeta['data']['methods'][call]['required_args']['args'][k]['ol'],\
                                      '--'+k, help=mmeta['data']['methods'][call]['required_args']['args'][k]['desc'])
                    arglist[k] = mmeta['data']['methods'][call]['required_args']['args'][k]['vartype']
                else:
                    parser.add_option('-'+mmeta['data']['methods'][call]['required_args']['args'][k]['ol'],\
                                      '--'+k, help=mmeta['data']['methods'][call]['required_args']['args'][k]['desc'],\
                                      action="store_true")
                    arglist[k] = mmeta['data']['methods'][call]['required_args']['args'][k]['vartype']
        if 'args' in mmeta['data']['methods'][call]['optional_args']:
            for k in sorted(mmeta['data']['methods'][call]['optional_args']['args'].keys()):
                if mmeta['data']['methods'][call]['optional_args']['args'][k]['vartype'] != "bool":
                    parser.add_option('-'+mmeta['data']['methods'][call]['optional_args']['args'][k]['ol'],\
                                      '--'+k, help=mmeta['data']['methods'][call]['optional_args']['args'][k]['desc'])
                    arglist[k] = mmeta['data']['methods'][call]['optional_args']['args'][k]['vartype']
                else:
                    parser.add_option('-'+mmeta['data']['methods'][call]['optional_args']['args'][k]['ol'],\
                                      '--'+k, help=mmeta['data']['methods'][call]['optional_args']['args'][k]['desc'],\
                                      action="store_true")
                    arglist[k] = mmeta['data']['methods'][call]['optional_args']['args'][k]['vartype']

        # do we have any required arguments?
        if 'args' in mmeta['data']['methods'][call]['required_args'].keys():
            required_args = mmeta['data']['methods'][call]['required_args']['args'].keys()
        else:
            required_args = [] 

        # parse our options and build a urlencode string to pass
        # over to the API service
        # 
        # TODO: need to use POST data for PII (usernames, passwords)
        #       will need to figure out a better way to do this 
        #
        # spaces in URLs make vyvyan sad, so replace with %20
        (options, args) = parser.parse_args(sys.argv[2:])
        files = {}
        for k in arglist.keys():
            a = vars(options)[k]

            # if the variable type expected by vyv_daemon is "file", we
            # need to operate slightly differently
            if a and k and arglist[k] == "file":
                files[k] = open(a)

            # if the variable type isn't "file", jam the query onto
            # the end of our query string buffer
            elif a and k:
                if buf:
                    buf += '&'
                if a != True:
                    buf += k+'='+str(a.replace(' ', '%20'))
                else:
                    buf += k

            # if options[k] is empty and is a required option, explode
            elif not a and k in required_args: 
                raise VyvyanCLIError(get_command_args(cfg, module_map))

            # this just means's it's an unpopulated optional argument
            # TODO: do we need this? -dk
            else:
                pass

        # make the call out to our API daemon, expect JSON back
        if mmeta['data']['methods'][call]['rest_type'] == 'GET':
            callresponse = requests.get('http://'+cfg.api_server+':'+cfg.api_port+'/'+module+'/'+call+'?'+buf, auth=(cfg.api_admin_user, cfg.api_admin_pass))
        elif mmeta['data']['methods'][call]['rest_type'] == 'POST':
            callresponse = requests.post('http://'+cfg.api_server+':'+cfg.api_port+'/'+module+'/'+call+'?'+buf, files=files, auth=(cfg.api_admin_user, cfg.api_admin_pass))
        elif mmeta['data']['methods'][call]['rest_type'] == 'DELETE':
            callresponse = requests.delete('http://'+cfg.api_server+':'+cfg.api_port+'/'+module+'/'+call+'?'+buf, auth=(cfg.api_admin_user, cfg.api_admin_pass))
        elif mmeta['data']['methods'][call]['rest_type'] == 'PUT':
            callresponse = requests.put('http://'+cfg.api_server+':'+cfg.api_port+'/'+module+'/'+call+'?'+buf, files=files, auth=(cfg.api_admin_user, cfg.api_admin_pass))

        # load the JSON response into the equivalent python variable type
        responsedata = myjson.loads(callresponse.content)
        if responsedata['status'] != 0:
            raise VyvyanCLIError("Error output:\n%s" % responsedata['msg'])

        # close any open files 
        if files:
            for k in files.keys():
                files[k].close()

        # if we get just a unicode string back, it's a status
        # message...print it. otherwise, we got back a dict or list
        # or something similar, fire it off at the template engine
        # if it blows up, dump the error and the response we got
        # from vyvyan_daemon.py
        if isinstance(responsedata['data'], unicode):
            print responsedata['data']
        else:
            try:
                print_responsedata(responsedata, mmeta, call)
            except Exception, e:
                print "Error: %s\n\n" % e
                print responsedata

    # explode violently
    except Exception, e:
        raise VyvyanCLIError(e)


# prints out response data, according to a jinja2 template defined in
# the module
def print_responsedata(responsedata, mmeta, call):
    """
    prints out response data according to a jinja2 template
    defined in the module directory

    this frontend tries to use "vyvyan/<modulename>/template.cmdln.<call>"
    for its template file. if it doesn't find a call-specific template, it will
    attempt to use "vyvyan/<modulename>/template.cmdln" as a default. 
    if all else fails, just spit out the response data.
    """
    if responsedata['msg']:
        # if we got back something in the "msg" field, it means an error occurred
        # the REST daemon may populate something in the data field to assist
        # troubleshooting, but the CLI isn't concerned with that. just let the 
        # user know what the error message was 
        print responsedata['msg']
    elif responsedata['data']:
        module = 'API_userdata'
        tfile = "template.cmdln.%s" % call 
        #env = Environment(loader=FileSystemLoader('vyvyan/'+module))
        try:
            # try to load up a template called template.cmdln.<call>
            # this allows us to format output specifically to each call
            if mmeta['data']['templates'][tfile]:
                template = mmeta['data']['templates'][tfile] 
                print Environment().from_string(template).render(r=responsedata)
            else:
                # no template at all! just spit the data out
                print responsedata
        except Exception, e:
            raise VyvyanCLIError(e)
    else:
        # no data, no msg, no error. most likely an API command that returned
        # an empty string or set. just print a blank line to indicate blankness
        # in the response 
        print "" 
        sys.exit(1)

# main execution block
if __name__ == "__main__":
    # the global CLI config. useful everywhere
    cfg = VyvyanConfigureCli('vyvyan_cli.yaml')
    cfg.load_config()
    log = VyvyanLogger(cfg)

    # prevent root from running vyv
    if sys.stdin.isatty():
        if os.geteuid() == 0:
            raise VyvyanCLIError("Please do not run vyv as root. Your effective uid: %s" % os.geteuid())

    # write out the command line we were called with to an audit log
    try:
        alog = open(cfg.logdir+'/'+cfg.audit_log_file, 'a')
        ltz = time.tzname[time.daylight]
        tformat = "%Y-%m-%d %H:%M:%S"
        timestamp = datetime.datetime.now()
        if sys.stdin.isatty():
            username = os.getlogin()
        else:
            username = "nottyUID=" + str(os.geteuid())
        command_run = ' '.join(sys.argv)
        buffer = "%s %s: %s: %s\n" % (ltz, timestamp.strftime(tformat), username, command_run)
        alog.write(buffer)
        alog.close()
    except Exception, e:
        print "Exception: " + str(e)
        print "Problem writing to audit log file!"
        print "Audit file configured as: " + cfg.audit_log_file
        print "logline dump:"
        print "%s %s: %s: %s" % (ltz, timestamp, username, command_run)
        alog.close()

    # doin stuff
    try:
        # if it didn't blow up, populate the module list
        module_map = {}
        response = requests.get('http://'+cfg.api_server+":"+cfg.api_port+'/API_userdata/metadata', auth=(cfg.api_admin_user, cfg.api_admin_pass))
        response_dict = myjson.loads(response.content)
        module_map['API_userdata'] = response_dict['data']['config']['shortname']
        # a reverse module map, useful in constructing our cmdln
        revmodule_map = swap_dict(module_map)

        # command line-y stuff. the order of the if statements is very
        # important. please be careful if you have to move things
        #
        # user ran: vyv
        if len(sys.argv) < 2:
            log.debug("get_commands called()")
            print get_commands(cfg, module_map)

        # user ran: vyv <command> 
        #elif len(sys.argv) == 2 and (sys.argv[1] in module_map['ud'].keys() or sys.argv[1] in module_map['ud'].values()):
        elif len(sys.argv) == 2:
            log.debug("get_command_args called()")
            print get_command_args(cfg, module_map)

        # user ran: vyv <invalid command>
        #elif len(sys.argv) == 2 and (sys.argv[1] not in module_map['API_userdata'].values() and sys.argv[1] not in module_map['API_userdata'].keys() and 'API_'+sys.argv[1] not in module_map.keys()):
        #    raise VyvyanCLIError("Requested module does not exist: %s" % "API_"+sys.argv[1])

        # user ran: vyv <valid module>/<command> --valid=args -a
        elif len(sys.argv) >= 3:
            log.debug("call_command called()")
            call_command(cfg, module_map)

        # user ran some real ugly crap.
        else:
            raise VyvyanCLIError("bad command line:\n%s" % " ".join(sys.argv))

    except IOError, e:
        print "Missing config file: vyvyan_cli.yaml"
        print "ERROR: %s" % e
        log.debug("Missing config file: vyvyan_cli.yaml")
        log.debug("ERROR: %s" % e)
        sys.exit(1)
    except VyvyanCLIError as e:
        print "Error in command line. \n\n%s" % e
        log.debug("Error in command line. \n\n%s" % e)
        sys.exit(1)
    except Exception, e:
        print "Error in __main__: %s" % e
        log.debug("Error in __main__: %s" % e)
        sys.exit(1)
