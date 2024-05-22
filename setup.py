from setuptools import setup, find_packages

with open("readme.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

setup(
    name="unittestreport_yami",
    version="0.1.1",
    author="Ethan",
    author_email="ethan.liu@yamibuy.com",
    url="https://github.com/EthanLiuInyami/UnitTestReport",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["Jinja2==3.0.3", "PyYAML==5.3.1", "requests==2.32.2"],
    packages=find_packages(),
    package_data={
        "": ["*.html", "*.md"],
    },
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
