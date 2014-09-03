from setuptools import setup, find_packages
import os

version = '0.0.1'

setup(
    name='loyalty_point_engine',
    version=version,
    description='Environment for managing loyalty points',
    author='Saurabh',
    author_email='saurabh.p@indictranstech.com',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=("frappe",),
)
