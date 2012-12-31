"""Minimal setup script to appease buildout for Melange.
"""
import os
import re
from setuptools import setup, find_packages


version = "0.0"

setup(
    name = 'PasteHub',
    description=("PasteHub makes sharing of text and code easily on the web."),
    version = version,
    packages = find_packages(exclude=['thirdparty','parts']),
    author="Praveen Kumar",
    url='http:://github.com/praveen97uma/pastehub',
    license='Not yet decided',
    install_requires = [
        ],
    tests_require=[
        'nose',
        ],
    entry_points = {'console_scripts': ['run-tests = tests.run:main',
                                        'gen-app-yaml = scripts.gen_app_yaml:main',
                                        ],
                    },
    include_package_data = True,
    zip_safe = False,
    )
