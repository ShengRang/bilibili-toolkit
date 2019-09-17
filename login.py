#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2019/9/16 22:19
# @Author  : Dawnnnnnn
# @Contact: 1050596704@qq.com
import base64
import hashlib
import random
import requests
import rsa
import string
import sys
import time
from termcolor import *
from urllib import parse


class BiliLogin:
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36"

    def __init__(self):
        self.cookie = ""

    def post(self, url, data=None, headers=None, json=None, decode=True,
             timeout=10):
        try:
            response = requests.post(url, data=data, headers=headers,
                                     json=json,
                                     timeout=timeout)
            return response.json() if decode else response.content
        except:
            return None

    def get(self, url, headers=None, decode=True, timeout=10):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            return response.json() if decode else response.content
        except:
            return None

    def current_time(self):
        tmp = str(
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        return "[" + tmp + "]"

    def log(self, string, info, color):
        ctm = self.current_time()
        tmp = "[" + str(info) + "]"
        print(colored(
            "{:<22}{:<15}{:<20}".format(str(ctm), str(tmp), str(string)),
            color))
        sys.stdout.flush()

    def getSign(self, param):
        salt = "560c52ccd288fed045859ed18bffd973"
        signHash = hashlib.md5()
        signHash.update(f"{param}{salt}".encode())
        return signHash.hexdigest()

    # 登录
    def login(self, username, password):
        self.username, self.password = username, password
        appKey = "1d8b6e7d45233436"
        url = "https://passport.bilibili.com/api/oauth2/getKey"
        data = {'appkey': appKey,
                'sign': self.getSign(f"appkey={appKey}")}
        response = self.post(url, data=data)
        if response and response.get('code') == 0:
            keyHash = response['data']['hash']
            pubKey = rsa.PublicKey.load_pkcs1_openssl_pem(
                response['data']['key'].encode())
        else:
            self.log(f"Key获取失败 {response}", "Error", "red")
            return False
        url = "https://passport.bilibili.com/api/v2/oauth2/login"
        param = f"appkey={appKey}&password={parse.quote_plus(base64.b64encode(rsa.encrypt(f'{keyHash}{self.password}'.encode(), pubKey)))}&username={parse.quote_plus(self.username)}"
        data = f"{param}&sign={self.getSign(param)}"
        headers = {'Content-type': "application/x-www-form-urlencoded"}
        response = self.post(url, data=data, headers=headers)
        while response and response.get('code') == -105:
            self.cookie = f"sid={''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
            url = "https://passport.bilibili.com/captcha"
            headers = {'Cookie': self.cookie,
                       'Host': "passport.bilibili.com",
                       'User-Agent': BiliLogin.ua}
            response = self.get(url, headers=headers, decode=False)
            if response is None:
                continue
            url = "http://106.75.36.27:19951/captcha/v1"
            img = base64.b64encode(response)
            img = str(img, encoding="utf-8")
            json = {'image': img}
            response = self.post(url, json=json, decode=True)
            self.log(f"验证码识别结果为: {response['message']}", "Running", "green")
            url = "https://passport.bilibili.com/api/v2/oauth2/login"
            param = f"appkey={appKey}&captcha={response['message']}&password={parse.quote_plus(base64.b64encode(rsa.encrypt(f'{keyHash}{self.password}'.encode(), pubKey)))}&username={parse.quote_plus(self.username)}"
            data = f"{param}&sign={self.getSign(param)}"
            headers = {'Content-type': "application/x-www-form-urlencoded",
                       'Cookie': self.cookie}
            response = self.post(url, data=data, headers=headers)
        if response and response.get('code') == 0:
            self.cookie = ";".join(f"{i['name']}={i['value']}" for i in
                                   response['data']['cookie_info']['cookies'])
            self.log(f"{self.username}登录成功 {self.cookie}", "Running", "green")
            with open("cookie.txt", "a+", encoding="utf-8")as f:
                f.write(self.cookie + "\n")
            return self.username, self.cookie
        else:
            self.log(f"{self.username}登录失败 {response}", "Error", "red")