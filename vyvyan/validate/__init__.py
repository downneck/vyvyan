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
vyvyan.validate

a library of validation methods
for various types of data
"""

# imports
import base64
import struct
import types
import re

# All of the models and sqlalchemy are brought in
# to simplify referencing
from vyvyan.vyvyan_models import *

class ValidationError(Exception):
    pass

# Validates domain input data
def v_domain(domain):
    """
    [description]
    validates domain input data (probably not necessary)

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        domain: the domain we're trying to validate

    [return value]
    True/False based on success of validation
    """
    # TODO: write some actual validation
    return True
    

# Validates ssh2 pubkeys
def v_ssh2_pubkey(key):
    """
    [description]
    validates ssh2 public keys

    [parameter info]
    required:
        key: the ssh2 public key we're trying to validate

    [return value]
    True/Exception based on success of validation
    """
    try:
        DSA_KEY_ID="ssh-dss"
        RSA_KEY_ID="ssh-rsa"
    
        if re.match(DSA_KEY_ID+'|'+RSA_KEY_ID, key):
            k = key.split(' ')
        else:
            raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key)
    
        if k:
            try:
                data = base64.decodestring(k[1])
            except IndexError:
                raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key)
            int_len = 4
            str_len = struct.unpack('>I', data[:int_len])[0] # this should return 7
            if DSA_KEY_ID in key:
              if data[int_len:int_len+str_len] == DSA_KEY_ID:
                  return True
              else:
                  raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key) 
            else:
                if data[int_len:int_len+str_len] == RSA_KEY_ID:
                  return True
                else:
                  raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key)
        else:
           raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key) 
    except Exception, e:
        raise ValidationError("validate/v_ssh2_pubkey: invalid ssh2 key: %s" % key)

# Validates UNIX uids
def v_uid(cfg, uid):
    """
    [description]
    validates UNIX UIDs

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        uid: the UID we're trying to validate

    [return value]
    True/False based on success of validation
    """

    if type(uid) == types.IntType:
        if uid >= cfg.uid_start and uid <= cfg.uid_end:
            return True
        else:
            cfg.log.debug("UID is outside the allowed range (%s to %s)" % (cfg.uid_start, cfg.uid_end))
            raise ValidationError("UID is outside the allowed range (%s to %s)" % (cfg.uid_start, cfg.uid_end))
    elif uid == None:
        cfg.log.debug("UID is empty!")
        raise ValidationError("UID is empty!")
    else:
        cfg.log.debug("UID must be an integer!")
        raise ValidationError("UID must be an integer!")

# Looks for a UID in the db and returns true if present, false if absent
def v_uid_in_db(cfg, uid, domain=None):
    """
    [description]
    looks for a UID in the db

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        uid: the UID we're trying to find
    optional:
        domain: the domain to look in

    [return value]
    True/False based on success of validation
    """
    # make sure we're within operational parameters
    v_uid(cfg, uid)
    uidlist = []
    # go get our list
    u = cfg.dbsess.query(Users).\
        filter(Users.realm==realm).\
        filter(Users.site_id==site_id).all()
    # put em in a list
    for userentry in u:
        uidlist.append(userentry.uid)
    # finally, check 'em
    uid_set = set(uidlist)
    if uid in uid_set:
        return True
    else:
        return False

# Looks for a GID in the db and returns true if present, false if absent
def v_gid_in_db(cfg, gid, domain=None):
    """
    [description]
    looks for a GID in the db

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        gid: the GID we're looking for
    optional:
        domain: the domain to look in 

    [return value]
    True/False based on success of validation
    """
    # make sure we're within operational parameters
    v_gid(cfg, gid)
    gidlist = []
    # go get our list
    if domain:
        g = cfg.dbsess.query(Groups).\
            filter(Groups.domain==domain).all()
    else:
        g = cfg.dbsess.query(Groups).all()
    # put em in a list
    for groupentry in g:
        gidlist.append(groupentry.gid)
    # finally, check 'em
    gid_set = set(gidlist)
    if gid in gid_set:
        return True
    else:
        return False

# Validates UNIX gids
def v_gid(cfg, gid):
    """
    [description]
    validates UNIX GIDs

    [parameter info]
    required:
        cfg: the config object. useful everywhere
        gid: the GID we're trying to validate

    [return value]
    True/False based on success of validation
    """

    if type(gid) == types.IntType:
        if gid >= cfg.gid_start and gid <= cfg.gid_end:
            return True
        else:
            cfg.log.debug("GID is outside the allowed range (%s to %s)" % (cfg.gid_start, cfg.gid_end))
            raise ValidationError("GID is outside the allowed range (%s to %s)" % (cfg.gid_start, cfg.gid_end))
    elif gid == None:
        cfg.log.debug("GID is empty") 
        raise ValidationError("GID is empty") 
    else:
        cfg.log.debug("GID must be an integer! GID: %s" % gid)
        raise ValidationError("GID must be an integer! GID: %s" % gid)


# VERY basic validation of user- group- or host-name input
def v_name(name):
    """
    [description]
    VERY basic validation of user- group- or host-name input
    """

    if not name:
        raise ValidationError('v_name() called without a name!')
    if re.search("[^A-Za-z0-9_\-.]", name):
        raise ValidationError('name contains illegal characters! allowed characters are: A-Z a-z 0-9 _ - .')
    if len(name) < 1:
        raise ValidationError('too short! name must have more than 1 character')
    return True
