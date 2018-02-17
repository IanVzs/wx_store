# -*- coding: utf-8 -*-

import auth
from yzclient import YZClient
import requests
import simplejson
import setting
import logging


def get_yz_token():
    data = {'client_id': setting.client_id, 'client_secret': setting.client_secret,
            'grant_type': setting.grant_type, 'kdt_id': setting.kdt_id}
    headers = {'content-type': setting.content_type}
    url = setting.token_url
    r = requests.post(url, data=data, headers=headers)
    return simplejson.loads(r.text)['access_token']

class YzScore():
    def get_token(self):
        self.token = get_yz_token()

    def prepare(self):
        pass

    def minus_score(self, points, fans_id):
        if not (isinstance(points, int) and points > 0):
            return
        token = auth.Token(token=self.token)
        client = YZClient(token)
        params = {'points': points, 'fans_id': fans_id}
        files = []
        print client.invoke('youzan.crm.customer.points.decrease', '3.0.1', 'GET', params=params, files=files)

    def add_score(self, points, mobile='', fans_id=''):
        auth_token = auth.Token(token=self.token)
        client = YZClient(auth_token)
        if mobile:
            params = {'points': points, 'mobile': mobile}
        else:
            params = {'points': points, 'fans_id': fans_id}
        files = []
        result = client.invoke('youzan.crm.customer.points.increase', '3.0.1', 'GET', params=params, files=files)
        print('add_score: %s' % result)
        logging.info('add_score: %s' % result)

    def change_log(self, fans_id, start_date, end_date):
        token = auth.Token(token=self.token)
        client = YZClient(token)
        params = {'fans_id': fans_id, 'start_date': start_date, 'end_date': end_date}
        files = []
        print client.invoke('youzan.crm.customer.points.changelog.get', '3.0.1', 'GET', params=params, files=files)

    def get_score(self, mobile='', open_user_id=''):
        token = auth.Token(token=self.token)
        client = YZClient(token)
        params = {}                     # {'open_user_id': open_user_id}
        if mobile:
            params['mobile'] = mobile      # '15929925857'
        else:
            params['open_user_id'] = open_user_id
        files = []
        print client.invoke('youzan.crm.fans.points.get', '3.0.1', 'GET', params=params, files=files)

    def get_user_tag(self):
        token = auth.Token(token=self.token)  # auth.Sign(app_id='app_id', app_secret='app_secret')
        client = YZClient(token)
        params = {}
        params['weixin_openid'] = "oMTlE1a08XjUGNKArU7V0ieQRMXc"
        files = []
        print client.invoke('youzan.users.weixin.follower.tags.get', '3.0.0', 'GET', params=params, files=files)

    def get_user_openid(self, mobile):
        auth_token = auth.Token(token=self.token)
        client = YZClient(auth_token)
        params = {'mobile': mobile, 'country_code': '+86'}
        files = []
        result = client.invoke('youzan.user.weixin.openid.get', '3.0.0', 'GET', params=params, files=files)
        print result
        logging.info('result=%s' % result)
        if 'response' in result:
            return result['response']['open_id']
        else:
            return None

    def funs_info(self, openid):
        token = auth.Token(token=self.token)
        client = YZClient(token)
        params = {'weixin_openid': openid}
        files = []
        r = client.invoke('youzan.users.weixin.follower.get', '3.0.0', 'GET', params=params, files=files)
        print r
        true = True
        exec("m="+r)
        return m


import qrcode
import time
class QrCode():
    def createqrcode(self, num, content='default content'):
        qr = qrcode.make(content)
        filename = str(num) + '_' + str(time.time())[1:10] + '.jpeg'
        qr.save(filename, format='jpeg')


if __name__ == '__main__':
    pass
    # list_qr = ["http://wxstore.solrxchina.com/fans_id/v1/qrcode/1/999999998"]
    # for i, url in enumerate(list_qr):
	 #    QrCode().createqrcode(i, url)

    # Yz_User = YzScore()
    # Yz_User.get_token()
    # Yz_User.funs()
    # print 'oMTlE1a08XjUGNKArU7V0ieQRMXc'
    #
    yz_score = YzScore()
    yz_score.get_token()
    #yz_score.get_user_info('15929925857')
    #'{"error_response":{"msg":"您的手机号尚未注册，请先注册","code":135200013}}'
    #yz_score.get_user_openid("15929925857") # 查询OpenID
    #yz_score.get_score("15929925857", "oMTlE1a08XjUGNKArU7V0ieQRMXc")   # 获取用户积分（手机可行OpenID无法找到）
    yz_score.funs_info("oMTlE1a08XjUGNKArU7V0ieQRMXc")  # 查询用户全部信息
    # print(len('{"response":{"user":{"sex":"m","tags":[],"is_follow":true,"points":48,"traded_num":0,"traded_money":"0.00","level_info":{},"user_id":4917946994,"weixin_openid":"oMTlE1a08XjUGNKArU7V0ieQRMXc","nick":"roi","avatar":"http:\/\/wx.qlogo.cn\/mmopen\/CyXNIiaoCwfmRHWR2mFpCgKVZ0ekyPGTNXAibdvbOjf4pbeuOojhJibSIEb00XmJqiciaS94VLsKhnhqyQnPic3VHxriapNMob0vCOx\/132","follow_time":1517811113,"province":"\u9655\u897f","city":"","union_id":"oAE9E0kssuh7J66tFGBP7_rElq0A"}}}'))
