#!/usr/bin/env python
# coding=utf-8

import time
from peewee import *
import hashlib
from bootloader import db
from lib.util import vmobile
import re


# 地区表
class Area(db.Model):
    id = PrimaryKeyField()
    pid = ForeignKeyField('self', db_column='pid', null=True)  # 父级ID
    code = CharField(max_length=40)  # 编码
    has_sub = IntegerField(default=0)  # 是否拥有下级
    name = CharField(max_length=30)  # 名称
    spell = CharField(max_length=50)  # 拼音
    spell_abb = CharField(max_length=30)  # 拼音缩写

    @classmethod
    def get_detailed_address(cls, area_code):
        try:
            area_code_len = len(area_code)
            area = Area.get(code=area_code)
            if area_code_len == 12:
                address = area.pid.pid.name + area.pid.name + area.name
            elif area_code_len == 8:
                address = area.pid.name + area.name
            else:
                address = area.name
            return address
        except:
            return ''

    @staticmethod
    def get_area_name(area_code):
        try:
            name = Area.get(code=area_code).name
        except Exception, e:
            name = None
        return name

    class Meta:
        db_table = 'area'


# 后台用户表
class AdminUser(db.Model):
    id = PrimaryKeyField()  # 主键
    username = CharField(unique=True, max_length=32, null=False)  # 注册用户名
    password = CharField(max_length=32)  # 密码
    mobile = CharField(max_length=12)  # 手机号
    email = CharField(max_length=128)  # email
    code = CharField(max_length=20)  # 业务推广人员编号
    roles = CharField(max_length=8)  # D开发人员；A管理员；Y运营；S市场；K客服；C财务；（可组合，如：DA）
    created = IntegerField(default=0)  # 注册时间
    last_login = IntegerField(default=0)  # 最后登录时间
    active = IntegerField(default=1)  # 状态 0删除 1有效

    @staticmethod
    def create_password(raw):
        return hashlib.new("md5", raw).hexdigest()

    def check_password(self, raw):
        return hashlib.new("md5", raw).hexdigest() == self.password

    def updatesignin(self):
        self.lsignined = int(time.time())
        self.save()

    class Meta:
        db_table = 'admin_user'


# # 后台用户操作日志
# class AdminUserLog(db.Model):
#     id = PrimaryKeyField()  # 主键
#     admin_user = ForeignKeyField(AdminUser, related_name='logs', db_column='admin_user_id')  # 后台人员
#     created = IntegerField(default=0)  # 创建时间
#     content = CharField(max_length=2048)  # 日志内容
#
#     class Meta:
#         db_table = 'tb_admin_users_log'


# 用户表
class User(db.Model):
    id = PrimaryKeyField()  # 主键
    openid = CharField(unique=True, max_length=255)
    name = CharField(max_length=32)  # 姓名
    mobile = CharField(max_length=32)  # 电话
    code = CharField(max_length=32)  # 推广码
    pid = IntegerField(default=0)  # 由哪个用户推广而来，上级用户ID
    store_manager = IntegerField(null=False)  #
    grade = CharField(default='')  # 空普通会员 A实体店店长 B线上分销者 C线下qrcode分销者
    level = IntegerField(default=1)  # 分销级别
    yz_user_info = TextField(default='')  # 有赞用户信息
    created = IntegerField(default=0)  # 注册时间
    token = CharField()  # 推广码

    class Meta:
        db_table = 'user'


# 商品分类
class Category(db.Model):
    id = PrimaryKeyField()
    name = CharField(max_length=20)  # 分类名
    active = IntegerField(default=1)  # 状态 0删除 1有效

    class Meta:
        db_table = 'category'


# 商品
class Product(db.Model):
    id = PrimaryKeyField()
    name = CharField(max_length=225)  # 商品名称
    category = ForeignKeyField(Category, related_name='products', db_column='category')  # 商品分类
    resume = CharField()  # 简单介绍
    score_buy = IntegerField()  # 购买赠送积分
    score_referrer = IntegerField()  # 推荐者赠送积分
    price = IntegerField()  # 价格
    count = IntegerField()  # 次数
    number = IntegerField()  # 总数量
    created = IntegerField(default=0)  # 添加时间
    active = IntegerField(default=1)  # 0删除 1正常

    class Meta:
        db_table = 'product'


# 商品
class ScoreRecord(db.Model):
    id = PrimaryKeyField()
    user = ForeignKeyField(User, related_name='score_records', db_column='user')  # 得积分的用户
    sub_user = ForeignKeyField(User, db_column='sub_user', default=0)  # 下线（当下线购买qr产品时给他送的积分）
    product = ForeignKeyField(Product, related_name='score_records', db_column='product')  # 商品名称
    qrcode_num = IntegerField()  # 简单介绍
    score = IntegerField()  # 购买赠送积分
    info = CharField(default='')  # 简介
    created = IntegerField(default=0)  # 添加时间
    active = IntegerField(default=1)  # 0删除 1正常

    @staticmethod
    def check_added():  # 检查该二维码是否加过积分
        pass

    class Meta:
        db_table = 'score_record'


def init_db():
    from lib.util import find_subclasses
    models = find_subclasses(db.Model)
    for model in models:
        if model.table_exists():
            model.drop_table()
        model.create_table()


if __name__ == '__main__':
    # init_db()
    User.create(id=1, name='agu')
    pass
