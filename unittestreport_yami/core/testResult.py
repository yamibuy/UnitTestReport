import re
import traceback
import unittest
import sys
import time
from io import StringIO

origin_stdout = sys.stdout


def output2console(s):
    """Output stdout content to console"""
    tmp_stdout = sys.stdout
    sys.stdout = origin_stdout
    print(s, end="")
    sys.stdout = tmp_stdout


class OutputRedirector(object):
    """Wrapper to redirect stdout or stderr"""

    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)
        origin_stdout.write(str(s))

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()


stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)


def add_screenshot(test):
    if type(getattr(test, "driver", "")).__name__ == "WebDriver":
        try:
            driver = getattr(test, "driver")
            test.images.append(driver.get_screenshot_as_base64())
        except Exception as e:
            print(e)
            driver.quit()


class TestResult(unittest.TestResult):
    def __init__(self):
        super().__init__()

        self.fields = {
            "success": 0,
            "all": 0,
            "fail": 0,
            "skip": 0,
            "error": 0,
            "begin_time": "",
            "results": [],
            "testClass": set(),
        }
        self.sys_stdout = None
        self.sys_stderr = None
        self.outputBuffer = None

    def startTest(self, test):
        super().startTest(test)
        self.start_time = time.time()
        self.outputBuffer = StringIO()
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer
        self.sys_stdout = sys.stdout
        self.sys_stderr = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def complete_output(self):
        if self.sys_stdout:
            sys.stdout = self.sys_stdout
            sys.stderr = self.sys_stderr
            self.sys_stdout = None
            self.sys_stderr = None
        return self.outputBuffer.getvalue()

    def stopTest(self, test):
        test.run_time = "{:.2f}s".format(time.time() - self.start_time)
        test.class_name = test.__class__.__qualname__
        test.method_name = test.__dict__["_testMethodName"]
        test.method_doc = test.shortDescription()
        self.fields["results"].append(test)
        self.fields["testClass"].add(test.class_name)
        self.complete_output()

    def stopTestRun(self, title=None):
        self.fields["fail"] = len(self.failures)
        self.fields["error"] = len(self.errors)
        self.fields["skip"] = len(self.skipped)
        self.fields["all"] = sum(
            [
                self.fields["fail"],
                self.fields["error"],
                self.fields["skip"],
                self.fields["success"],
            ]
        )
        self.fields["testClass"] = list(self.fields["testClass"])

    def addSuccess(self, test):
        self._add_screen_shot_in_test(test)
        self.fields["success"] += 1
        test.state = "成功"
        logs = []
        msg = "{}执行——>【通过】\n".format(test)
        logs.append(msg)
        sys.stdout.write(msg)
        # output = self.complete_output()
        # logs.append(output)
        if not test.run_info:
            test.run_info = []
        test.run_info.extend(logs)

    def addFailure(self, test, err):
        self._add_screen_shot_in_test(test)
        super().addFailure(test, err)
        test.state = "失败"
        logs = []
        msg = "{}执行——>【失败】\n".format(test)
        logs.append(msg)
        sys.stdout.write(msg)
        output = self.complete_output()
        logs.append(output)
        logs.extend(traceback.format_exception(*err))
        if not test.run_info:
            test.run_info = []
        test.run_info.extend(logs)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        test.state = "跳过"
        logs = [reason]
        msg = "{}执行--【跳过Skip】\n".format(test)
        logs.append(msg)
        sys.stdout.write(msg)

        if not test.run_info:
            test.run_info = []
        test.run_info.extend(logs)

    def addError(self, test, err):
        self._add_screen_shot_in_test(test)
        super().addError(test, err)
        test.state = "错误"

        msg = "{}执行——>【错误Error】\n".format(test)
        sys.stderr.write(msg)
        logs = []
        logs.append(msg)
        logs.extend(traceback.format_exception(*err))

        if test.__class__.__qualname__ == "_ErrorHolder":
            test.run_time = 0
            res = re.search(r"(.*)\(.*\.(.*)\)", test.description)
            test.class_name = res.group(2)
            test.method_name = res.group(1)
            test.method_doc = test.shortDescription()
            self.fields["results"].append(test)
            self.fields["testClass"].add(test.class_name)
        if not test.run_info:
            test.run_info = []
        test.run_info.extend(logs)

    def _add_screen_shot_in_test(self, test):
        add_screenshot(test)
        self.close_driver(test)

    def close_driver(self, test):
        if type(getattr(test, "driver", "")).__name__ == "WebDriver":
            driver = getattr(test, "driver")
            driver.quit()


class ReRunResult(TestResult):

    def __init__(self, count, interval):
        super().__init__()
        self.count = count
        self.interval = interval
        self.run_cases = []

    def startTest(self, test):
        if not hasattr(test, "count"):
            super().startTest(test)
        test.images = getattr(test, "images", [])

    def stopTest(self, test):
        if test not in self.run_cases:
            self.run_cases.append(test)
            super().stopTest(test)

    def addFailure(self, test, err):
        if not hasattr(test, "count"):
            test.count = 0
        if test.count < self.count:
            super().close_driver(test)
            test.count += 1
            sys.stderr.write("{}执行——>【失败Failure】\n".format(test))
            for string in traceback.format_exception(*err):
                sys.stderr.write(string)
            sys.stderr.write(
                f"================{test}重运行第{test.count}次================\n"
            )

            time.sleep(self.interval)
            test.run(self)
        else:
            super().addFailure(test, err)
            if test.count != 0:
                sys.stderr.write(
                    f"================重运行{test.count}次完毕================\n"
                )

    def addError(self, test, err):
        if not hasattr(test, "count"):
            test.count = 0
        if test.count < self.count:
            super().close_driver(test)
            test.count += 1
            sys.stderr.write("{}执行——>【错误Error】\n".format(test))
            for string in traceback.format_exception(*err):
                sys.stderr.write(string)
            sys.stderr.write(
                f"================{test}重运行第{test.count}次================\n"
            )
            time.sleep(self.interval)
            test.run(self)
        else:
            super().addError(test, err)
            if test.count != 0:
                sys.stderr.write(
                    f"================重运行{test.count}次完毕================\n"
                )
