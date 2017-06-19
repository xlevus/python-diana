#!/usr/bin/env python

import os
from setuptools import setup


setup(
    name='diana',
    version='0.0.2',
    description='Simple Dependency Injector for python',
    long_description='',
    author='Chris Targett',
    author_email='chris@xlevus.net',
    url='http://github.com/xlevus/diana',
    packages=['diana'],
    tests_require=['pytest', 'mock'],
)
