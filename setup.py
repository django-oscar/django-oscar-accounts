#!/usr/bin/env python
from setuptools import find_packages, setup

install_requires = [
    'django-oscar>=1.5,<1.6',
    'python-dateutil>=2.6,<3.0',
]

tests_require = [
    'django-webtest==1.9.2',
    'pytest==3.2.1',
    'pytest-cov==2.5.1',
    'pytest-django==3.1.2',
]

setup_requires = [
    'setuptools_scm==1.10.1'
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
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    extras_require={
        'test': tests_require,
    },
    use_scm_version=True,
)
