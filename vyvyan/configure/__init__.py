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
"""
    The Configure class is responsible for loading the yaml file that
    describes connecting to the database and any other configuration specific
    bits that should be abstracted away
"""
import os.path
import sys
import shutil
import yaml

# Extra modules
import xmlrpclib
import sqlalchemy
import sqlalchemy.orm

# our error class
class ConfigureError(Exception):
    pass

# This is the set of paths Configure will look for
# a config_file
load_paths = ['.', '~', '/etc', '/usr/local/etc']


# configuration options common to CLI and Daemon versions. These options
# should appear in BOTH .yaml files
class VyvyanConfigure(object):
    def __init__(self, config_file):
        """
            Takes a config_file name as a parameter and searches through the following
            dirs to load the configuration file:  /etc, CWD
        """
        # Read settings from configuration yaml
        try:
            yaml_config = open(self.load_path(config_file)).read()
            self.all_configs = yaml.load(yaml_config)
        except Exception, e:
            raise ConfigureError("Error loading config file: %s\nConfig search paths: %s\nError: %s" % (config_file, load_paths, e))

        all_configs = self.all_configs
        # general settings
        genconfig = all_configs['general']
        # user to authenticate for 'info' type requests (non-admin/read-only)
        if 'api_info_user' in genconfig and genconfig['api_info_user']:
            self.api_info_user = genconfig['api_info_user']
        else:
            self.api_info_user = 'apicli'
        # pass to authenticate for 'info' type requests (non-admin/read-only)
        if 'api_info_pass' in genconfig and genconfig['api_info_pass']:
            self.api_info_pass = genconfig['api_info_pass']
        # user to authenticate for 'admin' type requests (read-write)
        if 'api_admin_user' in genconfig and genconfig['api_admin_user']:
            self.api_admin_user = genconfig['api_admin_user']
        else:
            self.api_admin_user = 'apicli'
        # pass to authenticate for 'admin' type requests (read-write)
        if 'api_admin_pass' in genconfig and genconfig['api_admin_pass']:
            self.api_admin_pass = genconfig['api_admin_pass']


        # Logging settings
        logconfig = all_configs['logconfig']
        # log directory, default is /var/log/vyvyan
        if 'logdir' in logconfig and logconfig['logdir']:
            self.logdir = logconfig['logdir']
        else:
            self.logdir = '/var/log/vyvyan/'
        # do we log to a file?
        # default is False
        if 'log_to_file' in logconfig and logconfig['log_to_file']:
            self.log_to_file = logconfig['log_to_file']
        else:
            self.log_to_file = False
        # do we log to console? 
        # default is False
        if 'log_to_console' in logconfig and logconfig['log_to_console']:
            self.log_to_console = logconfig['log_to_console']
        else:
            self.log_to_console = False
        # logfile to write our main log to. no default
        if 'logfile' in logconfig and logconfig['logfile']:
            self.logfile = logconfig['logfile']
        else:
            self.logfile = 'vyvyan.log'
        # log level, corresponds to unix syslog priority levels
        # DEBUG, ERROR, WARNING, INFO
        if 'log_level' in logconfig and logconfig['log_level']:
            self.log_level = logconfig['log_level']
        else:
            self.log_level = 'DEBUG'


    def close_connections(self):
        """
            Close out connections
        """
        self.dbconn.close()
        self.dbsess.close()
        self.dbengine.dispose()


    def load_path(self, config_file):
        """
            Try to guess where the path is or return empty string
        """
        for load_path in load_paths:
            file_path = os.path.join(load_path, config_file)
            if os.path.isfile(file_path):
                return file_path
        return ''



# configuration options for the CLI. these options should appear ONLY in
# vyvyan_cli.yaml
class VyvyanConfigureCli(VyvyanConfigure):
    def load_config(self):

        all_configs = self.all_configs

        genconfig = all_configs['general']
        # api server hostname, used to tell the command line where to
        # send REST requests. default is "localhost"
        if 'api_server' in genconfig and genconfig['api_server']:
            self.api_server = genconfig['api_server']
        else:
            self.api_server = 'localhost'
        # api port, used to tell the command line where to send REST
        # requests. default is "8081"
        if 'api_port' in genconfig and genconfig['api_port']:
            self.api_port = genconfig['api_port']
        else:
            self.api_port = '8081'

        logconfig = all_configs['logconfig']
        # audit log filename, default is vyvyan_audit.log
        # logs all command line calls
        if 'audit_log_file' in logconfig and logconfig['audit_log_file']:
            self.audit_log_file = logconfig['audit_log_file']
        else:
            self.audit_log_file = 'vyvyan_audit.log'



