#!/usr/bin/python

import setuptools
from setuptools import setup,  find_packages

install_requires = [
    'cmdln',
    'python-ldap',
    'SQLAlchemy == 0.5.5'
    ]

setup(name='vyvyan',
      author='david kovach',
      author_email='dave@devopsadvice.com',
      description='vyvyan helps you manage users',
      install_requires = install_requires,
      extras_require = extras_require,
      packages=find_packages(),
      scripts=['vyv'],
      url='https://www.devopsadvice.com',
      version='0.0.1',
     )
