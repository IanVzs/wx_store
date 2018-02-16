#!/usr/bin/env python
# coding=utf8

import re
import time
import urllib
import urllib2
import httplib
import sys
reload(sys)
from sys import path
import setting
import logging
import xlwt


sys.setdefaultencoding('utf-8')

def setting_from_object(obj):
    setting = dict()
    for key in dir(obj):
        if key.isupper():
            setting[key.lower()] = getattr(obj, key)
        else:
            setting[key] = getattr(obj, key)
    return setting


def find_subclasses(klass, include_self=False):
    accum = []
    for child in klass.__subclasses__():
        accum.extend(find_subclasses(child, True))
    if include_self:
        accum.append(klass)
    return accum


def vmobile(mobile):
    return re.match(r"1[0-9]{10}", mobile)


def vemail(email):
    return re.match(r"^(\w)+(\.\w+)*@(\w)+((\.\w{2,3}){1,3})$", email)


def sendmsg( mobile, content, isyzm):
    if isyzm:
        sms_param = setting.SMS_PARAM_YZM.split(',')
        sms_url = sms_param[0]
        username = sms_param[1]
        pwd = sms_param[2]
        signname=sms_param[3]
        # result = client.service.SendSMSYZM(mobile, content, signtype, isyzm)
    else:
        sms_param = setting.SMS_PARAM_YX.split(',')
        sms_url = sms_param[0]
        username = sms_param[1]
        pwd = sms_param[2]
        signname=sms_param[3]
        # result = client.service.SendSMSYX(mobile, content)
    # print result
    # http://api.bjszrk.com/sdk/BatchSend.aspx?CorpID=test&Pwd=test&Mobile=13999999999&Content=ABC&Cell=&SendTime=&encode=utf-8
    content = content + '【' + signname + '】'
    values={'CorpID':username,'Pwd':pwd,'Mobile':mobile,'Content':content,'encode':'utf-8'}
    data = urllib.urlencode(values)
    req = urllib2.Request(sms_url, data)
    response = urllib2.urlopen(req)
    result = response.read()


class WriteXML(object):
    def __init__(self, name):
        self.f = xlwt.Workbook()  # 创建工作簿
        self.sheet = self.f.add_sheet(u'sheet1', cell_overwrite_ok=True)  # 创建sheet
        self.title_style = self.set_style('Times New Roman', 220, True)
        self.body_style = self.set_style('Arial', 220, False)
        self.name = name

    def set_style(self, name, height, bold=False):
        style = xlwt.XFStyle()  # 初始化样式
        font = xlwt.Font()  # 为样式创建字体
        font.name = name  # 'Times New Roman'
        font.bold = bold
        font.color_index = 4
        font.height = height
        style.font = font
        return style

    def write_excel(self, style, row, line):
        if style == 'title':
            style = self.title_style
        else:
            style = self.body_style
        for i, r in enumerate(row):
            self.sheet.write(line, i, r, style)

    def save(self):
        self.f.save(self.name)






