# Copyright 2015 WebEffects, Inc.
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
"""
    vyvyan.API_userdata

    Package for interacting with user and group data in vyvyan
"""

from sqlalchemy import or_, desc, MetaData
import sys
import passlib.hash 
import vyvyan
from vyvyan.vyvyan_models import *
from vyvyan.common import *
from vyvyan.validate import *

class UserdataError(Exception):
    pass      

class API_userdata:

    def __init__(self, cfg):
        self.cfg = cfg
        self.version = 1
        self.namespace = 'API_userdata'
        self.metadata = {
            'config': {
                'description': 'allows for the creation and manipulation of users and groups within vyvyan',
                'shortname': 'ud',
                'module_dependencies': {
                    'common': 1,
                },
            },
            'methods': {
                'list_users': {
                    'description': 'list users',
                    'short': 'lsu',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'all': {
                                'vartype': 'bool',
                                'desc': 'all domains',
                                'ol': 'a',
                            },
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain of the user',
                                'ol': 'd',
                            },
                        },
                    },
                    'return': {
                        'domain': [
                            'username',
                            'username',
                        ],
                        'domain': [
                            'username',
                            'username',
                        ],
                    },
                },
                'list_groups': {
                    'description': 'list groups',
                    'short': 'lsg',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 1,
                        'args': {
                            'all': {
                                'vartype': 'bool',
                                'desc': 'all domains',
                                'ol': 'a',
                            },
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain of the user',
                                'ol': 'd',
                            },
                        },
                    },
                    'return': {
                        'domain': [
                            'groupname',
                            'groupname',
                        ],
                        'domain': [
                            'groupname',
                            'groupname',
                        ],
                    },
                },
                'list_domains': {
                    'description': 'list domains (does not take arguments)',
                    'short': 'lsd',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                    },
                    'optional_args': {
                    },
                    'return': [
                        'domain',
                        'domain',
                    ],
                },
                'udisplay': {
                    'description': 'display a user\'s info',
                    'short': 'ud',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                        'args': {
                            'username': {
                                'vartype': 'str',
                                'desc': 'username of the user',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 1,
                        'args': {
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain of the user',
                                'ol': 'd',
                            },
                        },
                    },
                    'return': [
                        {
                            'user': 'ORMobject',
                            'groups': [
                                'group ORMobject',
                                'group ORMobject',
                            ],
                        },
                    ],
                },
                'uadd': {
                    'description': 'create a user entry in the user table',
                    'short': 'ua',
                    'rest_type': 'POST',
                    'admin_only': True,
                    'required_args': {
                        'args': {
                            'username': {
                                'vartype': 'str',
                                'desc': 'username of the user to add to the database',
                                'ol': 'u',
                            },
                            'password': {
                                'vartype': 'str',
                                'desc': 'user\'s password',
                                'ol': 'p',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 9,
                        'args': {
                            'domain': {
                                'vartype': 'str',
                                'desc': "LDAP domain to add user under (default: %s)" % cfg.default_domain,
                                'ol': 'd',
                            },
                            'first_name': {
                                'vartype': 'str',
                                'desc': 'user\'s first name (default John)',
                                'ol': 'f',
                            },
                            'last_name': {
                                'vartype': 'str',
                                'desc': 'user\'s last name (default Doe)',
                                'ol': 'l',
                            },
                            'ssh_key': {
                                'vartype': 'file',
                                'desc': 'a file containing the user\'s ssh key(s)',
                                'ol': 'k',
                            },
                            'shell': {
                                'vartype': 'str',
                                'desc': "user's shell (default: %s)" % cfg.shell,
                                'ol': 's',
                            },
                            'email_address': {
                                'vartype': 'str',
                                'desc': "user's email address (default: username@%s)" % cfg.default_domain,
                                'ol': 'e',
                            },
                            'home_dir': {
                                'vartype': 'str',
                                'desc': "user's home directory (default: %s/username)" % cfg.hdir,
                                'ol': 'o',
                            },
                            'user_type': {
                                'vartype': 'str',
                                'desc': "user type, pick one of: %s (default: %s)" % (" ".join(cfg.user_types), cfg.def_user_type),
                                'ol': 't',
                            },
                            'uid': {
                                'vartype': 'str',
                                'desc': "user's uid (default will pick the next available uid)",
                                'ol': 'i',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'uremove': {
                    'description': 'delete a user entry from the users table',
                    'short': 'urm',
                    'rest_type': 'DELETE',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'username': {
                                'vartype': 'str',
                                'desc': 'username of the user to delete from the database',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 1,
                        'args': {
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain of the user to delete',
                                'ol': 'd',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'umodify': {
                    'description': 'modify an existing user entry',
                    'short': 'um',
                    'rest_type': 'PUT',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'username': {
                                'vartype': 'str',
                                'desc': 'username of the user to modify',
                                'ol': 'u',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 10,
                        'args': {
                            'password': {
                                'vartype': 'str',
                                'desc': 'user\'s password',
                                'ol': 'p',
                            },
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain of the user to modify',
                                'ol': 'd',
                            },
                            'first_name': {
                                'vartype': 'str',
                                'desc': 'user\'s first name (default John)',
                                'ol': 'f',
                            },
                            'last_name': {
                                'vartype': 'str',
                                'desc': 'user\'s last name (default Doe)',
                                'ol': 'l',
                            },
                            'ssh_key': {
                                'vartype': 'file',
                                'desc': 'a file containing the user\'s ssh key(s)',
                                'ol': 'k',
                            },
                            'shell': {
                                'vartype': 'str',
                                'desc': "user's shell (default: %s)" % cfg.shell,
                                'ol': 's',
                            },
                            'email_address': {
                                'vartype': 'str',
                                'desc': "user's email address (default: username@%s)" % cfg.default_domain,
                                'ol': 'e',
                            },
                            'home_dir': {
                                'vartype': 'str',
                                'desc': "user's home directory (default: %s/username)" % cfg.hdir,
                                'ol': 'o',
                            },
                            'user_type': {
                                'vartype': 'str',
                                'desc': "user type, pick one of: %s (default: %s)" % (" ".join(cfg.user_types), cfg.def_user_type),
                                'ol': 't',
                            },
                            'uid': {
                                'vartype': 'str',
                                'desc': "user's uid (default will pick the next available uid)",
                                'ol': 'i',
                            },
                            'active': {
                                'vartype': 'str',
                                'desc': "true/false (or t/f), activate/deactivate. deactivate the user to disable without removing the user info from vyvyan",
                                'ol': 'a',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'uclone': {
                    'description': 'clone a user from one domain to another',
                    'short': 'uc',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'username': {
                                'vartype': 'str',
                                'desc': 'username of the user to clone from',
                               'ol': 'u',
                            },
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain to clone the user from',
                                'ol': 'd',
                            },
                            'newdomain': {
                                'vartype': 'str',
                                'desc': 'domain to clone the user into',
                                'ol': 'n',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'gdisplay': {
                    'description': 'display a group\'s info',
                    'short': 'gd',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                        'args': {
                            'groupname': {
                                'vartype': 'str',
                                'desc': 'name of the group',
                                'ol': 'g',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 1,
                        'args': {
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain of the group',
                                'ol': 'd',
                            },
                        },
                    },
                    'return': {
                        'groupname': 'ORMobject',
                        'users': [
                            'user ORMobject',
                            'user ORMobject',
                        ],
                    },
                },
                'gadd': {
                    'description': 'create a group entry in the group table',
                    'short': 'ga',
                    'rest_type': 'POST',
                    'admin_only': True,
                    'required_args': {
                        'args': {
                            'groupname': {
                                'vartype': 'str',
                                'desc': 'group of the group to add to the database',
                                'ol': 'g',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 4,
                        'args': {
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain of the group',
                                'ol': 'd',
                            },
                            'description': {
                                'vartype': 'str',
                                'desc': 'a description of the group',
                                'ol': 'e',
                            },
                            'sudo_cmds': {
                                'vartype': 'str',
                                'desc': 'comma-delimited commands users of this group are allowd to run as root',
                                'ol': 's',
                            },
                            'gid': {
                                'vartype': 'str',
                                'desc': 'group id number to assign to the group',
                                'ol': 'i',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'gremove': {
                    'description': 'delete a group entry from the groups table',
                    'short': 'grm',
                    'rest_type': 'DELETE',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'groupname': {
                                'vartype': 'str',
                                'desc': 'groupname of the group to delete from the database',
                                'ol': 'g',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 1,
                        'args': {
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain to delete the group from',
                                'ol': 'd',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'gmodify': {
                    'description': 'modify an existing group entry',
                    'short': 'gm',
                    'rest_type': 'PUT',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'groupname': {
                                'vartype': 'str',
                                'desc': 'groupname of the group to modify',
                                'ol': 'g',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 1,
                        'max': 4,
                        'args': {
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain to delete the group from',
                                'ol': 'd',
                            },
                            'description': {
                                'vartype': 'str',
                                'desc': 'a description of the group',
                                'ol': 'd',
                            },
                            'sudo_cmds': {
                                'vartype': 'str',
                                'desc': 'comma-delimited commands users of this group are allowd to run as root',
                                'ol': 's',
                            },
                            'gid': {
                                'vartype': 'str',
                                'desc': 'group id number to assign to the group',
                                'ol': 'i',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'gclone': {
                    'description': 'clone a group from one domain to another',
                    'short': 'gc',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'groupname': {
                                'vartype': 'str',
                                'desc': 'groupname of the group to clone from',
                                'ol': 'g',
                            },
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain to clone from',
                                'ol': 'd',
                            },
                            'newdomain': {
                                'vartype': 'str',
                                'desc': 'new domain to clone the group into',
                                'ol': 'n',
                            },
                        },
                    },
                    'optional_args': {
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'utog': {
                    'description': 'map a username to groupname in the same domain',
                    'short': 'ut',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'username': {
                                'vartype': 'str',
                                'desc': 'username of the user to map',
                               'ol': 'u',
                            },
                            'groupname': {
                                'vartype': 'str',
                                'desc': 'groupname to map the user to',
                                'ol': 'g',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 1,
                        'args': {
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain within which to map',
                               'ol': 'd',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
                'urmg': {
                    'description': 'remove a username from a group in the same domain',
                    'short': 'ur',
                    'rest_type': 'POST',
                    'admin_only': True, 
                    'required_args': {
                        'args': {
                            'username': {
                                'vartype': 'str',
                                'desc': 'username of the user to unmap',
                               'ol': 'u',
                            },
                            'groupname': {
                                'vartype': 'str',
                                'desc': 'groupname to remove the user from',
                                'ol': 'g',
                            },
                        },
                    },
                    'optional_args': {
                        'min': 0,
                        'max': 1,
                        'args': {
                            'domain': {
                                'vartype': 'str',
                                'desc': 'domain within which to unmap',
                               'ol': 'd',
                            },
                        },
                    },
                    'return': {
                        'string': 'success',
                    },
                },
            },
        }



    #############################
    # listing methods           #
    #############################

    def list_users(self, query):
        """
        [description]
        lists all users

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns a dict of lists of users per domain
        """
        try:
            self.cfg.log.debug(query.keys())
            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'list_users')

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/list_users: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/list_users: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # if the user specifies a domain, restrict output.
            # otherwise return userdata for all domains
            if 'domain' not in query.keys() or not query['domain']:
                domain = None
            else:
                domain = query['domain']

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'list_users')

            # iterate through all domains and spit out some users
            buf = {} 
            self.cfg.log.debug("API_userdata/list_users: querying for all users")
            if domain:
                usertable = self.cfg.dbsess.query(Users).\
                filter(Users.domain==domain).all()
            else:
                usertable = self.cfg.dbsess.query(Users).all()
            for u in usertable:
                if u.domain not in buf.keys():
                  buf[u.domain] = []
            for u in usertable:
                if u.active:
                    act = "active"
                else:
                    act = "inactive"
                buf[u.domain].append("%s uid:%s %s" % (u.username, u.uid, act))

            # if the user specified a domain but it's empty
            if buf == {} and domain:
                self.cfg.log.debug("API_userdata/list_users: no users in domain %s" % domain)
                raise UserdataError("API_userdata/list_users: no users in domain %s" % domain)
            elif buf == {}:
                self.cfg.log.debug("API_userdata/list_users: no users found")
                raise UserdataError("API_userdata/list_users: no users found")

            # return our listing
            self.cfg.log.debug(buf)
            return buf

        except Exception, e:
            self.cfg.log.debug("API_userdata/list_users: query failed for users. Error: %s" % e)
            raise UserdataError("API_userdata/list_users: query failed for groups. Error: %s" % e)


    def list_groups(self, query):
        """
        [description]
        lists all groups

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns a dict of lists of groups per domain
        """
        try:
            self.cfg.log.debug(query.keys())
            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'list_groups')

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/list_groups: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/list_groups: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # if the user specifies a domain, restrict output.
            # otherwise return userdata for all domains
            if 'domain' not in query.keys() or not query['domain']:
                domain = None
            else:
                domain = query['domain']

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'list_groups')

            # iterate through all domains and spit out some groups
            buf = {} 
            self.cfg.log.debug("API_userdata/list_groups: querying for all groups")
            if domain:
                grouptable = self.cfg.dbsess.query(Groups).\
                filter(Groups.domain==domain).all()
            else:
                grouptable = self.cfg.dbsess.query(Groups).all()
            for g in grouptable:
                if g.domain not in buf.keys():
                  buf[g.domain] = []
            for g in grouptable:
                buf[g.domain].append("%s gid:%s" % (g.groupname, g.gid))

            # if the user specified a domain but it's empty
            if buf == {} and domain:
                self.cfg.log.debug("API_userdata/list_groups: no groups in domain %s" % domain)
                raise UserdataError("API_userdata/list_groups: no groups in domain %s" % domain)
            elif buf == {}:
                self.cfg.log.debug("API_userdata/list_groups: no groups found")
                raise UserdataError("API_userdata/list_groups: no groups found")

            # return our listing
            self.cfg.log.debug(buf)
            return buf

        except Exception, e:
            self.cfg.log.debug("API_userdata/list_groups: query failed for groups. Error: %s" % e)
            raise UserdataError("API_userdata/list_groups: query failed for groups. Error: %s" % e)


    def list_domains(self, query):
        """
        [description]
        lists all domains

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns a list of domains
        """
        try:
            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'list_domains')

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/list_domains: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/list_domains: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # if the user specifies a domain, restrict output.
            # otherwise return userdata for all domains
            if 'domain' not in query.keys() or not query['domain']:
                domain = None
            else:
                domain = query['domain']

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'list_domains')

            # little bit of setup work
            buf = []
            self.cfg.log.debug("API_userdata/list_domains: querying for all domains")

            # iterate through all users and spit out some domains
            usertable = self.cfg.dbsess.query(Users).all()
            for u in usertable:
                if u.domain not in buf:
                  buf.append(u.domain)

            # iterate through all groups and spit out some domains
            # just in case we have some oddball domain with groups and no users
            grouptable = self.cfg.dbsess.query(Groups).all()
            for g in grouptable:
                if g.domain not in buf:
                  buf.append(g.domain)

            # if nothing exists
            if buf == []:
                self.cfg.log.debug("API_userdata/list_domains: no domains found")
                raise UserdataError("API_userdata/list_domains: no domains found")

            # return our listing
            return buf

        except Exception, e:
            self.cfg.log.debug("API_userdata/list_domains: query failed for domains. Error: %s" % e)
            raise UserdataError("API_userdata/list_domains: query failed for groups. Error: %s" % e)





    #############################
    # user manipulation methods #
    #############################

    def udisplay(self, query):
        """
        [description]
        display the information for a user 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns a list of user ORMobjects and associated list of group ORMobjects if successful, raises an error if unsuccessful 
        """
        try:
            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'udisplay')

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/udisplay: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/udisplay: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # to make our conditionals easier
            if 'username' not in query.keys() or not query['username']:
                self.cfg.log.debug("API_userdata/udisplay: no username provided!")
                raise UserdataError("API_userdata/udisplay: no username provided!")

            # if the user specifies a domain, restrict output.
            # otherwise return userdata for all domains
            if 'domain' not in query.keys() or not query['domain']:
                query['domain'] = self.cfg.default_domain

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'udisplay')

            # find us a username to display, validation done in the __get_user_obj function
            try:
                u = self.__get_user_obj(query['username'], query['domain']) 
            except:
                self.cfg.log.debug("API_userdata/udisplay: user %s not found (domain: %s)" % (query['username'], query['domain']))
                raise UserdataError("API_userdata/udisplay: user %s not found (domain: %s)" % (query['username'], query['domain']))

            # got a user, populate the return 
            if u:
                ret = {}
                ret['user'] = u.to_dict()
                ret['groups'] = []
                # user exists, find out what groups it's in 
                glist = self.__get_groups_by_user(u.username, u.domain)
                if glist:
                    for g in glist:
                        ret['groups'].append(g.to_dict())
            else:
                self.cfg.log.debug("API_userdata/udisplay: user %s not found." % query['username'])
                raise UserdataError("API_userdata/udisplay: user %s not found" % query['username'])

            # return's populated, return it
            return ret

        except Exception, e:
            self.cfg.log.debug("API_userdata/udisplay: %s" % e) 
            raise UserdataError("API_userdata/udisplay: %s" % e) 



    def uadd(self, query, files=None):
        """
        [description]
        create a new Users entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, raises an error if not
        """
        # setting our valid query keys
        common = VyvyanCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'uadd')

        try:
            # to make our conditionals easier
            if 'username' not in query.keys() or not query['username']:
                self.cfg.log.debug("API_userdata/uadd: no username provided!")
                raise UserdataError("API_userdata/uadd: no username provided!")
            else:
                username = query['username']
            if 'password' not in query.keys() or not query['password']:
                self.cfg.log.debug("API_userdata/uadd: no password provided!")
                raise UserdataError("API_userdata/uadd: no password provided!")
            else:
                password = query['password']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/uadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/uadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'uadd')
            # first name, validate or default
            if 'domain' in query.keys() and query['domain']:
                domain = query['domain']
                v_domain(domain)
            else:
                domain = self.cfg.default_domain
            # first name, validate or default
            if 'first_name' in query.keys() and query['first_name']:
                first_name = query['first_name']
                v_name(first_name)
            else:
                first_name = "John"
            # last name, validate or default
            if 'last_name' in query.keys() and query['last_name']:
                last_name = query['last_name']
                v_name(last_name)
            else:
                last_name = "Doe"
            # user type, validate or default
            if 'user_type' in query.keys() and query['user_type']:
                user_type = query['user_type']
                if user_type not in self.cfg.user_types:
                    self.cfg.log.debug("API_userdata/uadd: Invalid user type, please use one of the following: " + ', '.join(self.cfg.user_types))
                    raise UserdataError("API_userdata/uadd: Invalid user type, please use one of the following: " + ', '.join(self.cfg.user_types))
            else:
                user_type = self.cfg.def_user_type
            # shell, assign or default
            if 'shell' in query.keys() and query['shell']:
                shell = query['shell']
            else:
                shell = self.cfg.shell
            # ssh_keys file, validate or assign empty string 
            if files:
                if len(files) > 1:
                    self.cfg.log.debug("API_userdata/uadd: too many files uploaded for ssh_keys, refusing to continue")
                    raise UserdataError("API_userdata/uadd: too many files uploaded for ssh_keys, refusing to continue")
                ssh_keys = []
                for key in files[0].readlines():
                    if v_ssh2_pubkey(key):
                        ssh_keys.append(key)
                ssh_public_key = ''.join(ssh_keys).rstrip()
            else:
                ssh_public_key = "" 
            # home dir, assign or default
            if 'home_dir' in query.keys() and query['home_dir']:
                home_dir = query['home_dir']
            else:
                home_dir = "%s/%s" % (self.cfg.hdir, username)
            # email address, assign or default
            if 'email_address' in query.keys() and query['email_address']:
                email_address = query['email_address']
            else:
                email_address = "%s@%s" % (username, domain) 

            # input validation for username
            if username:
                v_name(username)
            else:
                self.cfg.log.debug("API_userdata/uadd: invalid username: %s" % username)
                raise UserdataError("API_userdata/uadd: invalid username: %s" % username)

            # make sure we're not trying to add a duplicate, validation done in the __get_user_obj function
            u = self.__get_user_obj(username, domain)
            if u:
                self.cfg.log.debug("API_userdata/uadd: user %s exists in domain %s" % (username, domain))
                raise UserdataError("API_userdata/uadd: user %s exists in domain %s" % (username, domain))
           
            # uid, validate or generate
            if 'uid' in query.keys() and query['uid']:
                uid = int(query['uid'])
                v_uid(self.cfg, uid)
                if v_uid_in_db(self.cfg, uid, domain):
                    self.cfg.log.debug("API_userdata/uadd: uid %s exists in domain %s already" % (uid, domain))
                    raise UserdataError("API_userdata/uadd: uid %s exists in domain %s already" % (uid, domain))
            else:
                uid = self.__next_available_uid(domain)

            # deal with default groups
            dg = []
            if self.cfg.default_groups:
                for grp in self.cfg.default_groups:
                    try:
                        # see if our default group(s) exist
                        g = self.__get_group_obj(grp, domain)
                        if g:
                            dg.append(g)
                        else:
                            # if not, explode
                            self.cfg.log.debug("API_userdata/uadd: default groups must exist before we can add users to them! missing group: %s in %s" % (grp, domain))
                            raise UserdataError("API_userdata/uadd: default groups must exist before we can add users to them! missing group: %s in %s" % (grp, domain))
                    except:
                        # if anything goes wrong, explode.
                        self.cfg.log.debug("API_userdata/uadd: default groups must exist before we can add users to them! missing group: %s in %s" % (grp, domain))
                        raise UserdataError("API_userdata/uadd: default groups must exist before we can add users to them! missing group: %s in %s" % (grp, domain))

            # hash the password. since we're LDAP-oriented we'll use SSHA
            passhash = passlib.hash.ldap_salted_sha1.encrypt(password, salt_size=self.cfg.salt_size)

            # create the user object, push it to the db, return status
            u = Users(first_name, last_name, ssh_public_key, passhash, username, domain, uid, user_type, home_dir, shell, email_address, active=True)
            self.cfg.dbsess.add(u)
            self.cfg.dbsess.commit()

            # if our default group(s) exist, shove the user into it/them
            if dg:
                for g in dg:
                    ugquery = {'username': username, 'groupname': g.groupname, 'domain': domain}
                    self.utog(ugquery)
                    self.cfg.log.debug("API_userdata/uadd: adding user %s to default group %s in domain %s" % (username, g.groupname, domain))
            return 'success'
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/uadd: error: %s" % e)
            raise UserdataError("API_userdata/uadd: error: %s" % e)


    def uremove(self, query):
        """
        [description]
        delete a user from the users table

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, None if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'username' not in query.keys() or not query['username']:
                self.cfg.log.debug("API_userdata/uremove: no username provided!")
                raise UserdataError("API_userdata/uremove: no username provided!")
            else:
                username = query['username']
                v_name(username)

            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'uremove')

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/uremove: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/uremove: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'uremove')

            # domain, validate or assign default 
            if 'domain' in query.keys() and query['domain']:
                domain = query['domain']
                v_domain(domain) 
            else:
                domain = self.cfg.default_domain

            # find us a username to delete, validation done in the __get_user_obj function
            u = self.__get_user_obj(username, domain) 
            if u:
                groups = self.__get_groups_by_user(username, domain)
                if groups:
                    for group in groups:
                        query = {"username": username, "groupname": group.groupname, "domain": domain} 
                        self.urmg(query) 
                self.cfg.dbsess.delete(u)
                self.cfg.dbsess.commit()
                self.cfg.log.debug("API_userdata/uremove: deleted user %s from domain %s" % (username, domain))
                return "success"
            else:
                self.cfg.log.debug("API_userdata/uremove: user %s not found in domain %s" % (username, domain))
                raise UserdataError("API_userdata/uremove: user %s not found in domain %s" % (username, domain))

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/uremove: error: %s" % e)
            raise UserdataError("API_userdata/uremove: error: %s" % e)


    def umodify(self, query, files=None):
        """
        [description]
        create a new tags entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns true if successful, raises an error if not
        """
        # setting our valid query keys
        common = VyvyanCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'umodify')

        try:
            # to make our conditionals easier
            if 'username' not in query.keys() or not query['username']:
                self.cfg.log.debug("API_userdata/umodify: no username provided!")
                raise UserdataError("API_userdata/umodify: no username provided!")
            else:
                username = query['username']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/umodify: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/umodify: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'umodify')

            # we do this here nad not below with the rest of the options because
            # we need this set to get a valid user object
            #
            # domain, validate or assign default 
            if 'domain' in query.keys() and query['domain']:
                domain = query['domain']
                v_domain(domain) 
            else:
                domain = self.cfg.default_domain

            # find us a username to modify, validation done in the __get_user_obj function
            u = self.__get_user_obj(username, domain) 
            if not u:
                self.cfg.log.debug("API_userdata/umodify: refusing to modify nonexistent user: %s" % username)
                raise UserdataError("API_userdata/umodify: refusing to modify nonexistent user: %s" % username)
           
            # first name, validate or leave alone 
            if 'first_name' in query.keys() and query['first_name']:
                v_name(query['first_name'])
                u.first_name = query['first_name']
            # last name, validate or leave alone 
            if 'last_name' in query.keys() and query['last_name']:
                v_name(query['last_name'])
                u.last_name = query['last_name']
            # user type, validate or leave alone 
            if 'user_type' in query.keys() and query['user_type']:
                if query['user_type'] not in self.cfg.user_types:
                    self.cfg.log.debug("API_userdata/umodify: Invalid user type, please use one of the following: " + ', '.join(self.cfg.user_types))
                    raise UserdataError("API_userdata/umodify: Invalid user type, please use one of the following: " + ', '.join(self.cfg.user_types))
                else:
                    u.user_type = query['user_type']
            # shell, assign or leave alone 
            if 'shell' in query.keys() and query['shell']:
                u.shell = query['shell']
            # ssh_keys file, validate or leave alone 
            if files:
                if len(files) > 1:
                    self.cfg.log.debug("API_userdata/umodify: too many files uploaded for ssh_keys, refusing to continue")
                    raise UserdataError("API_userdata/umodify: too many files uploaded for ssh_keys, refusing to continue")
                ssh_keys = []
                for key in files[0].readlines():
                    if v_ssh2_pubkey(key):
                        ssh_keys.append(key)
                u.ssh_public_key = ''.join(ssh_keys).rstrip()
            # home dir, assign or leave alone 
            if 'home_dir' in query.keys() and query['home_dir']:
                u.hdir = query['home_dir']
            # email, assign or leave alone 
            if 'email_address' in query.keys() and query['email_address']:
                u.email = query['email_address']
            # uid, validate or leave alone 
            if 'uid' in query.keys() and query['uid']:
                if u.uid != int(query['uid']) and v_uid_in_db(self.cfg, int(query['uid']), u.domain):
                    self.cfg.log.debug("API_userdata/umodify: uid exists already: %s" % query['uid'])
                    raise UserdataError("API_userdata/umodify: uid exists already: %s" % query['uid'])
                u.uid = int(query['uid'])

            # hash the password. since we're LDAP-oriented we'll use SSHA
            # TODO: provide support for checking passwords against a configurable number
            # TODO: of passwords and rejecting matches
            if 'password' in query.keys() and query['password']:
                passhash = passlib.hash.ldap_salted_sha1.encrypt(password, salt_size=cfg.salt_size)
                u.password = passhash

            # activate/deactivate the user
            if 'active' in query.keys() and query['active'] in ['F', 'f', 'False', 'false']:
                u.active = False
            elif 'active' in query.keys() and query['active'] in ['T', 't', 'True', 'true']:
                u.active = True

            # push the modified user object to the db, return status
            self.cfg.dbsess.add(u)
            self.cfg.dbsess.commit()
            return 'success'
        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/umodify: error: %s" % e)
            raise UserdataError("API_userdata/umodify: error: %s" % e)


    def uclone(self, query):
        """
        [description]
        delete a user from the users table

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, None if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'username' not in query.keys() or not query['username']:
                self.cfg.log.debug("API_useradata/uclone: no username provided!")
                raise UserdataError("API_useradata/uclone: no username provided!")
            if 'domain' not in query.keys() or not query['domain']:
                self.cfg.log.debug("API_useradata/uclone: no domain provided!")
                raise UserdataError("API_useradata/uclone: no domain provided!")
            if 'newdomain' not in query.keys() or not query['newdomain']:
                self.cfg.log.debug("API_useradata/uclone: no new domain provided!")
                raise UserdataError("API_useradata/uclone: no new domain provided!")

            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'uclone')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/uclone: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/uclone: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # input validation for new domain
            v_domain(query['domain'])

            # find us a username to clone, validation done in the __get_user_obj function
            u = self.__get_user_obj(query['username'], query['domain']) 
            if u:
                query = {
                    'username': query['username'],
                    'domain': query['newdomain'],
                    'first_name': u.first_name,
                    'last_name': u.last_name,
                    'uid': u.uid,
                    'user_type': u.type,
                    'shell': u.shell,
                    'email_address': u.email,
                    'ssh_key': u.ssh_public_key,
                    'home_dir': u.hdir,
                }
                self.uadd(query)
                self.cfg.log.debug("API_userdata/uclone: created user %s in query['domain'] %s based on query['domain'] %s" % (query['username'], query['newdomain'], query['domain']))
                return "success"
            else:
                self.cfg.log.debug("API_userdata/uclone: user %s not found in query['domain'] %s" % (query['username'], query['domain']))
                raise UserdataError("API_userdata/uclone: user %s not found in %s" % (query['username'], query['domain']))

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/uclone: error: %s" % e)
            raise UserdataError("API_userdata/uclone: error: %s" % e)


    ##############################
    # group manipulation methods #
    ##############################

    def gdisplay(self, query):
        """
        [description]
        display the information for a group 

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns the group ORMobject dict if successful, raises an error if unsuccessful
        """
        try:
            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'gdisplay')

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gdisplay: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gidsplay: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # to make our conditionals easier
            if 'groupname' not in query.keys() or not query['groupname']:
                self.cfg.log.debug("API_userdata/gdisplay: no groupname provided!")
                raise UserdataError("API_userdata/gdisplay: no groupname provided!")
            else:
                groupname = query['groupname']

            # domain, validate or substitute default 
            if 'domain' in query.keys() and query['domain']:
                domain = query['domain']
                v_domain(domain) 
            else:
                domain = self.cfg.default_domain
 
            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'gdisplay')

            # look for the group
            try:
                g = self.__get_group_obj(groupname, domain) 
                ret = {} 
                ret['group'] = g.to_dict()
            except Exception, e:
                self.cfg.log.debug("API_userdata/gdisplay: group %s not found in domain %s." % (groupname, domain))
                raise UserdataError("API_userdata/gdisplay: group %s not found in domain %s" % (groupname, domain))

            # now that we know the group exists, we can see if it's populated with users
            ret['users'] = []
            ulist = self.__get_users_by_group(groupname, domain)
            if ulist:
                for u in ulist:
                    ret['users'].append(u.to_dict())

            # return is populated, return it
            return ret

        except Exception, e:
            self.cfg.log.debug("API_userdata/gdisplay: %s" % e) 
            raise UserdataError("API_userdata/gdisplay: %s" % e) 


    def gadd(self, query, files=None):
        """
        [description]
        create a new tags entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns true if successful, raises an error if not
        """
        # setting our valid query keys
        common = VyvyanCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'gadd')

        try:
            # to make our conditionals easier
            if 'groupname' not in query.keys() or not query['groupname']:
                self.cfg.log.debug("API_userdata/gadd: no groupname provided!")
                raise UserdataError("API_userdata/gadd: no groupname provided!")
            else:
                groupname = query['groupname']
                v_name(groupname)


            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gadd: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'gadd')

            # domain, validate or default
            self.cfg.log.debug("default_domain: %s" % self.cfg.default_domain)
            if 'domain' in query.keys() and query['domain']:
                domain = query['domain']
                v_domain(domain)
            else:
                domain = self.cfg.default_domain 

            # description, assign or default
            if 'description' in query.keys() and query['description']:
                description = query['description']
            else:
                description = 'Please add a description for this group!' 

            # sudo commands. if "all" (case insensetive), translate to "ALL". if not and not blank, assign.  
            if 'sudo_cmds' in query.keys() and query['sudo_cmds']:
                sudo_cmds = query['sudo_cmds'].split(',')
                if 'ALL' in map(str.upper, sudo_cmds):
                    sudo_cmds = ['ALL']
            else:
                sudo_cmds = None

            # make sure we're not trying to add a duplicate
            g = self.__get_group_obj(groupname, domain) 
            if g:
                self.cfg.log.debug("API_userdata/gadd: group exists already: %s" % groupname)
                raise UserdataError("API_userdata/gadd: group exists already: %s" % groupname)
           
            # gid, validate or generate
            # this is down here instead of up above with its buddies because we need the
            # domain to query for existing uids
            if 'gid' in query.keys() and query['gid']:
                gid = int(query['gid'])
                v_gid(self.cfg, gid)
                if v_gid_in_db(self.cfg, gid, domain):
                    self.cfg.log.debug("API_userdata/gadd: gid exists already: %s" % gid)
                    raise UserdataError("API_userdata/gadd: gid exists already: %s" % gid)
            else:
                gid = self.__next_available_gid(domain)

            # create the group object, push it to the db, return status
            g = Groups(description, groupname, domain, gid)
            self.cfg.dbsess.add(g)
            self.cfg.dbsess.commit()

            # map any sudo commands to the group
            if sudo_cmds:
              self.__map_sudoers(g, sudo_cmds)

            return 'success'

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/gadd: error: %s" % e)
            raise UserdataError("API_userdata/gadd: error: %s" % e)


    def gremove(self, query):
        """
        [description]
        delete a group from the groups table

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, None if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'groupname' not in query.keys() or not query['groupname']:
                self.cfg.log.debug("API_userdata/gremove: no groupname provided!")
                raise UserdataError("API_userdata/gremove: no groupname provided!")
            else:
                groupname = query['groupname']

            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'gremove')

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gremove: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gremove: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'gremove')

            # domain, validate or default
            if 'domain' in query.keys() and query['domain']:
                domain = query['domain']
                v_domain(domain)
            else:
                domain = self.cfg.default_domain 

            # find us a groupname to delete, validation done in the __get_group_obj function
            g = self.__get_group_obj(groupname, domain) 
            if g:
                # make sure the group is empty
                if self.__get_users_by_group(groupname, domain):
                    self.cfg.log.debug("API_userdata/gremove: please remove all users from this group before deleting!")
                    raise UserdataError("API_userdata/gremove: please remove all users from this group before deleting!")
                # unmap any existing commands
                self.__unmap_sudoers(g)
                # delete the group
                self.cfg.dbsess.delete(g)
                # commit the transaction
                self.cfg.dbsess.commit()
                self.cfg.log.debug("API_userdata/gremove: deleted group %s from domain %s" % (groupname, domain))
                # declare victory
                return "success"
            else:
                self.cfg.log.debug("API_userdata/gremove: group %s not found in domain %s" % (groupname, domain))
                raise UserdataError("API_userdata/gremove: group %s not found in domain %s" % (groupname, domain))

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/gremove: error: %s" % e)
            raise UserdataError("API_userdata/gremove: error: %s" % e)


    def gmodify(self, query, files=None):
        """
        [description]
        create a new tags entry

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns true if successful, raises an error if not
        """
        # setting our valid query keys
        common = VyvyanCommon(self.cfg)
        valid_qkeys = common.get_valid_qkeys(self.namespace, 'gmodify')

        try:
            # to make our conditionals easier
            if 'groupname' not in query.keys() or not query['groupname']:
                self.cfg.log.debug("API_userdata/gmodify: no groupname provided!")
                raise UserdataError("API_userdata/gmodify: no groupname provided!")
            else:
                groupname = query['groupname']

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gmodify: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gmodify: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'gmodify')

            # domain, validate or default
            if 'domain' in query.keys() and query['domain']:
                domain = query['domain']
                v_domain(domain)
            else:
                domain = self.cfg.default_domain 

            # find us a groupname to modify, validation done in the __get_group_obj function
            g = self.__get_group_obj(groupname, domain) 
            if not g:
                self.cfg.log.debug("API_userdata/gmodify: refusing to modify nonexistent group %s in domain %s" % (groupname, domain))
                raise UserdataError("API_userdata/gmodify: refusing to modify nonexistent group %s in domain %s" % (groupname, domain))
           
            # description, assign or leave alone
            if 'description' in query.keys() and query['description']:
                g.description = query['description']

            # sudo commands. if "all" (case insensetive), translate to "ALL". if not and not blank, assign.  
            if 'sudo_cmds' in query.keys() and query['sudo_cmds']:
                sudo_cmds = query['sudo_cmds'].split(',')
                if 'ALL' in map(str.upper, sudo_cmds):
                    sudo_cmds = ['ALL']

            # gid, validate or leave alone 
            if 'gid' in query.keys() and query['gid']:
                if g.gid != int(query['gid']) and v_gid_in_db(self.cfg, int(query['gid']), g.domain):
                    self.cfg.log.debug("API_userdata/gmodify: gid exists in domain %s already: %s" % (domain, query['gid']))
                    raise UserdataError("API_userdata/gmodify: gid exists in domain %s already: %s" % (domain, query['gid']))
                g.gid = int(query['gid'])

            # push the modified group object to the db, return status
            self.cfg.dbsess.add(g)
            self.cfg.dbsess.commit()

            # remap sudoers commands
            # NOTE: you must provide the entire sudo_cmds array each time you modify a group
            # or it will delete existing commands
            if sudo_cmds:
              self.__map_sudoers(g, sudo_cmds)

            # declare victory
            return 'success'

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/gmodify: error: %s" % e)
            raise UserdataError("API_userdata/gmodify: error: %s" % e)


    def gclone(self, query):
        """
        [description]
        delete a group from the groups table

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, None if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'groupname' not in query.keys() or not query['groupname']:
                self.cfg.log.debug("API_userdata/gclone: no groupname provided!")
                raise UserdataError("API_userdata/gclone: no groupname provided!")
            if 'domain' not in query.keys() or not query['domain']:
                self.cfg.log.debug("API_userdata/gclone: no domain provided!")
                raise UserdataError("API_userdata/gclone: no domain provided!")
            if 'newdomain' not in query.keys() or not query['newdomain']:
                self.cfg.log.debug("API_userdata/gclone: no new domain provided!")
                raise UserdataError("API_userdata/gclone: no new domain provided!")

            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'gclone')
            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/gclone: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/gclone: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # input validation for new domain
            v_domain(self.cfg, domain)

            # find us a groupname to clone, validation done in the __get_group_obj function
            g = self.__get_group_obj(groupname, domain) 
            
            # get sudo commands for the group
            sudo_cmds = []
            for gsmap in self.cfg.dbsess.query(GroupSudocommandMapping).filter(GroupSudocommandMapping.groups_id==group.id).all():
              sudo_cmds.append(gsmap.sudocommand)

            # put it all together
            if g:
                query = {
                    'groupname': groupname,
                    'domain': newdomain,
                    'gid': g.gid,
                    'sudo_cmds': ','.join(sudo_cmds),
                    'description': g.description,
                }
                self.gadd(query) 
                self.cfg.log.debug("API_userdata/gclone: created group %s in domain %s" % (groupname, newdomain))
                return "success"
            else:
                self.cfg.log.debug("API_userdata/gclone: group %s not found in domain %s" % (groupname, domain))
                raise UserdataError("API_userdata/gclone: group %s not found in domain %s" % (groupname, domain))

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/gclone: error: %s" % e)
            raise UserdataError("API_userdata/gclone: error: %s" % e)


    ###################################
    # user-to-group mapping functions #
    ###################################

    
    def utog(self, query):
        """
        [description]
        map a user into a group

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, raises an error if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'username' not in query.keys() or not query['username']:
                self.cfg.log.debug("API_userdata/utog: no username provided!")
                raise UserdataError("API_userdata/utog: no username provided!")
            if 'groupname' not in query.keys() or not query['groupname']:
                self.cfg.log.debug("API_userdata/utog: no group provided!")
                raise UserdataError("API_userdata/utog: no group provided!")

            # validate things
            v_name(query['username'])
            v_name(query['groupname'])


            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'utog')

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/utog: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/tog: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'utog')

            # domain, validate or assign
            if 'domain' in query.keys() and query['domain']:
                domain = query['domain']
                v_domain(domain)
            else:
                domain = self.cfg.default_domain                

            # fetch our user and group
            u = self.__get_user_obj(query['username'], domain)
            g = self.__get_group_obj(query['groupname'], domain)
            if not u:
                self.cfg.log.debug("API_userdata/utog: user not found: %s in %s" % (query['username'], domain))
                raise UserdataError("API_userdata/utog: user not found: %s in %s" % (query['username'], domain))
            elif not g:
                self.cfg.log.debug("API_userdata/utog: group not found: %s in %s" % (query['groupname'], domain))
                raise UserdataError("API_userdata/utog: group not found: %s in %s" % (query['groupname'], domain))
            else:
                if self.cfg.dbsess.query(UserGroupMapping).\
                filter(UserGroupMapping.users_id==u.id).\
                filter(UserGroupMapping.groups_id==g.id).first():
                    self.cfg.log.debug("API_userdata/utog: mapping exists! refusing to create duplicate mapping")
                    raise UserdataError("API_userdata/utog: mapping exists! refusing to create duplicate mapping")
                ugmap = UserGroupMapping(g.id, u.id)
                self.cfg.dbsess.add(ugmap)
                self.cfg.dbsess.commit()
                return 'success'

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/utog: error: %s" % e)
            raise UserdataError("API_userdata/utog: error: %s" % e)


    def urmg(self, query):
        """
        [description]
        unmap a user from a group

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return]
        Returns "success" if successful, raises an error if unsuccessful 
        """
        try:
            # to make our conditionals easier
            if 'username' not in query.keys() or not query['username']:
                self.cfg.log.debug("API_userdata/utog: no username provided!")
                raise UserdataError("API_userdata/utog: no username provided!")
            if 'groupname' not in query.keys() or not query['groupname']:
                self.cfg.log.debug("API_userdata/utog: no group provided!")
                raise UserdataError("API_userdata/utog: no group provided!")

            # setting our valid query keys
            common = VyvyanCommon(self.cfg)
            valid_qkeys = common.get_valid_qkeys(self.namespace, 'urmg')

            # check for wierd query keys, explode
            for qk in query.keys():
                if qk not in valid_qkeys:
                    self.cfg.log.debug("API_userdata/utog: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))
                    raise UserdataError("API_userdata/tog: unknown querykey \"%s\"\ndumping valid_qkeys: %s" % (qk, valid_qkeys))

            # check for min/max number of optional arguments
            common.check_num_opt_args(query, self.namespace, 'urmg')

            # domain, validate or default
            if 'domain' in query.keys() and query['domain']:
                domain = query['domain']
                v_domain(domain)
            else:
                domain = self.cfg.default_domain 

            # fetch our user and group
            u = self.__get_user_obj(query['username'], domain)
            g = self.__get_group_obj(query['groupname'], domain)

            # explode if things are missing
            if not u:
                self.cfg.log.debug("API_userdata/utog: user %s not found in domain %s" % (query['username'], domain))
                raise UserdataError("API_userdata/utog: user %s not found in domain %s" % (query['username'], domain))
            elif not g:
                self.cfg.log.debug("API_userdata/utog: group %s not found in domain %s" % (query['groupname'], domain))
                raise UserdataError("API_userdata/utog: group %s not found in domain %s" % (query['groupname'], domain))
            else:
                # get the mapping entry
                ugmap = self.cfg.dbsess.query(UserGroupMapping).\
                filter(UserGroupMapping.users_id==u.id).\
                filter(UserGroupMapping.groups_id==g.id).first()
                if not ugmap:
                    self.cfg.log.debug("API_userdata/utog: mapping does not exist")
                    raise UserdataError("API_userdata/utog: mapping does not exist")
                # rm it
                self.cfg.dbsess.delete(ugmap)
                self.cfg.dbsess.commit()
                return 'success'

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/utog: error: %s" % e)
            raise UserdataError("API_userdata/utog: error: %s" % e)


    #################################
    # internal functions below here #
    #################################

    def __get_group_obj(self, groupname, domain):
        """
        [description]
        for a given groupname, fetch the group object 
    
        [parameter info]
        required:
            groupname: the groupname we want to parse
    
        [return value]
        returns a Groups ORM object or None
        """
        try:
            # validate things 
            v_name(groupname)
            v_domain(domain)

            # go get our group
            g = self.cfg.dbsess.query(Groups).\
            filter(Groups.groupname==groupname).\
            filter(Groups.domain==domain).first()
    
            if g:
                return g
            else:
                return None 

        except Exception, e:
            raise UserdataError("API_userdata/__get_group_obj: error: %s" % e)


    def __get_user_obj(self, username, domain):
        """
        [description]
        for a given username, fetch the user object 
    
        [parameter info]
        required:
            username: the username we want to find
            domain: the domain that contains our user
    
        [return value]
        returns a Users ORM object or None
        """
        try:
            # validate stuff 
            v_name(username)
            v_domain(domain)

            # go get our user
            u = self.cfg.dbsess.query(Users).\
            filter(Users.username==username).\
            filter(Users.domain==domain).first()
    
            if u:
                return u
            else:
                return None 

        except Exception, e:
            raise UserdataError("API_userdata/__get_group_obj: error: %s" % e)


    def __next_available_uid(self, domain):
        """
        [description]
        searches the db for existing UIDS and picks the next available UID within the parameters configured in vyvyan.yaml
    
        [parameter info]
        required:
            domain: the domain we're checking uids for
    
        [return value]
        returns an integer representing the next available UID
        """
        try:
            # get the first allowable uid 
            i = self.cfg.uid_start
            uidlist = []

            # fetch all existing users
            u = self.cfg.dbsess.query(Users).\
            filter(Users.domain==domain).all()

            # add all known uids to a list
            for userentry in u:
                uidlist.append(userentry.uid)
            uidlist.sort(key=int)


            # if we don't have any users in the users table
            # return the default first uid as configured in the yaml
            # otherwise, pick the next open uid and return it
            if not uidlist:
                return self.cfg.uid_start
            else:
                for uu in uidlist:
                    if uu < self.cfg.uid_start:
                        pass
                    elif not i == uu and i < self.cfg.uid_end:
                        return i
                    elif i < self.cfg.uid_end:
                        i += 1
                    else:
                        self.cfg.log.debug("API_userdata/__next_available_uid: No available UIDs!")
                        raise UserdataError("API_userdata/__next_available_uid: No available UIDs!")
                return i

        except Exception, e:
            raise UserdataError("API_userdata/__next_available_uid: %s" % e)


    def __next_available_gid(self, domain):
        """
        [description]
        searches the db for existing GIDS and picks the next available GID within the parameters configured in vyvyan.yaml
    
        [parameter info]
        required:
            domain: the domain we're checking gids for
    
        [return value]
        returns an integer representing the next available GID
        """
        try: 
            # get the first allowable gid 
            i = self.cfg.gid_start
            gidlist = []

            # fetch all existing groups 
            g = self.cfg.dbsess.query(Groups).\
            filter(Groups.domain==domain).all()

            # add all known uids to a list
            for groupentry in g:
                gidlist.append(groupentry.gid)
            gidlist.sort(key=int)


            # if we don't have any groups in the groups table
            # return the default first gid as configured in the yaml
            # otherwise pick the next open gid and return it
            if not gidlist:
                return self.cfg.gid_start
            else:
                for gg in gidlist:
                    if gg < self.cfg.gid_start:
                        pass
                    elif not i == gg and i < self.cfg.gid_end:
                        return i
                    elif i < self.cfg.gid_end:
                        i += 1
                    else:
                        self.cfg.log.debug("API_userdata/__next_available_gid: No available GIDs!")
                        raise UserdataError("API_userdata/__next_available_gid: No available GIDs!")
                return i

        except Exception, e:
            raise UserdataError("API_userdata/__next_available_gid: %s" % e)


    def __get_groups_by_user(self, username, domain):
        """
        [description]
        searches the db for user-group mappings by username 
    
        [parameter info]
        required:
            username: the username to search for 
            domain: the domain to search in 
    
        [return value]
        returns a list of Groups ORMobjects or nothing 
        """
        try:
            # fetch our user
            glist = []
            u = self.__get_user_obj(username, domain)
            if not u:
                self.cfg.log.debug("API_userdata/__get_groups_by_user: user not found: %s" % username)
                raise UserdataError("API_userdata/__get_groups_by_user: user not found: %s" % username)

            # get all groups to which the user is mapped
            maplist = []
            maplist = self.cfg.dbsess.query(UserGroupMapping).\
                filter(UserGroupMapping.users_id==u.id).all()

            # add each group mapped to the user to a list, return it
            if maplist:
                for ugmap in maplist:
                    glist.append(self.cfg.dbsess.query(Groups).filter(Groups.id==ugmap.groups_id).first())
            return glist

        except Exception, e:
            raise UserdataError("API_userdata/__get_groups_by_user: %s" % e)


    def __get_users_by_group(self, groupname, domain):
        """
        [description]
        searches the db for user-group mappings by groupname 
    
        [parameter info]
        required:
            groupname: the groupname to search for 
            domain: the domain to search in 
    
        [return value]
        returns a list of Groups ORMobjects or nothing 
        """
        try:
            # fetch our group
            ulist = []
            g = self.__get_group_obj(groupname, domain)
            if not g:
                self.cfg.log.debug("API_userdata/__get_users_by_group: group %s not found in %s" % (groupname, domain))
                raise UserdataError("API_userdata/__get_groups_by_user: group %s not found in %s" % (groupname, domain))

            # get all users mapped to this group
            maplist = []
            maplist = self.cfg.dbsess.query(UserGroupMapping).\
                filter(UserGroupMapping.groups_id==g.id).all()

            # add each user mapped to the group to a list, return it
            if maplist:
                for ugmap in maplist:
                    ulist.append(self.cfg.dbsess.query(Users).filter(Users.id==ugmap.users_id).first())
            return ulist

        except Exception, e:
            raise UserdataError("API_userdata/__get_users_by_group: %s" % e)


    def __map_sudoers(self, group, sudo_cmds):
        """
        [description]
        map a set of sudo commands to a group

        [parameter info]
        required:
            group: the ORM object of the group we want to map
            sudo_cmds: a list of strings representing the commands to map to the group 

        [return]
        Returns "success" if successful, raises an error if unsuccessful 
        """
        try:
            # for sanity's sake
            if not group:
                self.cfg.log.debug("API_userdata/__map_sudoers: group not found, missing parameter")
                raise UserdataError("API_userdata/__map_sudoers: group not found, missing parameter")
            elif not sudo_cmds:
                self.cfg.log.debug("API_userdata/__map_sudoers: sudo_cmds not found, missing parameter")
                raise UserdataError("API_userdata/__map_sudoers: sudo_cmds not found, missing parameter")
            else:

                # loop over commands and map them to the group
                for command in sudo_cmds:
                    if not self.cfg.dbsess.query(GroupSudocommandMapping).\
                    filter(GroupSudocommandMapping.sudocommand==command).\
                    filter(GroupSudocommandMapping.groups_id==group.id).first():
                      gsmap = GroupSudocommandMapping(group.id, command)
                      self.cfg.dbsess.add(gsmap)

                # loop over existing mappings and ensure they're valid. remove any invalid mappings
                for gsmap in self.cfg.dbsess.query(GroupSudocommandMapping).filter(GroupSudocommandMapping.groups_id==group.id).all():
                  if gsmap.sudocommand not in sudo_cmds:
                    self.cfg.dbsess.delete(gsmap)

                # commit our transaction
                self.cfg.dbsess.commit()

                # declare victory
                return 'success'

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/__map_sudoers: error: %s" % e)
            raise UserdataError("API_userdata/__map_sudoers: error: %s" % e)


    def __unmap_sudoers(self, group):
        """
        [description]
        map a set of sudo commands to a group

        [parameter info]
        required:
            group: the ORM object of the group we want to unmap

        [return]
        Returns "success" if successful, raises an error if unsuccessful 
        """
        try:

            # for sanity's sake
            if not group:
                self.cfg.log.debug("API_userdata/__unmap_sudoers: group not found, missing parameter")
                raise UserdataError("API_userdata/__unmap_sudoers: group not found, missing parameter")

            # loop over existing mappings and remove
            else:
                for gsmap in self.cfg.dbsess.query(GroupSudocommandMapping).filter(GroupSudocommandMapping.groups_id==group.id).all():
                  self.cfg.dbsess.delete(gsmap)

                # commit our transaction
                self.cfg.dbsess.commit()

                # declare victory
                return 'success'

        except Exception, e:
            # something odd happened, explode violently
            self.cfg.dbsess.rollback()
            self.cfg.log.debug("API_userdata/__unmap_sudoers: error: %s" % e)
            raise UserdataError("API_userdata/__unmap_sudoers: error: %s" % e)
