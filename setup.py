import os
from setuptools import setup, find_packages
from Timetracker.version import __version__


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="TimeTracker",
    version=__version__,
    author="Harold Claus",
    author_email="harold1984@gmail.com",
    description="CLI solution to manage your worklogs and send them to JIRA",
    license="GPLv3",
    keywords="timetracker jira",
    packages=find_packages(),
    scripts=['tt'],
    python_requires='>3.4',
    long_description=read('README.md'),
)
