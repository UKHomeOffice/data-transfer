"""Configuration settings for setuptools"""

from setuptools import setup, find_packages

def readme():
    """A helper function to read in the README.rst file as the long_description
    """
    with open('README.rst') as readme_file:
        return readme_file.read()

setup(
    name="data-transfer",
    version="1.8.0",
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
    license="MIT",
    long_description=readme(),
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['sqlalchemy==1.3.0', 'coverage==4.4.2', 'pytest==3.2.5',
                      'pytest-cov==2.5.1', 'pathlib==1.0.1', 'boto3==1.4.8',
                      'schedule==0.5.0', 'paramiko==2.4.2'],
    scripts=['bin/data-transfer'],
    url="https://github.com/UKHomeOffice/data-transfer",
)
