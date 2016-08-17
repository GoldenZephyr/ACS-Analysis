#!/usr/bin/env python

from setuptools import setup

import sys, os

version = "0.0.1"

#acs_root = os.environ["ACS_ROOT"]

setup(name='ACSObjects',
      version=version,
      zip_safe=True,
      description='ACS Analysis Libraries',
      long_description='A suite of utility functions that facilitate analysis of interest to Aerial Combat Swarms',
      url='coming soon',
      author='NPS ARSENL Lab',
      author_email='acray@nps.edu',
      classifiers=[
          'Devlopment Status :: 2 - Pre-Alpha',
          'Environment :: X11 Applications ',
          'Intended Audience :: Science/Research',
          'License :: TBD',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 2.7',
          'Topic :: Scienctific/Engineering'],
      license='TBD',
      packages=['ACSObjects'])
#,
#      scripts=[acs_root + '/PX4Firmware/Tools/sdlog2/sdlog2_dump.py']
      
