#!/usr/bin/python3
# -- coding: utf-8 --
# -------------------------------
# @Author : github@limoruirui https://github.com/limoruirui
# @Time : 2022/8/23 23:31
# -------------------------------
from requests import post
from json import dumps
from sys import path
path.append("./tools")
from tool import get_environ



def wxpush(text):
    url = f"http://yun.tustbpf.top:83/?sendkey=000000&text={text}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        post(url, headers=headers)
    except:
        print('推送失败')



if __name__ == "__main__":
    wxpush("22323")