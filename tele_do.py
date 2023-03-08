#!/usr/bin/python3
# -- coding: utf-8 --
# -------------------------------
# @Author : yun.tustbpf.top:84
# @Time : 2023/1/29 16:10
# cron "1 9,12 * * *" script-path=xxx.py,tag=匹配cron用
# const $ = new Env('电信签到');
# -------------------------------

"""
1. 电信签到自动完成金豆任务。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。
2. cron说明 12点必须执行一次(用于兑换) 然后12点之外还需要执行一次(用于执行每日任务) 一天共两次 可直接使用默认cron
2. 环境变量说明:
    必须  TELECOM_PHONE : 电信手机号
    选填  TELECOM_PASSWORD : 电信服务密码 填写后会执行更多任务
    选填  TELECOM_FOOD  : 给宠物喂食次数 默认为0 不喂食 根据用户在网时长 每天可以喂食5-10次
3. 必须登录过 电信营业厅 app的账号才能正常运行
"""

from datetime import date, datetime
from random import shuffle, randint, choices
from time import sleep, strftime
from re import findall
from requests import get, post
from base64 import b64encode
from tools.aes_encrypt import AES_Ctypt
from tools.rsa_encrypt import RSA_Encrypt
from tools.tool import timestamp, get_environ, print_now
from tools.send_msg import wxpush
from login.telecom_login import TelecomLogin
from string import ascii_letters, digits
from  rsapost import RsaPost



