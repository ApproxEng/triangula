__author__ = 'tom'
from setuptools import setup

setup(
    name='triangula',
    version='0.1',
    description='Code for Triangula',
    classifiers=['Programming Language :: Python :: 2.7'],
    url='https://github.com/tomoinn/triangula/',
    author='Tom Oinn',
    author_email='tomoinn@gmail.com',
    license='GPL',
    packages=['triangula'],
    install_requires=[],
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False)
