import unittest
from unittestreport import TestRunner

suite = unittest.defaultTestLoader.discover(
    r"C:\git_project\UnitTestReport\tests\testcases"
)

runner = TestRunner(suite, templates=1, report_dir="./reports")

runner.run()

runner.send_email(
    host="smtp.qq.com",
    port=465,
    user="musen_nmb@qq.com",
    password="algmmzptupjccbab",
    to_addrs="3247119728@qq.com",
)


# python setup.py sdist bdist_wheel
# twine upload dist/*
