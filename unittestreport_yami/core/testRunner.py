# encoding=utf-8

import json
import os
import unittest
import time
from concurrent.futures.thread import ThreadPoolExecutor

from unittestreport_yami.core.screenshot import upload_img_to_s3, upload_report_to_s3
from ..core.testResult import TestResult, ReRunResult
from ..core.resultPush import DingTalk, WeiXin, SendEmail

from jinja2 import Environment, FileSystemLoader
import copy

Load = unittest.defaultTestLoader

IMG_TMPL = """
<div id="case-image" class="modal show" style="display:none; background-color: #000000c7;">
  <div class="modal-dialog modal-dialog-centered log_window">
    <div class="modal-content shadow-3">
      <div class="modal-header">
        <div>
          <h5 class="mb-1">screenshots</h5>
        </div>
          <div>
            <button class="btn btn-sm btn-square bg-tertiary bg-opacity-20 bg-opacity-100-hover text-tertiary text-white-hover" onclick='hideImg(this)'">X</button>
          </div>
        </div>
        <div class="modal-body" style="height: 600px; background: #e7eaf0;">
          {images}
        </div>
        <div class="img-circle"></div>
    </div>
    </div>
</div>
"""


class TestRunner:

    def __init__(
        self,
        suite: unittest.TestSuite,
        filename="report.html",
        report_dir="./reports",
        title="测试报告",
        tester="测试员",
        desc="测试报告",
        templates=1,
        report_url=None,
        only_failed=False,
        upload_report_to_s3=False,
        render=True,
    ):
        """
        :param suites: test suite
        :param filename: Report file name
        :param report_dir:The path to the report file
        :param title:Test suite title
        :param templates: You can specify the style template for the report by parameter value 1 or 2. Currently, there are only two templates
        :param tester:Tester
        """
        if not isinstance(suite, unittest.TestSuite):
            raise TypeError("Parameter suite is not a test suite")
        if not isinstance(filename, str):
            raise TypeError("filename is not str")
        if not filename.endswith(".html"):
            filename = filename + ".html"
        self.suite = suite
        self.filename = filename
        self.title = title
        self.tester = tester
        self.desc = desc
        self.templates = templates
        self.report_dir = report_dir
        self.result = []
        self.starttime = time.time()
        self.report_url = report_url
        self.only_failed = only_failed
        self.render = render
        self.upload_report_to_s3 = upload_report_to_s3
        self.report_s3_url = ""

    def __classification_suite(self):
        suites_list = []

        def wrapper(suite):
            for item in suite:
                if isinstance(item, unittest.TestCase):
                    suites_list.append(suite)
                    break
                else:
                    wrapper(item)

        wrapper(copy.deepcopy(self.suite))
        return suites_list

    def __do_with_base_result(self, test_result, render=True):
        print(f"do with base result, render is {render}")
        s3_url = ""
        for res in test_result["results"]:
            if not s3_url and hasattr(res, "s3_url"):
                s3_url = res.s3_url
            if getattr(res, "images", []) and not getattr(
                res, "images_processed", False
            ):
                status_text = bytes(res.state, "utf-8").decode()
                if self.only_failed and status_text == "成功":
                    for img in res.images:
                        if hasattr(res, "s3_url"):
                            os.remove(img)
                    res.images = []
                tmp = ""

                for i, img in enumerate(res.images):
                    if hasattr(res, "s3_url") and os.path.exists(img):
                        s3_img_url = upload_img_to_s3(res.s3_url, img)
                        if not s3_img_url:
                            continue
                        if i == 0:
                            tmp += """<img src="{}" style="display: block;" loading="lazy" class="img"/>\n""".format(
                                s3_img_url
                            )
                        else:
                            tmp += """<img src="{}" style="display: none;" loading="lazy" class="img"/>\n""".format(
                                s3_img_url
                            )
                    else:
                        if i == 0:
                            tmp += """<img src="data:image/jpg;base64,{}" style="display: block;" class="img"/>\n""".format(
                                img
                            )
                        else:
                            tmp += """<img src="data:image/jpg;base64,{}" style="display: none;" class="img"/>\n""".format(
                                img
                            )
                screenshots_html = IMG_TMPL.format(images=tmp)
                setattr(res, "screenshots_html", screenshots_html)
                # Mark images as processed
                setattr(res, "images_processed", True)
        # 判断是否要生产测试报告
        if not os.path.isdir(self.report_dir):
            os.mkdir(self.report_dir)
        # 获取历史执行数据
        test_result["history"] = self.__handle_history_data(test_result)
        template_path = os.path.join(os.path.dirname(__file__), "../templates")
        env = Environment(loader=FileSystemLoader(template_path))
        if self.templates == 2:
            template = env.get_template("templates2.html")
        elif self.templates == 3:
            template = env.get_template("templates3.html")
        else:
            template = env.get_template("templates.html")
        if render:
            file_path = os.path.join(self.report_dir, self.filename)
            res = template.render(test_result)
            with open(file_path, "wb") as f:
                f.write(res.encode("utf8"))
            if self.upload_report_to_s3:
                self.report_s3_url = upload_report_to_s3(
                    s3_url=s3_url, file_path=file_path
                )
                print("测试报告已经生成，报告路径为:{}".format(self.report_s3_url))
            else:
                print("测试报告已经生成，报告路径为:{}".format(file_path))
            self.email_conent = {
                "file": os.path.abspath(file_path),
                "content": env.get_template("templates03.html").render(test_result),
            }
            self.test_result = test_result
        return test_result
    
    def seconds_to_hms(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02}h {minutes:02}m {seconds:02}s"

    def __get_reports(self):
        print("所有用例执行完毕，组合数据中......")
        test_result = {
            "success": 0,
            "all": 0,
            "fail": 0,
            "skip": 0,
            "error": 0,
            "results": [],
            "testClass": [],
        }
        for res in self.result:
            for item in test_result:
                test_result[item] += res.fields[item]

        execute_duration_seconds = time.time() - self.starttime
        execute_duration_string = self.seconds_to_hms(execute_duration_seconds)
        test_result["runtime"] = execute_duration_string
        # test_result["runtime"] = "{:.2f}s".format(time.time() - self.starttime)
        test_result["begin_time"] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(self.starttime)
        )
        test_result["title"] = self.title
        test_result["tester"] = self.tester
        test_result["desc"] = self.desc
        if test_result["all"] != 0:
            test_result["pass_rate"] = "{:.2f}".format(
                test_result["success"] / test_result["all"] * 100
            )
        else:
            test_result["pass_rate"] = 0
        return self.__do_with_base_result(test_result, self.render)

    def __handle_history_data(self, test_result):
        """
        处理历史数据
        :return:
        """
        try:
            with open(
                os.path.join(self.report_dir, "history.json"), "r", encoding="utf-8"
            ) as f:
                history = json.load(f)
        except FileNotFoundError as e:
            history = []
        history.append(
            {
                "success": test_result["success"],
                "all": test_result["all"],
                "fail": test_result["fail"],
                "skip": test_result["skip"],
                "error": test_result["error"],
                "runtime": test_result["runtime"],
                "begin_time": test_result["begin_time"],
                "pass_rate": test_result["pass_rate"],
            }
        )

        with open(
            os.path.join(self.report_dir, "history.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(history, f, ensure_ascii=True)
        return history

    def __get_notice_content(self):
        """获取通知的内容"""
        template_path = os.path.join(os.path.dirname(__file__), "../templates")
        env = Environment(loader=FileSystemLoader(template_path))
        if self.report_s3_url:
            template = env.get_template("remote_report.md")
            self.test_result["report_address"] = self.report_s3_url
        elif self.report_url:
            template = env.get_template("remote_report.md")
            report_address = f"{self.report_url}/{self.filename}"
            report_address = report_address.replace("\\", "/")
            self.test_result["report_address"] = report_address
        else:
            template = env.get_template("dingtalk.md")
        res_text = template.render(self.test_result)
        return res_text

    def run(self, thread_count=1, count=0, interval=2):
        """
        The entrance to running tests
        Note: if multiple test classes share a global variable, errors may occur due to resource competition
        :param thread_count:Number of threads. default 1
        :param count: Rerun times,  default 0
        :param interval: Rerun interval, default 2
        :return: Test run results
        """
        suites = self.__classification_suite()

        if thread_count > 1:
            with ThreadPoolExecutor(max_workers=thread_count) as ts:
                for i in suites:
                    res = ReRunResult(count=count, interval=interval)
                    self.result.append(res)
                    ts.submit(i.run, result=res).add_done_callback(res.stopTestRun)
        else:
            res = ReRunResult(count=count, interval=interval)
            self.result.append(res)
            self.suite.run(res)
            res.stopTestRun()
        result = self.__get_reports()
        return result

    def rerun_run(self, count=0, interval=2):
        """
        Test case failure and error rerun mechanism
        :param count: Rerun times,  default 0
        :param interval: Rerun interval, default 2
        :return: Test run results
        """
        res = ReRunResult(count=count, interval=interval)
        self.result.append(res)
        suites = self.__classification_suite()
        for case_ in suites:
            case_.run(res)
        res.stopTestRun()
        res = self.__get_reports()
        return res

    def send_email(
        self, host: str, port: int, user: str, password: str, to_addrs, is_file=True
    ):
        """
        The occurrence report is attached to the mailbox
        :param host: SMTP server address
        :param port: SMTP server port
        :param user: Email account number
        :param password: SMTP service authorization code of mailbox
        :param to_addrs: Addressee's address str or list
        :return:
        """
        sm = SendEmail(host=host, port=port, user=user, password=password)
        if is_file:
            filename = self.email_conent["file"]
        else:
            filename = None
        content = self.email_conent["content"]

        sm.send_email(
            subject=self.title, content=content, filename=filename, to_addrs=to_addrs
        )

    def get_except_info(self):
        """Get error reporting information for error cases and failure cases"""
        except_info = []
        num = 0
        for i in self.result:
            for texts in i.failures:
                t, content = texts
                num += 1
                except_info.append(
                    "*{}、用例【{}】执行失败*，\n失败信息如下：".format(
                        num, t._testMethodDoc
                    )
                )
                except_info.append(content)
            for texts in i.errors:
                num += 1
                t, content = texts
                except_info.append(
                    "*{}、用例【{}】执行错误*，\n错误信息如下：".format(
                        num, t._testMethodDoc
                    )
                )
                except_info.append(content)
        except_str = "\n".join(except_info)
        return except_str

    def dingtalk_notice(
        self,
        url,
        key=None,
        secret=None,
        atMobiles=None,
        isatall=False,
        except_info=False,
    ):
        """
        :param url: 钉钉机器人的Webhook地址
        :param key: （非必传：str类型）如果钉钉机器人安全设置了关键字，则需要传入对应的关键字
        :param secret:（非必传:str类型）如果钉钉机器人安全设置了签名，则需要传入对应的密钥
        :param atMobiles: （非必传，list类型）发送通知钉钉中要@人的手机号列表，如：[137xxx,188xxx]
        :param isatall: 是否@所有人，默认为False,设为True则会@所有人
        :param except_info:是否发送未通过用例的详细信息，默认为False，设为True则会发送失败用例的详细信息
        :return:  发送成功返回 {"errcode":0,"errmsg":"ok"}  发送失败返回 {"errcode":错误码,"errmsg":"失败原因"}
        """

        res_text = self.__get_notice_content()
        if except_info:
            res_text += "\n ### 未通过用例详情：\n"
            res_text += self.get_except_info()
        data = {
            "msgtype": "markdown",
            "markdown": {"title": "{}({})".format(self.title, key), "text": res_text},
            "at": {"atMobiles": atMobiles, "isAtAll": isatall},
        }
        ding = DingTalk(url=url, data=data, secret=secret)
        response = ding.send_info()
        return response.json()

    def weixin_notice(self, chatid, access_token=None, corpid=None, corpsecret=None):
        """
        测试结果推送到企业微信群，【access_token】和【corpid，corpsecret】至少要传一种
        可以传入access_token ,也可以传入（corpid，corpsecret）来代替access_token
        :param chatid: 企业微信群ID
        :param access_token: 调用企业微信API接口的凭证
        :param corpid: 企业ID
        :param corpsecret:应用的凭证密钥
        :return:
        """
        # 获取通知结果
        res_text = self.__get_notice_content()
        data = {
            "chatid": chatid,
            "msgtype": "markdown",
            "markdown": {"content": res_text},
        }
        wx = WeiXin(access_token=access_token, corpid=corpid, corpsecret=corpsecret)
        response = wx.send_info(data=data)
        return response

    def weixin_robot_notice(self, webhook, notice_users=None):
        res_text = self.__get_notice_content()
        notice_users = notice_users or []
        if self.test_result["fail"] or self.test_result["error"]:
            res_text = f"{res_text}\n\n"
            for user in notice_users:
                res_text = f"{res_text} <@{user}>"
        data = {
            "msgtype": "markdown",
            "markdown": {"content": res_text},
        }
        response = WeiXin().send_to_bot(webhook, data)
        return response

    def merge_result(self, *other_results):
        """
        :param other_results: 可以多个合并,这里的other_result 是 run返回的字典对象
        """
        if not self.result:
            main_result = TestResult()
            main_result.fields = {
                "success": 0,
                "fail": 0,
                "error": 0,
                "skip": 0,
                "all": 0,
                "results": [],
                "testClass": [],
            }
            main_result.testsRun = 0
            self.result.append(main_result)
        else:
            main_result = self.result[0]

        for other_result in other_results:
            # 合并统计字段
            for key in ["success", "fail", "error", "skip"]:
                main_result.fields[key] += other_result.get(key, 0)
            main_result.fields["all"] += other_result.get("all", 0)

            main_result.fields["results"].extend(other_result.get("results", []))

            main_result.fields["testClass"].extend(other_result.get("testClass", []))

        self.__get_merged_reports()

    def __get_merged_reports(self):
        print("所有用例执行完毕，正在生成测试报告中......")
        test_result = {
            "success": 0,
            "all": 0,
            "fail": 0,
            "skip": 0,
            "error": 0,
            "results": [],
            "testClass": [],
        }

        for res in self.result:
            for key in ["success", "fail", "error", "skip"]:
                test_result[key] += res.fields.get(key, 0)
            test_result["all"] += res.fields.get("all", 0)
            test_result["results"].extend(res.fields.get("results", []))
            test_result["testClass"].extend(res.fields.get("testClass", []))

        test_result["runtime"] = "{:.2f}s".format(time.time() - self.starttime)
        test_result["begin_time"] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(self.starttime)
        )
        test_result["title"] = self.title
        test_result["tester"] = self.tester
        test_result["desc"] = self.desc
        if test_result["all"] != 0:
            test_result["pass_rate"] = "{:.2f}".format(
                test_result["success"] / test_result["all"] * 100
            )
        else:
            test_result["pass_rate"] = 0

        return self.__do_with_base_result(test_result, True)
