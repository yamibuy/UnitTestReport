import re
import traceback
import unittest
import time
from .screenshot import add_screenshot


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

    def startTest(self, test):
        super().startTest(test)
        self.start_time = time.time()

    def stopTest(self, test):
        test.run_time = "{:.2f}s".format(time.time() - self.start_time)
        test.class_name = test.__class__.__qualname__
        test.method_name = test.__dict__["_testMethodName"]
        test.method_doc = test.shortDescription()
        self.fields["results"].append(test)
        self.fields["testClass"].add(test.class_name)

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
        msg = "{}执行——>【通过】\n".format(test)
        self._log_run_info_to_test(test, msg)

    def addFailure(self, test, err):
        self._add_screen_shot_in_test(test)
        super().addFailure(test, err)
        test.state = "失败"
        msg = "{}执行——>【失败】\n".format(test)
        self._log_run_info_to_test(test, msg)
        self._log_run_info_to_test(test, traceback.format_exception(*err))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        test.state = "跳过"
        msg = "{}执行--【跳过Skip】\n".format(test)
        self._log_run_info_to_test(test, reason)
        self._log_run_info_to_test(test, msg)

    def addError(self, test, err):
        self._add_screen_shot_in_test(test)
        super().addError(test, err)
        test.state = "错误"

        msg = "{}执行——>【错误Error】\n".format(test)
        self._log_run_info_to_test(test, msg)
        self._log_run_info_to_test(test, traceback.format_exception(*err))

        if test.__class__.__qualname__ == "_ErrorHolder":
            test.run_time = 0
            res = re.search(r"(.*)\(.*\.(.*)\)", test.description)
            test.class_name = res.group(2)
            test.method_name = res.group(1)
            test.method_doc = test.shortDescription()
            self.fields["results"].append(test)
            self.fields["testClass"].add(test.class_name)

    def _add_screen_shot_in_test(self, test):
        add_screenshot(test)
        self.close_driver(test)

    def close_driver(self, test):
        if type(getattr(test, "driver", "")).__name__ == "WebDriver":
            driver = getattr(test, "driver")
            driver.quit()

    def _log_run_info_to_test(self, test, msg):
        if not hasattr(test, "run_info"):
            test.run_info = []
        if isinstance(msg, list):
            test.run_info.extend(msg)
        else:
            test.run_info.append(msg)
        print(msg)


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
            self.close_driver(test)
            test.count += 1
            msg = f"{test}执行——>【失败Failure】\n"
            self._log_run_info_to_test(test, msg)
            self._log_run_info_to_test(test, traceback.format_exception(*err))

            retry_str = (
                f"================{test}重运行第{test.count}次================\n"
            )
            self._log_run_info_to_test(test, retry_str)

            time.sleep(self.interval)
            test.run(self)
        else:
            super().addFailure(test, err)
            if test.count != 0:
                retried_str = (
                    f"================重运行{test.count}次完毕================\n"
                )
                self._log_run_info_to_test(test, retried_str)

    def addError(self, test, err):
        if not hasattr(test, "count"):
            test.count = 0
        if test.count < self.count:
            self.close_driver(test)
            test.count += 1
            msg = f"{test}执行——>【错误Error】\n"
            self._log_run_info_to_test(test, msg)
            self._log_run_info_to_test(test, traceback.format_exception(*err))
            retry_str = (
                f"================{test}重运行第{test.count}次================\n"
            )
            self._log_run_info_to_test(test, retry_str)
            time.sleep(self.interval)
            test.run(self)
        else:
            super().addError(test, err)
            if test.count != 0:
                retried_str = (
                    f"================重运行{test.count}次完毕================\n"
                )
                self._log_run_info_to_test(test, retried_str)
