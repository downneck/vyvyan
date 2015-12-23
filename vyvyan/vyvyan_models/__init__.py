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
vyvyan's ORM
"""

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation, backref

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    first_name = Column(String)
    last_name = Column(String)
    ssh_public_key = Column(String)
    password = Column(String)
    username = Column(String, primary_key=True)
    domain = Column(String, primary_key=True)
    uid = Column(Integer)
    id = Column(Integer, primary_key=True)
    type = Column(String)
    hdir = Column(String)
    shell = Column(String)
    email = Column(String)
    active = Column(Boolean, server_default='true')

    def __init__(self, first_name, last_name, ssh_public_key, password, username, domain, uid, type, hdir, shell, email, active):
        self.first_name = first_name
        self.last_name = last_name
        self.ssh_public_key = ssh_public_key
        self.password = password
        self.username = username
        self.domain = domain
        self.uid = uid
        self.type = type
        self.hdir = hdir
        self.shell = shell
        self.email = email
        self.active = active

    def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

    def __repr__(self):
        return "<Users('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')>" % (self.first_name, self.last_name, self.ssh_public_key, self.username, self.domain, self.uid, self.type, self.hdir, self.shell, self.email, self.active)


class Groups(Base):
    __tablename__ = 'groups'

    description = Column(String)
    groupname = Column(String, primary_key=True)
    domain = Column(String, primary_key=True)
    gid = Column(Integer)
    id = Column(Integer, primary_key=True)

    def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

    def __init__(self, description, groupname, domain, gid):
        self.description = description
        self.groupname = groupname
        self.domain = domain
        self.gid = gid

    def __repr__(self):
        return "<Groups('%s', '%s', '%s', '%s')>" % (self.description, self.groupname, self.domain, self.sudo_cmds)


class UserGroupMapping(Base):
    __tablename__ = 'user_group_mapping'

    groups_id = Column(Integer, ForeignKey(Groups.id))
    users_id = Column(Integer, ForeignKey(Users.id))
    id = Column(Integer, primary_key=True)

    def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

    def __init__(self, groups_id, users_id):
        self.groups_id = groups_id
        self.users_id = users_id

    def __repr__(self):
        return "<UserGroupMapping('%s', '%s')>" % (self.groups_id, self.users_id)

class GroupSudocommandMapping(Base):
    __tablename__ = 'group_sudocommand_mapping'

    groups_id = Column(Integer, ForeignKey(Groups.id))
    sudocommand = Column(String)
    id = Column(Integer, primary_key=True)

    def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

    def __init__(self, groups_id, sudocommand):
        self.groups_id = groups_id
        self.sudocommand = sudocommand

    def __repr__(self):
        return "<UserGroupMapping('%s', '%s')>" % (self.groups_id, self.users_id)