# configuration options for the Daemon. these options should appear ONLY
# in vyvyan_daemon.yaml
class VyvyanConfigureDaemon(VyvyanConfigure):
    def load_config(self):
        """
            Takes a config_file name as a parameter and searches through the following
            dirs to load the configuration file:  /etc, CWD
        """
        # module metadata for API module loader
        self.module_metadata = {}
        all_configs = self.all_configs

        # Database related settings
        dbconfig = all_configs['db']
        # try to create a DB engine with sqlalchemy
        try:
            engine = ''
            # PostgreSQL
            if dbconfig['engine'] == 'postgresql':
                dbtuple = (dbconfig['user'], dbconfig['hostname'], dbconfig['dbname'])
                engine = sqlalchemy.create_engine("postgresql://%s@%s/%s" % dbtuple, echo=dbconfig['echo'])
            elif dbconfig['engine'] == 'postgres':
                dbtuple = (dbconfig['user'], dbconfig['hostname'], dbconfig['dbname'])
                engine = sqlalchemy.create_engine("postgres://%s@%s/%s" % dbtuple, echo=dbconfig['echo'])
            # MySql
            elif dbconfig['engine'] == 'mysql':
                dbtuple = (dbconfig['user'], dbconfig['pass'], dbconfig['hostname'], dbconfig['dbname'])
                engine = sqlalchemy.create_engine("mysql://%s:%s@%s/%s" % dbtuple, echo=dbconfig['echo'])
            # uhhhh....
            else:
                raise ConfigureError("DB section of /etc/vyvyan_daemon.yaml is misconfigured! Exiting")
            # now that we have an engine, bind it to a session
            Session = sqlalchemy.orm.sessionmaker(bind=engine)
            dbsession = Session()
            self.dbconfig = dbconfig
            self.dbconn = engine.connect()
            self.dbengine = engine
            self.dbsess = dbsession
            self.dbnull = sqlalchemy.sql.expression.null()
        except Exception, e:
            raise ConfigureError("Database configuration error. dbtuple: %s, engine: %s. Error: %s" % (dbtuple, engine, e))

        # General settings
        genconfig = all_configs['general']
        # our default domain, default is "localhost.localdomain"
        if 'default_domain' in genconfig and genconfig['default_domain']:
            self.default_domain = genconfig['default_domain']
        else:
            self.default_domain = 'localhost.localdomain'
        # main contact, for alerts and such. default is
        # "hostmaster@localhost.localdomain"
        if 'contact' in genconfig and genconfig['contact']:
            self.contact = genconfig['contact']
        else:
            self.contact = 'hostmaster@localhost.localdomain'
        # allow sudo without passwords, default is True
        if 'sudo_nopass' in genconfig and genconfig['sudo_nopass']:
            self.sudo_nopass = genconfig['sudo_nopass']
        else:
            self.sudo_nopass = True

        # Users and Groups settings
        ugconfig = all_configs['users_and_groups']
        # User settings
        # default home parent dir for your users. default is /home
        if 'hdir' in ugconfig and ugconfig['hdir']:
            self.hdir = ugconfig['hdir']
        else:
            self.hdir = '/home'
        # default shell for users, default is /bin/bash
        if 'shell' in ugconfig and ugconfig['shell']:
            self.shell = ugconfig['shell']
        else:
            self.shell = '/bin/bash'
        # lowest UID to start provisioning from. default is 500
        # VYVYAN WILL NOT ALLOW PROVISIONING BELOW THIS
        if 'uid_start' in ugconfig and ugconfig['uid_start']:
            self.uid_start = int(ugconfig['uid_start'])
        else:
            self.uid_start = 500
        # highest UID to provision to. default is 65535
        # VYVYAN WILL NOT ALLOW PROVISIONING BEYOND THIS
        if 'uid_end' in ugconfig and ugconfig['uid_end']:
            self.uid_end = int(ugconfig['uid_end'])
        else:
            self.uid_end = 65535
        # allowed user types. default is "employee, consultant, system"
        if 'user_types' in ugconfig and ugconfig['user_types']:
            self.user_types = ugconfig['user_types']
        else:
            self.user_types = ['employee', 'consultant', 'system']
        # default user type if none is specified on the command line
        # default is "employee"...obviously this should be one of the
        # allowed user types above.
        if 'def_user_type' in ugconfig and ugconfig['def_user_type']:
            self.def_user_type = ugconfig['def_user_type']
        else:
            self.def_user_type = 'employee'
        # Group settings
        # lowest GID to start provisioning from. default is 500
        # VYVYAN WILL NOT ALLOW PROVISIONING BELOW THIS
        if 'gid_start' in ugconfig and ugconfig['gid_start']:
            self.gid_start = int(ugconfig['gid_start'])
        else:
            self.gid_start = 500
        # highest GID to provision to. default is 65535
        # VYVYAN WILL NOT ALLOW PROVISIONING BEYOND THIS
        if 'gid_end' in ugconfig and ugconfig['gid_end']:
            self.gid_end = int(ugconfig['gid_end'])
        else:
            self.gid_end = 65535
        # all users are put into the default groups when the user is
        # created. default is "users"
        if 'default_groups' in ugconfig and ugconfig['default_groups']:
            self.default_groups = ugconfig['default_groups']
        else:
            self.default_groups = ['users',]

        # LDAP settings
        ldconfig = all_configs['ldap']
        # whether to activate the LDAP module. default is False
        if 'active' in ldconfig and ldconfig['active']:
            self.ldap_active = ldconfig['active']
        else:
            self.ldap_active = False
        # ldap OU (organizational unit) for users. default is "users"
        if 'users_ou' in ldconfig and ldconfig['users_ou']:
            self.ldap_users_ou = ldconfig['users_ou']
        else:
            self.ldap_users_ou = 'users'
        # ldap OU (organizational unit) for groups. default is "groups"
        if 'groups_ou' in ldconfig and ldconfig['groups_ou']:
            self.ldap_groups_ou = ldconfig['groups_ou']
        else:
            self.ldap_groups_ou = 'groups'
        # LDAP connection success code.
        # DO NOT CHANGE THIS unless you know what you're doing
        # default is 97
        if 'ldap_success' in ldconfig and ldconfig['ldap_success']:
            self.ldap_success = ldconfig['ldap_success']
        else:
            self.ldap_success = 97
        # Default gidNumber for posixGroup , should match value
        # associated to the first entry of default_groups array
        # default is "500"
        if 'default_gid' in ldconfig and ldconfig['default_gid']:
            self.ldap_default_gid = ldconfig['default_gid']
        else:
            self.ldap_default_gid = '500'
