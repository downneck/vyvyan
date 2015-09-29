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
    supports the listing of various types of values
"""

# imports
from sqlalchemy import or_, desc, MetaData
from vyvyan.vyvyan_models import *
from vyvyan.common import *

class ListValuesError(Exception):
    pass


class API_list_values:

    def __init__(self, cfg):
        self.cfg = cfg
        self.common = VyvyanCommon(cfg)
        self.version = 1
        self.namespace = 'API_list_values'
        self.metadata = {
            'config': {
                'shortname': 'lsv',
                'description': 'retrieves and lists values from the database',
                'module_dependencies': {
                    'vyvyan_models': 1,
                },
            },
            'methods': {
                'users': {
                    'description': 'list all users',
                    'short': 'u',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                    },
                    'optional_args': {
                    },
                    'return': {
                        'values': ['value', 'value',], # in the case of users and groups, this will be a list of dicts
                    },
                },
                'groups': {
                    'description': 'list all groups',
                    'short': 'g',
                    'rest_type': 'GET',
                    'admin_only': False,
                    'required_args': {
                    },
                    'optional_args': {
                    },
                    'return': {
                        'values': ['value', 'value',], # in the case of users and groups, this will be a list of dicts
                    },
                },
            },
        }


    def users(self, query):
        """
        [description]
        lists all values of a given type

        [parameter info]
        required:
            query: the query dict being passed to us from the called URI

        [return value]
        returns an integer representing the next available UID
        """

        buf = []

        # verify the number of query arguments
        if len(query.keys()) > self.metadata['methods']['lsv']['optional_args']['max']:
            retval = "API_list_values/lsv: too many queries! max number of queries is: %s\n" % self.metadata['methods']['lsv']['optional_args']['max']
            retval += "API_list_values/lsv: you tried to pass %s queries\n" % len(query.keys())
            self.cfg.log.debug(retval)
            raise ListValuesError(retval)
        else:
            self.cfg.log.debug("API_list_values/lsv: num queries: %s" % len(query.keys()))
            self.cfg.log.debug("API_list_values/lsv: max num queries: %s" % self.metadata['methods']['lsv']['optional_args']['max'])

        # make sure we are being passed a valid query
        if query.keys()[0] not in self.metadata['methods']['lsv']['optional_args']['args'].keys():
            self.cfg.log.debug("API_list_values/lsv: unsupported listing for: %s. please specify one of the following: %s" % (query.keys()[0], " ".join(self.metadata['methods']['lsv']['optional_args']['args'].keys())))
            raise ListValuesError("API_list_values/lsv: unsupported listing for: %s. please specify one of the following: %s" % (query.keys()[0], " ".join(self.metadata['methods']['lsv']['optional_args']['args'].keys())))
        # check for min/max number of optional arguments
        self.common.check_num_opt_args(query, self.namespace, 'lsv')

        self.cfg.log.debug("API_list_values/lsv: querying for all users")
        try:
            for u in self.cfg.dbsess.query(Users):
                if u.active:
                    act = "active"
                else:
                    act = "inactive"
                buf.append("%s.%s.%s uid:%s %s" % (u.username, u.realm, u.site_id, u.uid, act))
            self.cfg.log.debug(buf)
        except Exception, e:
            self.cfg.log.debug("API_list_values/lsv: query failed for users. Error: %s" % e)
            raise ListValuesError("API_list_values/lsv: query failed for groups. Error: %s" % e)

        # return our listing
        return buf


    # groups
    def groups(self, query):
        """
        [description]
        lists all groups

        [parameter info]

        [return value]
        returns a list of groups
        """

        buf = []

        # verify the number of query arguments
        if len(query.keys()) > self.metadata['methods']['lsv']['optional_args']['max']:
            retval = "API_list_values/lsv: too many queries! max number of queries is: %s\n" % self.metadata['methods']['lsv']['optional_args']['max']
            retval += "API_list_values/lsv: you tried to pass %s queries\n" % len(query.keys())
            self.cfg.log.debug(retval)
            raise ListValuesError(retval)
        else:
            self.cfg.log.debug("API_list_values/lsv: num queries: %s" % len(query.keys()))
            self.cfg.log.debug("API_list_values/lsv: max num queries: %s" % self.metadata['methods']['lsv']['optional_args']['max'])

        # make sure we are being passed a valid query
        if query.keys()[0] not in self.metadata['methods']['lsv']['optional_args']['args'].keys():
            self.cfg.log.debug("API_list_values/lsv: unsupported listing for: %s. please specify one of the following: %s" % (query.keys()[0], " ".join(self.metadata['methods']['lsv']['optional_args']['args'].keys())))
            raise ListValuesError("API_list_values/lsv: unsupported listing for: %s. please specify one of the following: %s" % (query.keys()[0], " ".join(self.metadata['methods']['lsv']['optional_args']['args'].keys())))
        # check for min/max number of optional arguments
        self.common.check_num_opt_args(query, self.namespace, 'lsv')

        self.cfg.log.debug("API_list_values/lsv: querying for all groups")
        try:
            for g in self.cfg.dbsess.query(Groups):
                buf.append("%s.%s.%s gid:%s" % (g.groupname, g.realm, g.site_id, g.gid))
            self.cfg.log.debug(buf)
        except Exception, e:
            self.cfg.log.debug("API_list_values/lsv: query failed for groups. Error: %s" % e)
            raise ListValuesError("API_list_values/lsv: query failed for groups. Error: %s" % e)

        # return our listing
        return buf
