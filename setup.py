#!/usr/bin/env python

from setuptools import setup


def read_init_var(name):
    prefix = '%s = ' % (name,)
    with open('diana/__init__.py') as f:
        for line in f:
            if line.startswith(prefix):
                return line.replace(prefix, '').strip().strip("'")
    raise AssertionError('variable %s not found' % (name,))

version = read_init_var('__version__')

long_desc = open('README.rst', 'r').read()


setup(
    name='diana',
    version=version,
    description='Simple Dependency Injector for python',
    long_description=long_desc,
    author='Chris Targett',
    author_email='chris@xlevus.net',
    url='http://github.com/xlevus/python-diana',
    packages=['diana'],
    license='MIT',
    python_requires=">3.4.*, <4",
    tests_require=['pytest', 'mock'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'],
)