class ChinaTelecom:
    def __init__(self, account, pwd, checkin=True):
        self.phone = account
        self.ticket = ""
        self.token = ""
        self.task_status=""
        self.task_list=""
        self.live_List=[]
        self.task_dic={}
        self.anchorId=[]
        if pwd != "" and checkin:
            userLoginInfo = TelecomLogin(account, pwd).main()
            print(userLoginInfo)
            self.ticket = userLoginInfo[0]
            self.token = userLoginInfo[1]

    def init(self):
        self.msg = ""
        self.ua = f"CtClient;9.6.1;Android;12;SM-G9860;{b64encode(self.phone[5:11].encode()).decode().strip('=+')}!#!{b64encode(self.phone[0:5].encode()).decode().strip('=+')}"
        self.headers = {
            "Host": "wapside.189.cn:9001",
            "Referer": "https://wapside.189.cn:9001/resources/dist/signInActivity.html",
            "User-Agent": "CtClient;8.1.0;Android;10;SM-N9600",
            "sign": "5cf8543f835d4775a1d3cb359af45fe4"     
        }
        self.key = "-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+ugG5A8cZ3FqUKDwM57GM4io6\nJGcStivT8UdGt67PEOihLZTw3P7371+N47PrmsCpnTRzbTgcupKtUv8ImZalYk65\ndU8rjC/ridwhw9ffW2LBwvkEnDkkKKRi2liWIItDftJVBiWOh17o6gfbPoNrWORc\nAdcbpk2L+udld5kZNwIDAQAB\n-----END PUBLIC KEY-----"

    def req(self, url, method, data=None):
        if method == "GET":
            data = get(url, headers=self.headers).json()
            return data
        elif method.upper() == "POST":
            data = post(url, headers=self.headers, json=data).json()
            return data
        else:
            print_now("您当前使用的请求方式有误,请检查")

    # 长明文分段rsa加密
    def telecom_encrypt(self, text):
        if len(text) <= 32:
            return RSA_Encrypt(self.key).encrypt(text)
        else:
            encrypt_text = ""
            for i in range(int(len(text) / 32) + 1):
                split_text = text[(32 * i):(32 * (i + 1))]
                encrypt_text += RSA_Encrypt(self.key).encrypt(split_text)
            return encrypt_text
    @staticmethod
    def geneRandomToken():
        randomList = choices(ascii_letters + digits, k=129)
        token = f"V1.0{''.join(x for x in randomList)}"
        return token
    # 签到
    def chech_in(self):
        url = "https://wapside.189.cn:9001/jt-sign/api/home/sign"
        data = {
            "encode": AES_Ctypt("34d7cb0bcdf07523").encrypt(
                f'{{"phone":{self.phone},"date":{timestamp()},"signSource":"smlprgrm"}}')
        }
        print_now(self.req(url, "post", data))

    # 获取任务列表
    def get_task(self):

        url = "https://wapside.189.cn:9001/jt-sign/paradise/getTask"
        data = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        msg = self.req(url, "post", data)

        if msg["resoultCode"] == "0":
            self.task_list = msg["data"]
            print_now("---------------------------------任务状态-------------------------------------------")
            print_now("")
            for task in self.task_list:
                if(task["status"]!="2"):
                    print(f'{(task["title"])}----------------【未完成】')
                else:
                    print(f'{(task["title"])}----------------已完成')
            print_now("")
            print_now("---------------------------------任务状态-------------------------------------------")
        else:
            print_now("获取任务列表失败")
            print_now(msg)
            return



    # 做每日任务
    def do_task(self):

        url = "https://wapside.189.cn:9001/jt-sign/paradise/polymerize"
        for task in self.task_list:
            if "翻牌抽好礼" in task["title"] or "查看我的订单" in task["title"] or "查看我的云盘" in task["title"] or "访问宽带余额" in task["title"] or "我的宽带" in task["title"] or "装修进度" in task["title"] or "登录" in task["title"]or "查看" in task["title"]:
                print_now(f'{task["title"]}----{task["taskId"]}')
                decrept_para = f'{{"phone":"{self.phone}","jobId":"{task["taskId"]}"}}'
                data = {
                    "para": self.telecom_encrypt(decrept_para)
                }
                data = self.req(url, "POST", data)
                if data["data"]["code"] == 0:
                    # print(data["resoultMsg"])
                    print_now(data["data"]["err"])
                    #print_now(decrept_para)
                    #print_now(self.telecom_encrypt(decrept_para))
                else:
                    print_now(f'聚合任务完成失败,原因是{data["resoultMsg"]}')

    # 给宠物喂食
    def food(self):
        url = "https://wapside.189.cn:9001/jt-sign/paradise/food"
        data = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        res_data = self.req(url, "POST", data)
        if res_data["resoultCode"] == "0":
            print_now(res_data["resoultMsg"])
        else:
            print_now(f'聚合任务完成失败,原因是{res_data["resoultMsg"]}')

    # 查询宠物等级
    def get_level(self):
        url = "https://wapside.189.cn:9001/jt-sign/paradise/getParadiseInfo"
        body = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        data = self.req(url, "POST", body)
        self.level = int(data["userInfo"]["paradiseDressup"]["level"])
        if self.level < 5:
            print_now("当前等级小于5级 不领取等级权益")
            return
        url = "https://wapside.189.cn:9001/jt-sign/paradise/getLevelRightsList"
        right_list = self.req(url, "POST", body)[f"V{self.level}"]
        for data in right_list:
            # print(dumps(data, indent=2, ensure_ascii=0))
            if "00金豆" in data["righstName"] or "话费" in data["righstName"]:
                rightsId = data["id"]
                self.level_ex(rightsId)
                continue
        # print(self.rightsId)

    # 每月领取等级金豆
    def level_ex(self, rightsId):
        # self.get_level()
        url = "https://wapside.189.cn:9001/jt-sign/paradise/conversionRights"
        data = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone},"rightsId":"{rightsId}"}},"receiveCount":1')
        }
        print_now(self.req(url, "POST", data))

    # 查询连续签到天数
    def query_signinfo(self):
        url = "https://wapside.189.cn:9001/jt-sign/reward/activityMsg"
        body = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        data = self.req(url, "post", body)
        # print(dumps(data, indent=2, ensure_ascii=0))
        recordNum = data["recordNum"]
        if recordNum != 0:
            return data["date"]["id"]
        return ""

    # 若连续签到为7天 则兑换
    def convert_reward(self):
        url = "https://wapside.189.cn:9001/jt-sign/reward/convertReward"
        try:
            rewardId = self.query_signinfo()  # "baadc927c6ed4d8a95e28fa3fc68cb9"
        except:
            rewardId = "baadc927c6ed4d8a95e28fa3fc68cb9"
        if rewardId == "":
            return
        body = {
            "para": self.telecom_encrypt(
                f'{{"phone":"{self.phone}","rewardId":"{rewardId}","month":"{date.today().__format__("%Y%m")}"}}')
        }
        for i in range(10):
            try:
                data = self.req(url, "post", body)
            except Exception as e:
                print(f"请求发送失败: " + str(e))
                sleep(6)
                continue
            print_now(data)
            if data["code"] == "0":
                break
            sleep(6)
        reward_status = self.get_coin_info()
        if reward_status:
            self.msg += f"账号{self.phone}连续签到7天兑换1元话费成功\n"
            print_now(self.msg)
            wxpush(self.msg)
        else:
            self.msg += f"账号{self.phone}连续签到7天兑换1元话费失败 明天会继续尝试兑换\n"
            print_now(self.msg)
            wxpush(self.msg)


    # 查询金豆数量
    def coin_info(self):
        url = "https://wapside.189.cn:9001/jt-sign/api/home/userCoinInfo"
        data = {
            "para": self.telecom_encrypt(f'{{"phone":{self.phone}}}')
        }
        self.coin_count = self.req(url, "post", data)
        print_now(self.coin_count)

    def author(self):
        """
        通过usercode 获取 authorization
        :return:
        """
        self.get_usercode()
        url = "https://xbk.189.cn/xbkapi/api/auth/userinfo/codeToken"
        data = {
            "usercode": self.usercode
        }
        data = post(url, headers=self.headers_live, json=data).json()
        ccc=data['data']['token']
        #print(ccc)
        a= RsaPost()
        a.init()
        b=a.get_Auth(ccc)
        #print(b)
        self.authorization = f"Bearer {b}"
        self.headers_live["Authorization"] = self.authorization
    def get_usercode(self):
        """
        授权星播客登录获取 usercode
        :return:
        """
        url = f"https://xbk.189.cn/xbkapi/api/auth/jump?userID={self.ticket}&version=9.3.3&type=room&l=renwu"
        self.headers_live = {
            "User-Agent": self.ua,
            "Host": "xbk.189.cn",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "sign": "5cf8543f835d4775a1d3cb359af45fe4"  
        }
        location = get(url, headers=self.headers_live, allow_redirects=False).headers["location"]
        usercode = findall(r"usercode=(.*?)&", location)[0]
        self.usercode = usercode
 # 获取任务列表
    def get_xbktask(self):
        url = "https://xbk.189.cn/xbkapi/lteration/liveTask/index/taskLists"
        msg = get(url,headers=self.headers_live).json()
        #print_now(msg)
        #print_now(json.dumps(msg, indent=2, ensure_ascii=False))
        if msg["code"] == 0:
            self.task_list = msg["data"]
            print_now("---------------------------------任务状态-------------------------------------------")
            print_now("")
            for task_list in self.task_list:
                for task_status in self.task_status:
                    if task_list["task_id"]==task_status["job_id"]:
                        if(task_status["job_total"]-task_status["finish_count"]!=0):
                            self.msg+=f'{task_list["title"]}----{task_status["finish_count"]}/{task_status["job_total"]}-------还需要完成{task_status["job_total"]-task_status["finish_count"]}次'
                            print_now(f'{task_list["title"]}----{task_status["finish_count"]}/{task_status["job_total"]}-------还需要完成{task_status["job_total"]-task_status["finish_count"]}次')
                        else:
                            self.msg+=f'{task_list["title"]}-----------任务已完成'
                            print_now(f'{task_list["title"]}-----------任务已完成')

                        #print_now(f'\'{task_list["title"]}\':\'{task_status["job_total"]-task_status["finish_count"]}\'')
                        a={task_list["title"]:task_status["job_total"]-task_status["finish_count"]}
                        self.task_dic.update(a)
            print_now("-----------------------------------------------------------------------------------")
            print_now(self.task_dic)

        else:
            print_now("获取任务列表失败")
            print_now(msg)
            return

    # 获取任务状态
    def get_taskStatus(self):
        url = "https://xbk.189.cn/xbkapi/lteration/liveTask/index/taskStatus"
        msg =  get(url,headers=self.headers_live).json()
        #print_now(msg)
        #print_now(json.dumps(msg, indent=2, ensure_ascii=False))
        if msg["code"] == 0:
            self.task_status = msg["data"]
            print("获取任务状态成功")

        else:
            print_now("获取任务状态失败")
            print_now(msg)
            return
            
    # 获取直播列表
    def get_liveList(self):
        url = "https://xbk.189.cn/xbkapi/api/room/index/floor?provinceCode=06&pageType=1&page=1&khd=2"
        msg = get(url,headers=self.headers_live).json()
        #print_now(msg)
        #print_now(json.dumps(msg, indent=2, ensure_ascii=False))
        if msg["code"] == 0:
            live_List = msg["data"]
            for live_list in live_List:
                self.live_List.append(live_list["liveId"])
                self.anchorId.append(live_list["anchorId"])
                

        else:
            print_now("获取任务状态失败")
            print_now(msg)
            return


    def watch_video(self):
        """
        看视频 一天可完成6次
        :return:
        """
        url = "https://xbk.189.cn/xbkapi/lteration/liveTask/index/watchVideo"
        data = {
            "articleId": 3453
        }
        data = post(url, headers=self.headers_live, json=data).json()
        if data["code"] == 0:
            print("看小视频15s完成一次")
        else:
            print(f"完成看小视频15s任务失败, 失败原因为{data['msg']}")
    def like(self):
        """
        点赞直播间 可完成5次
        :return:
        """
        url = "https://xbk.189.cn/xbkapi/lteration/room/like"
        liveId_list = self.live_List
        shuffle(liveId_list)
        for liveId in liveId_list[:5]:
            data = {
                "account": self.phone,
                "liveId": liveId
            }
            try:
                data = post(url, headers=self.headers_live, json=data).json()
                if data["code"] == 8888:
                    sleep(2)
                    print(data["msg"])
                else:
                    print(f"完成点赞直播间任务失败,原因是{data['msg']}")
            except Exception:
                print(Exception)

    def follow(self):
        """
        关注直播间 可完成1次
        :return:
        """
        url = "https://xbk.189.cn/xbkapi/api/room/index/follow"
        anchorId_list = self.anchorId
        shuffle(anchorId_list)
        for anchorId in anchorId_list[:1]:
            data = {
                "anchorId": anchorId,
                "anctionType": "1"
            }
            try:
                data = post(url, headers=self.headers_live, json=data).json()
                if data["code"] == 8888:
                    sleep(2)
                    print(data["msg"])
                else:
                    print(f"完成关注直播间任务失败,原因是{data['msg']}")
            except Exception:
                print(Exception)


    def reserve(self):
        """
        预约直播间 可完成2次
        :return:
        """
        url = "https://xbk.189.cn/xbkapi/api/room/index/reserve"
        anchorId_list = self.live_List
        shuffle(anchorId_list)
        for anchorId in anchorId_list[:5]:
            data = {
                "liveId": anchorId,
                "period": "16",
                "account": self.phone,
                "khd": "2"
            }
            try:
                data = post(url, headers=self.headers_live, json=data).json()
                if data["code"] == 8888:
                    sleep(2)
                    print(data["msg"])
                else:
                    print(f"完成关注直播间任务失败,原因是{data['msg']}")
            except Exception:
                print(Exception)


    def watch_live(self):
        # 首先初始化任务,等待15秒倒计时后再完成 可完成10次
        url = "https://xbk.189.cn/xbkapi/lteration/liveTask/index/watchLiveInit"
        live_id = randint(1000, 2700)
        data = {
            "period": 1,
            "liveId": live_id
        }
        data = post(url, headers=self.headers_live, json=data).json()
        if data["code"] == 0:
            taskcode = data["data"]
            url = "https://xbk.189.cn/xbkapi/lteration/liveTask/index/watchLive"
            data = {
                "key": taskcode,
                "period": 1,
                "liveId": live_id
            }
            print("正在等待15秒")
            for k in range(15):
                sleep(1)
                print_now(f'请继续等待{15-k}秒，完成下一次任务')
            data = post(url, headers=self.headers_live, json=data).json()
            if data["code"] == 0:
                print("完成1次观看直播任务")
            else:
                print(f"完成观看直播任务失败,原因是{data['msg']}")
        else:
            print(f"初始化观看直播任务失败，失败原因为{data['msg']}")

    def get_userid(self):
        url = "https://wapside.189.cn:9001/jt-sign/api/home/homeInfo"
        body = {
            "para": self.telecom_encrypt(f'{{"phone":"{self.phone}","signDate":"{datetime.now().__format__("%Y-%m")}"}}')
        }
        userid = post(url, json=body).json()["data"]["userInfo"]["userThirdId"]
        return userid
   
   
   
   
    def share(self):
        """
        50的分享任务 token不做校检 有值即可 若登录成功了 使用自己的token 否则生成随机的token
        :return:
        """
        url = "https://appfuwu.189.cn:9021/query/sharingGetGold"
        body = {
            "headerInfos": {
                "code": "sharingGetGold",
                "timestamp": datetime.now().__format__("%Y%m%d%H%M%S"),
                "broadAccount": "",
                "broadToken": "",
                "clientType": "#9.6.1#channel50#iPhone 14 Pro Max#",
                "shopId": "20002",
                "source": "110003",
                "sourcePassword": "Sid98s",
                "token": self.token if self.token != "" else self.geneRandomToken(),
                "userLoginName": self.phone
            },
            "content": {
                "attach": "test",
                "fieldData": {
                    "shareSource": "3",
                    "userId": self.get_userid(),
                    "account": TelecomLogin.get_phoneNum(self.phone)
                }
            }
        }
        headers = {
            "user-agent": "iPhone 14 Pro Max/9.6.1"
        }
        data = post(url, headers=headers, json=body).json()
        print_now(data)
 
 
 
 
 
    def main(self):
        self.init()
        #self.chech_in()
        #self.get_task()
        #self.do_task()
        if foods != 0:
            for i in range(foods):
                self.food()
        # self.convert_reward()
        if datetime.now().day == 1:
            self.get_level()
        #self.share()
        if self.ticket != "":
            self.author()
            self.get_taskStatus()
            self.get_xbktask()
            for i in range(self.task_dic["观看短视频15s +5金豆"]):
                print_now("现在开始完成【观看短视频15s +5金豆】任务")
                try:
                    self.watch_video()
                except Exception:
                    print(Exception)
                for k in range(15):
                    sleep(1)
                    print_now(f'请继续等待{15-k}秒，完成下一次任务')
            for i in range(self.task_dic["观看直播15s +5金豆"]):
                print_now("现在开始完成【观看直播15s +5金豆】任务")
                try:
                    self.watch_live()
                    self.get_taskStatus()
                    self.get_xbktask()
                except Exception:
                        print(Exception)
            self.get_liveList()
            if self.task_dic["点赞直播 +1金豆"]!=0:
                self.like()
            try:

                if self.task_dic["关注直播 +5金豆"]!=0:
                    try:
                        self.follow()
                    except Exception:
                            print(Exception)
            except Exception:
                        print(Exception)
            if self.task_dic["预约直播 +5金豆"]!=0:
                try:
                    self.reserve()
                except Exception:
                        print(Exception)


        self.coin_info()
        self.msg += f"你账号{self.phone} 当前有金豆{self.coin_count['totalCoin']}"
        wxpush(self.msg)
    def get_coin_info(self):
        url = "https://wapside.189.cn:9001/jt-sign/api/getCoinInfo"
        decrept_para = f'{{"phone":"{self.phone}","pageNo":0,"pageSize":10,type:"1"}}'
        data = {
            "para": self.telecom_encrypt(decrept_para)
        }
        data = self.req(url, "POST", data)
        if "skuName" in data["data"]["biz"]["results"][0] and "连续签到" in data["data"]["biz"]["results"][0]["skuName"]:
            return True
        return False


if __name__ == "__main__":
  
    #QQ交流群495669534
    param = "手机号&服务密码"
    if param == "" :
        print("未填写相应变量 退出")
        exit(0)  
    for x in param.split('\n') :
        tmp = x.split('&')
        if len(tmp) < 2 :
            continue
        print("===================手机号:"+ tmp[0]+"===================")

        phone=tmp[0]
        password=tmp[1]
        foods = int(float(get_environ("TELECOM_FOOD", 0, False)))
        if phone == "":
            exit(0)
        if password == "":
            print_now("电信服务密码未提供 只执行部分任务")
        if datetime.now().hour + (8 - int(strftime("%z")[2])) == 111:
            telecom = ChinaTelecom(phone, password, False)
            telecom.init()
            telecom.convert_reward()
        else:
            telecom = ChinaTelecom(phone, password)
            telecom.main()
