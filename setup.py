#!/usr/bin/env python
import os
import sys
from distutils.log import warn as printf
from setuptools import setup, find_packages, Extension, Command

if 'build' in sys.argv:
    os.system('make configure')

setup(
    name='procszoo',
    version='0.97.1',
    description='python module to operate Linux namespaces',
    license='GPL2+',
    author='xning',
    author_email='anzhou94@gmail.com',
    packages = find_packages(),
    url='https://github.com/xning/procszoo',
    use_2to3=False,
    scripts=['bin/richard_parker', 'lib/procszoo/my_init'],
    ext_modules = [
        Extension(name='procszoo.c_functions.atfork',
            sources=['procszoo/c_functions/atfork/atfork.c',
                'procszoo/c_functions/atfork/atfork_module.c'],
            depends=['procszoo/c_functions/atfork/atfork.h'],
            ),
        ],
    package_data = {'': ['*.txt', '*.md', 'README.first']}
)

