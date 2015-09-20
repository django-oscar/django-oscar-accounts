#!/usr/bin/env python
from setuptools import setup, find_packages

from accounts import VERSION

tests_require = [
    'django-dynamic-fixture==1.8.5',
    'django-webtest==1.7.8',
    'pytest==2.8.0',
    'pytest-cov==2.1.0',
    'pytest-django==2.8.0',
]

setup(
    name='django-oscar-accounts',
    version=VERSION,
    author="David Winterbottom",
    author_email="david.winterbottom@tangentlabs.co.uk",
    description="Managed accounts for django-oscar",
    long_description=open('README.md').read(),
    license=open('LICENSE').read(),
    packages=find_packages(exclude=['sandbox*', 'tests*']),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python'
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
