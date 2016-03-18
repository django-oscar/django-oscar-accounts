#!/usr/bin/env python
import os
import sys

from setuptools import find_packages, setup

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from oscar_accounts import VERSION # isort:skip


tests_require = [
    'django-webtest==1.7.8',
    'pytest==2.9.0',
    'pytest-cov==2.1.0',
    'pytest-django==2.8.0',
]

setup(
    name='django-oscar-accounts',
    version=VERSION,
    author="David Winterbottom",
    author_email="david.winterbottom@tangentlabs.co.uk",
    description="Managed accounts for django-oscar",
    long_description=open('README.rst').read(),
    license='BSD',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python'
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=[
        'django-oscar>=1.1.1',
        'python-dateutil>=2.4,<2.5'
    ],
    extras_require={
        'test': tests_require,
    },
    tests_require=tests_require,
)
