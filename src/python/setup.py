__author__ = 'tom'

from setuptools import setup

# Makes use of the sphinx and sphinx-pypi-upload packages. To build for local development
# use 'python setup.py develop'. To upload a version to pypi use 'python setup.py clean sdist upload'.
# To build docs use 'python setup.py build_sphinx' and to upload docs to pythonhosted.org use
# 'python setup.py upload_sphinx'. Both uploads require 'python setup.py register' to be run, and will
# only work for Tom as they need the pypi account credentials.

setup(
    name='triangula',
    version='0.3.1',
    description='Code for Triangula',
    classifiers=['Programming Language :: Python :: 3.8'],
    url='https://github.com/tomoinn/triangula/',
    author='Tom Oinn',
    author_email='tomoinn@gmail.com',
    license='ASL2.0',
    packages=['triangula'],
    install_requires=['approxeng.input', 'approxeng.task', 'pyserial',
                      'approxeng.holochassis', 'approxeng.hwsupport', 'smbus2', 'euclid'],
    include_package_data=True,
    dependency_links=[],
    zip_safe=False)
