#!/usr/bin/env python
from setuptools import find_packages, setup

install_requires = [
    'django>=2.2,<3.1',
    'django-oscar>=2.0',
    'python-dateutil>=2.6,<3.0',
]

tests_require = [
    'django-webtest==1.9.7',
    'pytest-cov>=2.5,<2.11',
    'pytest-django>=3.5,<4.2',
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
        'Framework :: Django :: 3.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=['setuptools_scm'],
    extras_require={
        'test': tests_require,
    },
    use_scm_version=True,
)
