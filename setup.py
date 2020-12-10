from setuptools import setup, find_packages

with open('requirements.txt', 'r') as requirements:
    setup(
        name='dbify',
        version='0.0.1',
        install_requires=list(requirements.read().splitlines()),
        packages=find_packages(),
        description='decorator for storing function results in a database'
    )
