"""
============================
Author:Ethan
============================
"""
from setuptools import setup, find_packages

with open("readme.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

setup(
    name='unittestreport_yami',
    version='0.0.2',
    author='Ethan',
    author_email='ethan.liu@yamibuy.com',
    url='https://github.com/EthanLiuInyami/UnitTestReport',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["Jinja2==3.0.3", "PyYAML==5.3.1","requests==2.24.0"],
    packages=find_packages(),
    package_data={
        "": ["*.html",'*.md'],
    },
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)

