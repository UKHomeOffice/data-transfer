"""Configuration settings for setuptools"""

from setuptools import setup, find_packages

def readme():
    """A helper function to read in the README.rst file as the long_description
    """
    with open('README.rst') as readme_file:
        return readme_file.read()

setup(
    name="data-transfer",
    version="1.2.0",
    author="Aker Systems",
    author_email="development@akersystems.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    description=("A data movement app that can use different source/targets to"
                 "move data around."),
    keywords="data movement ftp sftp s3 buckets ingest",
    license="BSD",
    long_description=readme(),
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    scripts=['bin/data-transfer'],
    url="https://github.com/UKHomeOffice/data-transfer",
)
