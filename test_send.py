import json
from unittestreport_yami.core.resultPush import WeiXin
import requests


def send():
    access_token = None
    corpid = "ww6ffacca2e05d76b0"
    corpsecret = "lENXKKq9_foaFtKCezNxU1EfO8KcADquU5Aj_pbsfpE"
    user_id = "EthanLiu"
    data = {
        "touser": user_id,
        "msgtype": "text",
        "agentid": "1000034",
        "text": "hello",
        "safe": 0,
    }
    wx = WeiXin(access_token=access_token, corpid=corpid, corpsecret=corpsecret)
    response = wx.send_info(data)
    print(response.json)


def send_to_robot():
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4c1559a5-28f5-4632-80aa-60e03800e83d"
    data = {"msgtype": "text", "text": {"content": "hello world"}}
    res = requests.post(url=url, json=data)
    return res
