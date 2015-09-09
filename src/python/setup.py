__author__ = 'tom'
from setuptools import setup

# Makes use of the sphinx and sphinx-pypi-upload packages. To build for local development
# use 'python setup.py develop'. To upload a version to pypi use 'python setup.py clean sdist upload'.
# To build docs use 'python setup.py build_sphinx' and to upload docs to pythonhosted.org use
# 'python setup.py upload_sphinx'. Both uploads require 'python setup.py register' to be run, and will
# only work for Tom as they need the pypi account credentials.

# Note - on OSX (and others) to install pygame requires libSDL. On OSX this can be installed with
# 'brew install sdl'. PyGame depends on SDL and not on SDL2. The actual version fetched from mercurial
# may vary, when I did this it pulled back 1.9.2a0 but there's no guarantee this will happen. To
# install pygame in a virtualenv, which makes life much easier, use something like:
# 'yes y | pip install hg+http://bitbucket.org/pygame/pygame' from within the virtualenv you're using.

setup(
    name='triangula',
    version='0.1',
    description='Code for Triangula',
    classifiers=['Programming Language :: Python :: 2.7'],
    url='https://github.com/tomoinn/triangula/',
    author='Tom Oinn',
    author_email='tomoinn@gmail.com',
    license='ASL2.0',
    packages=['triangula'],
    install_requires=['pygame==1.9.2a0', 'euclid==0.1'],
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    dependency_links=['hg+http://bitbucket.org/pygame/pygame#egg=pygame-1.9.2a0'],
    zip_safe=False)
