from setuptools import setup, find_packages
from os import path
from codecs import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
	long_description = f.read()

setup(
	name='maus',
	version='0.1',
	description="Call the MAUS forced aligner running in docker from Python",
	long_description=long_description,

	url='https://github.com/Alveo/alveo-maus',

	maintainer='Steve Cassidy',
	maintainer_email='Steve.Cassidy@mq.edu.au',
	license = 'BSD',

	keywords='speech forced-alignment acoustics',

	packages = find_packages(exclude=['contrib', 'docs', 'tests*']),

    install_requires=[
    ],

    test_suite='tests'
	)
