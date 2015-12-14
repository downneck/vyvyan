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
this module holds methods for dealing with LDAP
this should only, generally speaking, be used to talk with an LDAP server
all user interaction should be done in the vyvyan.API_userdata module
"""

# imports
import os
import ldap
import vyvyan.validate
import vyvyan.API_userdata as userdata

# db imports
from vyvyan.vyvyan_models import *

class LDAPError(Exception):
    pass

def ld_connect(cfg, server):
    """
    [description]
    open a connection to an LDAP server 

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        server: server to connect to

    [return value]
    returns the open ldap connection object 
    """
    try:
      # stitch together some useful info
      admin_dn = "cn=%s,dc=%s" % (cfg.ldap_admin_cn, ',dc='.join(cfg.default_domain.split('.')))
      ld_server_string = "ldaps://"+server

      # init the connection to the ldap server
      ldcon = ldap.initialize(ld_server_string)
      ldcon.simple_bind_s(admin_dn, cfg.ldap_admin_pass)
    except ldap.LDAPError, e:
      cfg.log.debug("error connecting to ldap server: %s" % ldap_master)
      cfg.log.debug("INFO DUMP:\n")
      cfg.log.debug("admin_dn: %s\nld_server_string: %s" % (admin_dn, ld_server_string))
      raise LDAPError(e)

    # we managed to open a connection. return it so it can be useful to others
    return ldcon


def uadd(cfg, user, server=None):
    """
    [description]
    add a user to ldap
    
    [parameter info]
    required:
        cfg: the config object. useful everywhere
        user: the ORM user object
    optional: 
        server: restrict activity to a single server

    [return value]
    returns "success"
    """
    # just checking....
    if user:
        if not user.active:
            raise LDAPError("user %s is not active. please set the user active, first." % user.username)
    else:
        raise LDAPError("empty ORM object passed for user")

    # stitch together the LDAP, fire it into the ldap master server 
    try:
        # construct an array made of the domain parts, stitch it back together in a way
        # that LDAP will understand
        domain_parts = user.domain.split('.')
        dn = "uid=%s,ou=%s,dc=" % (user.username, cfg.ldap_users_ou)
        dn += ',dc='.join(domain_parts)

        add_record = [('objectclass', ['inetOrgPerson','person','ldapPublicKey','posixAccount'])]
        full_name = user.first_name + " " + user.last_name
        if user.ssh_public_key:
            attributes = [('gn', user.first_name),
                          ('sn', user.last_name),
                          ('gecos', full_name),
                          ('cn', full_name),
                          ('uid', user.username),
                          ('uidNumber', str(user.uid)),
                          ('gidNumber', cfg.ldap_default_gid),
                          ('homeDirectory', user.hdir),
                          ('loginShell', user.shell),
                          ('mail', user.email),
                          ('sshPublicKey', user.ssh_public_key),
                         ]
        else:
            attributes = [('gn', user.first_name),
                          ('sn', user.last_name),
                          ('gecos', full_name),
                          ('cn', full_name),
                          ('uid', user.username),
                          ('uidNumber', str(user.uid)),
                          ('gidNumber', cfg.ldap_default_gid),
                          ('homeDirectory', user.hdir),
                          ('loginShell', user.shell),
                          ('mail', user.email),
                         ]
        add_record += attributes

        # connect to ldap server(s) and do stuff
        if server:
          servers = [server]
        else:
          servers = cfg.ldap_servers
    
        for myserver in servers:
            # create a connection to the server 
            ldcon = ld_connect(cfg, myserver)
                print "adding ldap user entry for user %s to domain %s" % (user.username, user.domain)
                ldcon.add_s(dn,add_record)
            except ldap.LDAPError, e:
                # don't leave dangling connections
                ldcon.unbind()
                raise LDAPError(e)
            # close the LDAP connection
            ldcon.unbind()
        # give something back to the community
        return "success" 
    except ldap.LDAPError, e:
        raise LDAPError(e)


def uremove(cfg, user, server=None):
    """
    [description]
    remove a user

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        user: the ORM user object
    optional: 
        server: restrict activity to a single server

    [return value]
    returns "success" 
    """
    # just checking...
    if not user:
        raise LDAPError("empty ORM object passed for user")

    # do the needful
    try:
        # construct an array made of the domain parts, stitch it back together in a way
        # that LDAP will understand
        domain_parts = user.domain.split('.')
        udn = "uid=%s,ou=%s,dc=" % (user.username, cfg.ldap_users_ou)
        udn += ',dc='.join(domain_parts)

        # connect to ldap server(s) and do stuff
        if server:
          servers = [server]
        else:
          servers = cfg.ldap_servers
        for server in cfg.servers:
            # create a connection to the server
            ldcon = ld_connect(cfg, server)
            ldcon.delete_s(udn)
            ldcon.unbind()

        # give something back to the community
        return "success" 
    except ldap.LDAPError, e:
        ldcon.unbind()
        raise LDAPError(e)


def urefresh_all(cfg, server=None):
    """
    [description]
    refresh the LDAP users database. drop all users, add them back in again

    [parameter info]
    required:
        cfg: the config object. useful everywhere
    optional: 
        server: restrict activity to a single server

    [return value]
    returns "success" 
    """
    # some vars we'll need later
    domainlist = []
    ulist = []
    userlist = []

    # do the needful
    try:
        # construct our user list
        for user in cfg.dbsess.query(Users).\
        filter(Users.active==True).all():
            userlist.append(user)
            if user.domain not in domainlist:
                domainlist.append(user.domain)

        # suss out the server situation
        if server:
            servers = [server]
        else:
            servers = cfg.ldap_servers

        # connect to ldap server(s) and do stuff
        for myserver in servers:
            for domain in domainlist:
                # make an array of the domain parts. stitch it back together in a way
                # ldap will understand
                domain_parts = domain.split('.')
                udn ="ou=%s,dc=" % cfg.ldap_users_ou
                udn += ',dc='.join(domain_parts)

                # create a connection to the server
                ldcon = ld_connect(cfg, myserver)
                search = '(objectClass=person)'

                # ALL USERS BALEETED
                for result in ldcon.search_s(udn, ldap.SCOPE_SUBTREE, search):
                    ldcon.delete_s(result[0])

                # unbind thyself
                ldcon.unbind()

                # add the users back in
                for user in userlist:
                    uadd(cfg, user, server=myserver)

        # give something back to the community
        return "success" 

    # something horrible has happened.
    except ldap.LDAPError, e:
        ldcon.unbind()
        raise LDAPError(e)


# we may get rid of this completely...
def uupdate(cfg, user, server=None):
    """
    [description]
    update a user entry

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        user: the ORM user object
    optional: 
        server: restrict activity to a single server

    [return value]
    no explicit return 
    """
    try:
        # construct an array made of the domain parts, stitch it back together in a way
        # that LDAP will understand
        domain_parts = user.domain.split('.')
        dn = "uid=%s,ou=%s,dc=" % (user.username, cfg.ldap_users_ou)
        dn += ',dc='.join(domain_parts)
    
        # we only really care about active users
        if not user.active:
            raise LDAPError("user %s is not active. please set the user active, first." % u.username)
    
        # connect ldap server(s) and do stuff
        if server:
            servers = [server]
        else:
            servers = cfg.ldap_servers

        # stitch together the LDAP, fire it into the ldap master server 
        full_name = user.first_name + " " + user.last_name
        if user.ssh_public_key:
            mod_record = [(ldap.MOD_REPLACE, 'gn', user.first_name),
                          (ldap.MOD_REPLACE, 'sn', user.last_name),
                          (ldap.MOD_REPLACE, 'gecos', full_name),
                          (ldap.MOD_REPLACE, 'cn', full_name),
                          (ldap.MOD_REPLACE, 'uidNumber', str(user.uid)),
                          (ldap.MOD_REPLACE, 'gidNumber', cfg.ldap_default_gid),
                          (ldap.MOD_REPLACE, 'homeDirectory', user.hdir),
                          (ldap.MOD_REPLACE, 'loginShell', user.shell),
                          (ldap.MOD_REPLACE, 'mail', user.email),
                          (ldap.MOD_REPLACE, 'sshPublicKey', user.ssh_public_key),
                         ]
        else:
            mod_record = [(ldap.MOD_REPLACE, 'gn', user.first_name),
                          (ldap.MOD_REPLACE, 'sn', user.last_name),
                          (ldap.MOD_REPLACE, 'gecos', full_name),
                          (ldap.MOD_REPLACE, 'cn', full_name),
                          (ldap.MOD_REPLACE, 'uidNumber', str(user.uid)),
                          (ldap.MOD_REPLACE, 'gidNumber', cfg.ldap_default_gid),
                          (ldap.MOD_REPLACE, 'homeDirectory', user.hdir),
                          (ldap.MOD_REPLACE, 'loginShell', user.shell),
                          (ldap.MOD_REPLACE, 'mail', user.email),
                         ]

        # do the needful, once for each server in the array 
        for myserver in servers:

            # create a connection to the server
            ldcon = ld_connect(cfg, myserver)
                print "updating ldap user entry for user %s on domain %s" % (user.username, user.domain)
                ldcon.modify_s(dn, mod_record)

            # close the LDAP connection
            ldcon.unbind()

        # give something back to the community
        return "success"

    except ldap.LDAPError, e:
        ldcon.unbind()
        raise LDAPError(e)


def gadd(cfg, group, server=None):
    """
    [description]
    add a group

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        group: the ORM group object
    optional: 
        server: restrict activity to a single server

    [return value]
    returns "success"
    """
    try:
        if group:
            # construct an array made of the domain parts, stitch it back together in a way
            # that LDAP will understand to create our group
            domain_parts = group.domain.split('.')
            gdn = "cn=%s,ou=%s,dc=" % (group.groupname, cfg.ldap_groups_ou)
            gdn += ',dc='.join(domain_parts)
            ngdn = "cn=%s,ou=%s,dc=" % (group.groupname, cfg.ldap_netgroups_ou)
            ngdn += ',dc='.join(domain_parts)

            # construct the list of users in this group three ways
            # ACHTUNG: we may not need both memberlist and memberoflist. test this!
            memberoflist = [] # groupOfNames stylee
            memberlist = [] # posixGroup steez
            netgrouplist = [] # nisNetgroups are still a thing?
            # iterate over all users assigned to this group
            for ugmap in cfg.dbsess.query(UserGroupMapping).\
                    filter(UserGroupMapping.groups_id==group.id):
                user = cfg.dbsess.query(Users).\
                filter(Users.id==ugmap.users_id).first()
                # construct the memberOf list for groupOfNames
                memberoflist.append(user.username)
                # construct the member list for posixGroup
                ldap_user_dn = "uid=%s,ou=%s,dc=" % (user.username, cfg.ldap_groups_ou)
                ldap_user_dn += ',dc='.join(domain_parts)
                memberlist.append(ldap_user_dn)
                # construct the netgroup list for nisNetgroup
                netgrouplist.append("(-,%s,)" % user.username)
        else:
            raise LDAPError("group object not supplied, aborting")
    
        # connect ldap server(s) and do stuff
        if server:
            servers = [server]
        else:
            servers = cfg.ldap_servers
    
        for myserver in servers:
            # construct the Group record to add 
            g_add_record = [('objectClass', ['top', 'posixGroup', 'groupOfNames'])]
            if memberoflist:
                g_attributes = [('description', group.description),
                               ('cn', group.groupname),
                               ('gidNumber', str(group.gid)),
                               ('memberUid', memberoflist),
                               ('member', memberlist),
                              ]
            else:
                g_attributes = [('description', group.description),
                               ('cn', group.groupname),
                               ('gidNumber', str(group.gid)),
                              ]

            # construct the nisNetgroup record to add 
            g_add_record = [('objectClass', ['top', 'nisNetgroup'])]
            if netgrouplist:
                ng_attributes = [('description', group.description),
                               ('cn', group.groupname),
                               ('nisNetgroupTriple', netgrouplist),
                              ]
            else:
                ng_attributes = [('description', group.description),
                               ('cn', group.groupname),
                              ]

            # stitch the records together
            g_add_record += g_attributes
            ng_add_record += ng_attributes

            # create a connection to the ldap server
            ldcon = ld_connect(cfg, myserver)
   
            # talk about our feelings
            print "adding ldap Group record for %s" % (gdn)
            print "adding ldap nisNetgroup record for %s" % (ngdn)

            # slam the records into the server
            ldcon.add_s(gdn, g_add_record)
            ldcon.add_s(ngdn, ng_add_record)
            ldcon.unbind()
    
        # give something back to the community
        return "success"

    except ldap.LDAPError, e:
        ldcon.unbind()
        raise LDAPError(e)


def gupdate(cfg, group, server=None):
    """
    [description]
    update a group

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        group: the ORM group object
    optional: 
        server: restrict activity to a single server

    [return value]
    returns "success"
    """
    try:
        if group:
            # construct an array made of the domain parts, stitch it back together in a way
            # that LDAP will understand to create our group
            domain_parts = group.domain.split('.')
            gdn = "cn=%s,ou=%s,dc=" % (group.groupname, cfg.ldap_groups_ou)
            gdn += ',dc='.join(domain_parts)
            ngdn = "cn=%s,ou=%s,dc=" % (group.groupname, cfg.ldap_netgroups_ou)
            ngdn += ',dc='.join(domain_parts)

            # construct the list of users in this group three ways
            # ACHTUNG: we may not need both memberlist and memberoflist. test this!
            memberoflist = [] # groupOfNames stylee
            memberlist = [] # posixGroup steez
            netgrouplist = [] # nisNetgroups are still a thing?
            # iterate over all users assigned to this group
            for ugmap in cfg.dbsess.query(UserGroupMapping).\
                    filter(UserGroupMapping.groups_id==group.id):
                user = cfg.dbsess.query(Users).\
                filter(Users.id==ugmap.users_id).first()
                # construct the memberOf list for groupOfNames
                memberoflist.append(user.username)
                # construct the member list for posixGroup
                ldap_user_dn = "uid=%s,ou=%s,dc=" % (user.username, cfg.ldap_groups_ou)
                ldap_user_dn += ',dc='.join(domain_parts)
                memberlist.append(ldap_user_dn)
                # construct the netgroup list for nisNetgroup
                netgrouplist.append("(-,%s,)" % user.username)
        else:
            raise LDAPError("group object not supplied, aborting")
    
        # connect ldap server(s) and do stuff
        if server:
            servers = [server]
        else:
            servers = cfg.ldap_servers
   
        for myserver in servers:
            # construct the Group record to add 
            if memberoflist:
                g_attributes = [(ldap.MOD_REPLACE, 'description', group.description),
                                (ldap.MOD_REPLACE, 'gidNumber', str(group.gid)),
                                (ldap.MOD_REPLACE, 'memberUid', memberoflist),
                                (ldap.MOD_REPLACE, 'member', memberlist),
                               ]
            else:
                g_attributes = [(ldap.MOD_REPLACE, 'description', group.description),
                                (ldap.MOD_REPLACE, 'gidNumber', str(group.gid)),
                               ]

            # construct the nisNetgroup record to add 
            if netgrouplist:
                ng_attributes = [(ldap.MOD_REPLACE, 'description', group.description),
                                 (ldap.MOD_REPLACE, 'nisNetgroupTriple', netgrouplist),
                               ]
            else:
                ng_attributes = [(ldap.MOD_REPLACE, 'description', group.description),
                               ]

            # create a connection to the ldap server
            ldcon = ld_connect(cfg, myserver)
   
            # talk about our feelings
            print "updating ldap Group record for %s" % (gdn)
            print "updating ldap nisNetgroup record for %s" % (ngdn)

            # slam the records into the server
            ldcon.modify_s(gdn, g_attributes)
            ldcon.modify_s(ngdn, ng_attributes)
            ldcon.unbind()
    
        # give something back to the community
        return "success"

    except ldap.LDAPError, e:
        ldcon.unbind()
        raise LDAPError(e)


def gremove(cfg, group, server=None):
    """
    [description]
    remove a group

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        group: the ORM group object
    optional: 
        server: restrict activity to a single server

    [return value]
    returns "success"
    """
    try:
        if group:
            # construct an array made of the domain parts, stitch it back together in a way
            # that LDAP will understand to create our group
            domain_parts = group.domain.split('.')
            gdn = "cn=%s,ou=%s,dc=" % (group.groupname, cfg.ldap_groups_ou)
            gdn += ',dc='.join(domain_parts)
            ngdn = "cn=%s,ou=%s,dc=" % (group.groupname, cfg.ldap_netgroups_ou)
            ngdn += ',dc='.join(domain_parts)
        else:
            raise LDAPError("group object not supplied, aborting")
    
        # connect ldap server(s) and do stuff
        if server:
            servers = [server]
        else:
            servers = cfg.ldap_servers
   
        for myserver in servers:
            # create a connection to the ldap server
            ldcon = ld_connect(cfg, myserver)
   
            # talk about our feelings
            print "removing ldap Group record for %s" % (gdn)
            print "removing ldap nisNetgroup record for %s" % (ngdn)

            # slam the records into the server
            ldcon.delete_s(gdn)
            ldcon.delete_s(ngdn)
            ldcon.unbind()
    
        # give something back to the community
        return "success"

    except ldap.LDAPError, e:
        ldcon.unbind()
        raise LDAPError(e)


def grefresh_all(cfg, server=None):
    """
    [description]
    refresh the LDAP groups database. drop all groups, add them back in again

    [parameter info]
    required:
        cfg: the config object. useful everywhere
    optional: 
        server: restrict activity to a single server

    [return value]
    returns "success" 
    """
    # some vars we'll need later
    domainlist = []
    glist = []
    nglist = []
    grouplist = []

    # do the needful
    try:
        # construct our group list
        for group in cfg.dbsess.query(Groups).all()
            grouplist.append(group)
            if group.domain not in domainlist:
                domainlist.append(group.domain)

        # suss out the server situation
        if server:
            servers = [server]
        else:
            servers = cfg.ldap_servers

        # connect to ldap server(s) and do stuff
        for myserver in servers:
            for domain in domainlist:
                # make an array of the domain parts. stitch it back together in a way
                # ldap will understand
                domain_parts = domain.split('.')
                gdn ="ou=%s,dc=" % cfg.ldap_groups_ou
                gdn += ',dc='.join(domain_parts)
                ngdn ="ou=%s,dc=" % cfg.ldap_netgroups_ou
                ngdn += ',dc='.join(domain_parts)

                # create a connection to the server
                ldcon = ld_connect(cfg, myserver)

                # ALL GROUPS BALEETED
                search = '(objectClass=posixGroup)'
                for result in ldcon.search_s(gdn, ldap.SCOPE_SUBTREE, search):
                    ldcon.delete_s(result[0])

                # ALL NETGROUPS BALEETED 
                search = '(objectClass=nisNetgroup)'
                for result in ldcon.search_s(ngdn, ldap.SCOPE_SUBTREE, search):
                    ldcon.delete_s(result[0])

                # unbind thyself
                ldcon.unbind()

                # add the groups back in
                for group in grouplist:
                    gadd(cfg, group, server=myserver)

        # give something back to the community
        return "success" 

    # something horrible has happened.
    except ldap.LDAPError, e:
        ldcon.unbind()
        raise LDAPError(e)


def ldapimport(cfg, domain=None, server=None):
    """
    [description]
    import ldap data into vyvyan (DANGEROUS)
    in fact this is so dangerous, i'm leaving
    it unlinked for the moment. will need a LOT
    more sanity checking before it can be allowed
    into service

    [parameter info]
    required:
        cfg: the config object. useful everywhere
    optional:
        domain: just import a single domain's worth of userdata
        server: manually set the server to import from. leaving blank will pick from your configured list.

    [return value]
    returns "success"
    """
    # some vars we'll need later
    domainlist = []
    grouplist = {}
    netgrouplist = {}
    userlist = {}
    

    # check to see if groups or users tables are populated already. if so, bail out.
    # we don't want to overwrite information already in vyvyan's database.
    try:
        if len(cfg.dbsess.query(Groups).all()) > 0 or len(cfg.dbsess.query(Users).all()) > 0:
            raise LDAPError("Refusing to import into a populated database")

        # suss out the server situation
        if not server:
            server = cfg.ldap_servers[0]

        # suss out the domain situation
        if not domain:
            # connect to ldap server and grab a list of all domains (ie. namingContext) 
            ldcon = ld_connect(cfg, server)
            search_filter = '(objectClass=namingContext)'
            for result in ldcon.search_s('', ldap.SCOPE_BASE, search_filter, None):
                # i kind of don't know that this will work. hopeful though.
                # turn 'dc=' notation into a regular dotted domain
                domainlist.append(result[1].replace(',dc=', '.').replace('dc=', ''))
            ldcon.unbind()
        else:
            domainlist = [domain]

        # iterate over discovered domains
        for domain in domainlist:
            # validate the thing to make sure we didn't get something insane
            v_domain(domain)

            # add the domain to the grouplist and userlist
            grouplist[domain] = [] 
            netgrouplist[domain] = [] 
            userlist[domain] = [] 
            sudoerslist[domain] = [] 

            # make an array of the domain parts. stitch it back together in a way
            # ldap will understand
            # users dn
            domain_parts = domain.split('.')
            udn ="ou=%s,dc=" % cfg.ldap_users_ou
            udn += ',dc='.join(domain_parts)
            # groups dn
            gdn ="ou=%s,dc=" % cfg.ldap_groups_ou
            gdn += ',dc='.join(domain_parts)
            # netgroups dn
            ngdn ="ou=%s,dc=" % cfg.ldap_netgroups_ou
            ngdn += ',dc='.join(domain_parts)
            # sudoers dn
            sdn ="ou=%s,dc=" % cfg.ldap_sudoers_ou
            sdn += ',dc='.join(domain_parts)

            
            # connect to ldap server and do stuff
            ldcon = ld_connect(cfg, server)

            # first, harvest groups
            # don't know that we need this. keeping it here for posterity
            #attr = ['memberUid', 'gidNumber', 'description', 'cn']
            for result in ldcon.search_s(gdn, ldap.SCOPE_SUBTREE, '(objectClass=posixGroup)', None):
                if result[1]:
                    grouplist[domain].append(result[1])

            # next, harvest netgroups
            # TODO: do we need these?
            for result in ldcon.search_s(ngdn, ldap.SCOPE_SUBTREE, '(objectClass=nisNetgroup)', None):
                if result[1]:
                    netgrouplist[domain].append(result[1])

            # next, harvest users
            for result in ldcon.search_s(udn, ldap.SCOPE_SUBTREE, '(objectClass=posixAccount)', None):
                if result[1]:
                    userlist[domain].append(result[1])

            # finally, harvest sudoers info
            for result in ldcon.search_s(sdn, ldap.SCOPE_SUBTREE, '(objectClass=sudoRole)', None):
                if result[1]:
                    sudoerslist[domain].append(result[1])

            # clean up after ourselves
            ldcon.unbind()

            # need to do a bunch of parsing and re-arranging of sudoers to hopefully
            # figure out what group needs what sudo commands and suchlike
            sudoergrouplist = {}
            sudoeruserlist = {}
            for sudoer in sudoerslist[domain]:
                if sudoer['sudoUser']:
                    for entry in sudoer['sudoUser']:
                        if '%' in entry:
                            sudoergrouplist[entry.replace('%', '')] = {'sudoHost': sudoer['sudoHost'], 'sudoCommand': sudoer['sudoCommand']}
                        else:
                            sudoeruserlist[entry.replace('%', '')] = {'sudoHost': sudoer['sudoHost'], 'sudoCommand': sudoer['sudoCommand']}

            # create our groups first
            # TODO: figure out how to deal with sudo structure 
            # TODO: figure out how to inject SSHA passwords into the db
            for domain in grouplist.keys():
                for group in grouplist[domain]:
                    query = {'domain': domain,
                             'groupname': group['cn'],
                             'gid': group['gidNumber'],
                             'description': group['description'],
                             'sudo_cmds': '',
                            }
                    userdata.gadd(cfg, query)

                    # if this domain has users, make 'em.
                    if domain in userlist.keys():
                        for user in userlist[domain]:
                            query = {'username', user['uid'],
                                     'uid', user['uidNumber'],
                                    }
                            if 'gn' in user and user['gn']:
                                query['first_name'] = user['gn']
                            if 'sn' in user and user['sn']:
                                query['last_name'] = user['sn']
                            if 'homeDirectory' in user and user['homeDirectory']:
                                query['hdir'] = user['homeDirectory']
                            if 'loginShell' in user and user['loginShell']:
                                query['shell'] = user['loginShell']
                            if 'mail' in user and user['mail']:
                                query['email'] = user['mail']

                    #TODO: figure out ssh keys

                    #TODO: add users to groups with utog


#MARK
# this shit ain't nearly done




                        # fetch user info from ldap, stuff into new
                        # user, map user into group
                        dn = "uid=%s,ou=%s,dc=" % (user, cfg.ldap_users_ou)
                        dn += ',dc='.join(d)
                        search = '(objectClass=person)'
                        print "fetching user data for: %s" % dn
                        try:
                            result = ldcon.search_s(dn, ldap.SCOPE_BASE, search)
                        except ldap.LDAPError, e:
                            print "Entity not found, skipping."
                            print e
                            result = False
                        if result:
                            print "user \"%s\" does not exist, creating from ldap info and mapping into group \"%s\"" % (user+'.'+fqn, groupname+'.'+fqn)
                            # pull the user data out of the ldap schema
                            username = result[0][1]['uid'][0]
                            if result[0][1]['sshPublicKey']:
                                # THIS SHOULD USE THE LIST VERSION, NOT A SINGLE MEMBER
                                # in case they have multiple keys
                                ssh_public_key = result[0][1]['sshPublicKey'][0]
                            else:
                                ssh_public_key = None
                            uid = result[0][1]['uidNumber'][0]
                            first_name, last_name = result[0][1]['gecos'][0].split(None, 1)
                            hdir = result[0][1]['homeDirectory'][0]
                            shell = result[0][1]['loginShell'][0]
                            email = result[0][1]['mail'][0]
                            # ldap doesn't store user type data so
                            # use the default type
                            user_type = cfg.def_user_type
                            # create a new user object and fire it into
                            # the db, face first.
                            u = Users(first_name, last_name, ssh_public_key, username, site_id, realm, uid, user_type, hdir, shell, email, True)
                            cfg.dbsess.add(u)
                            cfg.dbsess.commit()
                            # map the user we just created into the
                            # group we're currently operating on
                            ugmap = UserGroupMapping(g.id, u.id)
                            cfg.dbsess.add(ugmap)
                            cfg.dbsess.commit()
                        else:
                            print "User \"%s\" not created. The user is in a group in LDAP but does not actually exist in LDAP.\nMost likely this is a system user (such as \"nobody\" or \"apache\") that should not exist in LDAP." % user
        # if the group doesn't exist, create it then map any users it
        # may have into the vyvyan group definition
        else:
            groupname = result[1]['cn'][0]
            print "group \"%s\" does not exist, creating from ldap info" % (groupname+'.'+fqn)
            description = result[1]['description']
            gid = int(result[1]['gidNumber'][0])
            g = Groups(description, groupname, site_id, realm, gid)
            cfg.dbsess.add(g)
            cfg.dbsess.commit()
            if userlist:
                for user in userlist:
                    u = vyvyan.validate.v_get_user_obj(cfg, user+'.'+fqn)
                    if u:
                        print "mapping user \"%s\" into group \"%s\"" % (u.username+'.'+fqn, groupname+'.'+fqn)
                        ugmap = UserGroupMapping(g.id, u.id)
                        cfg.dbsess.add(ugmap)
                        cfg.dbsess.commit()
                    else:
                        # fetch user info from ldap, stuff into new
                        # user, map user into group
                        dn = "uid=%s,ou=%s,dc=" % (user, cfg.ldap_users_ou)
                        dn += ',dc='.join(d)
                        search = '(objectClass=person)'
                        try:
                            result = ldcon.search_s(dn, ldap.SCOPE_BASE, search)
                        except ldap.LDAPError, e:
                            print "Entity not found, skipping."
                            print e
                            result = False
                        if result:
                            # pull the user data out of the ldap schema
                            username = result[0][1]['uid'][0]
                            print "user \"%s\" does not exist, creating from ldap info and mapping into group \"%s\"" % (username+'.'+fqn, groupname+'.'+fqn)
                            if result[0][1]['sshPublicKey']:
                                ssh_public_key = result[0][1]['sshPublicKey'][0]
                            else:
                                ssh_public_key = None
                            uid = result[0][1]['uidNumber'][0]
                            first_name, last_name = result[0][1]['gecos'][0].split(None, 1)
                            hdir = result[0][1]['homeDirectory'][0]
                            shell = result[0][1]['loginShell'][0]
                            email = result[0][1]['mail'][0]
                            # ldap doesn't store user type data so
                            # use the default type
                            user_type = cfg.def_user_type
                            # create a new user object and fire it into
                            # the db, face first.
                            u = Users(first_name, last_name, ssh_public_key, username, site_id, realm, uid, user_type, hdir, shell, email, True)
                            cfg.dbsess.add(u)
                            cfg.dbsess.commit()
                            # map the user we just created into the
                            # group we're currently operating on
                            ugmap = UserGroupMapping(g.id, u.id)
                            cfg.dbsess.add(ugmap)
                            cfg.dbsess.commit()
                        else:
                            print "User \"%s\" not created. The user is in a group in LDAP but does not actually exist in LDAP.\nMost likely this is a system user (such as \"nobody\" or \"apache\") that should not exist in LDAP." % user
    # now that we're done with the groups, let's go back in and make
    # sure we create any leftover users that weren't in a group
    dn = "ou=%s,dc=" % cfg.ldap_users_ou
    dn += ',dc='.join(d)
    search = '(objectClass=person)'
    try:
        results = ldcon.search_s(dn, ldap.SCOPE_BASE, search)
    except ldap.LDAPError, e:
        print "Entity not found, skipping."
        print e
        results = False
    if results:
        for result in results:
            username = result[0][1]['uid'][0]
            u = vyvyan.validate.v_get_user_obj(cfg, username+'.'+fqn)
            if u:
                print "user exists, skipping"
            else:
                # create a new user object and fire it into
                # the db, face first.
                print "user \"%s\" does not exist, creating from ldap info" % (username+'.'+fqn)
                if result[0][1]['sshPublicKey']:
                    ssh_public_key = result[0][1]['sshPublicKey'][0]
                else:
                    ssh_public_key = None
                uid = result[0][1]['uidNumber'][0]
                first_name, last_name = result[0][1]['gecos'][0].split(None, 1)
                hdir = result[0][1]['homeDirectory'][0]
                shell = result[0][1]['loginShell'][0]
                email = result[0][1]['mail'][0]
                # ldap doesn't store user type data so
                # use the default type
                user_type = cfg.def_user_type
                u = Users(first_name, last_name, ssh_public_key, username, site_id, realm, uid, user_type, hdir, shell, email, True)
                cfg.dbsess.add(u)
                cfg.dbsess.commit()
                # map the user we just created into the
                # group we're currently operating on
                ugmap = UserGroupMapping(g.id, u.id)
                cfg.dbsess.add(ugmap)
                cfg.dbsess.commit()
    else:
        print "No users found!"









# ACHTUNG! bits below here may be useful. they will probably need to be moved into userdata

def password_prompt(minchars, enctype):
    import getpass
    import hashlib
    from base64 import encodestring as encode
    ans1 = getpass.getpass("Enter new passwd:")
    if len(ans1) < minchars:
        print 'Password is too short!  Must be at least %d char(s)' % minchars
        return
    ans2 = getpass.getpass("Re-type new passwd:")
    if ans1 != ans2:
        print 'Passwords do not match!'
        return
    salt = os.urandom(4)
    h = eval('hashlib.%s(ans1)' % enctype)
    h.update(salt)
    return '{SSHA}' + encode(h.digest() + salt)[:-1]

def update_ldap_passwd(cfg, username):
    u = vyvyan.validate.v_get_user_obj(cfg, username)
    d = cfg.domain.split('.')
    if u:
        ldap_master = __get_master(cfg, u.realm+'.'+u.site_id)
        dn = "uid=%s,ou=%s,dc=" % (u.username, cfg.ldap_users_ou)
        dn += ',dc='.join(d)
    else:
        raise LDAPError("user \"%s\" not found, aborting" % username)
    ldcon = ld_connect(cfg, ldap_master)
    try:
        raw_res = ldcon.search_s(dn, ldap.SCOPE_BASE)
        if 'userPassword' in raw_res[0][1].keys():
            print 'User %s ALREADY has LDAP password set' % u.username
        else:
            print 'User %s does NOT have LDAP password set' % u.username
        newpass = password_prompt(8,'sha1')
        try:
            ldcon.modify_s(dn, [(ldap.MOD_REPLACE, 'userPassword', newpass)])
        except ldap.LDAPError, e:
            raise LDAPError(e)
        ldcon.unbind()
    except ldap.LDAPError, e:
        raise LDAPError(e)


