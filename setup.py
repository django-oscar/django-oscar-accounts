#!/usr/bin/env python
from setuptools import find_packages, setup

install_requires = [
    'django-oscar>=3.0',
    'python-dateutil>=2.6,<3.0',
]

tests_require = [
    'django-webtest==1.9.8',
    'pytest-cov>=2.12,<3.1',
    'pytest-django>=4.4,<4.5',
    'freezegun>=1.1,<1.2',
    'sorl-thumbnail',
    'factory-boy>=3.2,<3.3',
    'coverage>=5.5,<6.2',
    'tox>=3.17,<3.25',
]


setup(
    name='django-oscar-accounts',
    author="David Winterbottom",
    author_email="david.winterbottom@tangentlabs.co.uk",
    description="Managed accounts for django-oscar",
    long_description=open('README.rst').read(),
    license='BSD',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=['setuptools_scm'],
    extras_require={
        'test': tests_require,
    },
    use_scm_version=True,
)
