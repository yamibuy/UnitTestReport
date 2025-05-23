from setuptools import setup, find_packages

with open("readme.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

# 读取更新说明
with open("CHANGELOG.md", "r", encoding="utf8") as fh:
    changelog = fh.read()

# 将更新说明添加到长描述中
long_description = f"{long_description}\n\n## Changelog\n{changelog}"

setup(
    name="unittestreport_yami",
    version="0.1.49",
    author="Ethan",
    author_email="ethan.liu@yamibuy.com",
    url="https://github.com/EthanLiuInyami/UnitTestReport",
    license="MIT",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["Jinja2==3.1.2", "PyYAML==5.3.1", "requests>=2.29.0"],
    packages=find_packages(),
    package_data={
        "": ["*.html", "*.md"],
    },
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
)
