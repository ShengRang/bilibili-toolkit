#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2019/9/17 23:06
# @Author  : Dawnnnnnn
# @Contact: 1050596704@qq.com
import traceback
import aiohttp
import asyncio
import time
from printer import Printer

printer = Printer()


# 生成获取令牌
def generate_verify_token():
    return object()


class Request:
    def __init__(self, loop=None):
        self.proxy_api = "8.8.8.8"
        # 全局session
        self.ssion = {}
        # 工作队列
        self.que = asyncio.Queue()
        self.query_limit_sem = asyncio.Semaphore(15)
        self.form_data = aiohttp.FormData()
        self.loop = loop or asyncio.get_event_loop()

    # 请求中心
    async def _requests(self, fut, method, url, proxy=False,
                        suname='',
                        **kwargs):
        flag = 10
        while True:
            try:
                if flag < 0 or proxy:
                    temp = await self.other_get(self.proxy_api)
                    proxy = f'http://{temp}'
                else:
                    proxy = None
                async with self.query_limit_sem:
                    async with getattr(self.ssion[suname], method)(
                            url, proxy=proxy, verify_ssl=False, timeout=20,
                            **kwargs) as r:

                        # text()函数相当于requests中的r.text，r.read()相当于requests中的r.content
                        data = await r.read()
                        await r.release()
                        fut.set_result(data)
                        return data

            except Exception as e:
                traceback.print_exc()
                printer.printer(f"{url}{e}", "Error", "red")
                flag -= 1
                continue

    # 其他GET请求
    async def other_get(self, url, headers=None, proxy=False):
        flag = 10
        while True:
            try:
                if flag < 0 or proxy:
                    temp = await self.other_get(self.proxy_api)
                    proxy = f'http://{temp}'
                else:
                    proxy = None

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers,
                                           timeout=10, proxy=proxy,
                                           verify_ssl=False) as r:
                        # text()函数相当于requests中的r.text，r.read()相当于requests中的r.content
                        data = await r.text()
                        await r.release()
                        return data

            except Exception as e:
                printer.printer(f"{url}{e}", "Error", "red")
                flag -= 1
                continue

    # 加入请求任务
    async def req_add_job(self, *args, **kwargs):
        try:
            # 将任务放入队列，等待阻塞读取，参数是被执行的函数和函数的参数
            fut = self.loop.create_future()
            req_pack = ((self._requests, args, kwargs), fut)
            await self.que.put(req_pack)
            return await fut
        except Exception as e:
            printer.printer(f"req_add_job {e}", "Error", "red")

    # 维护请求队列
    async def req_loop(self):
        while True:
            try:
                req = await self.que.get()
                ((target, args, kwargs), fut) = req
                task = self.loop.create_task(target(fut, *args, **kwargs))
            except Exception as e:
                printer.printer(f"req_loop {e}", "Error", "red")
