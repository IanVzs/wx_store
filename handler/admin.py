#!/usr/bin/env python
# coding=utf8

import setting
import simplejson
import qrcode
import time
import os
import handler
import logging
import uuid
import traceback
from lib.give_score.demo import YzScore
from handler import BaseHandler, AdminBaseHandler, WXBaseHandler
from lib.route import Route
from lib.model import *


# ---------------------------------------------后台---------------------------------------------------
@Route(r'/index', name='index')  # 后台首页
class IndexHandler(AdminBaseHandler):
    def get(self):
        data = self.get_argument('data', '')
        self.render('admin/picture_edit.html', active='pic', data=data)


@Route(r'/admin/login', name='admin_login')  # 后台登录
class LoginHandler(BaseHandler):
    def get(self):
        self.render('admin/login.html')

    def post(self):
        username = self.get_argument("username", None)
        password = self.get_argument("password", None)
        if username and password:
            try:
                user = AdminUser.get(AdminUser.username == username)
                if user.check_password(password):
                    if user.active == 1:
                        user.updatesignin()
                        session, sessionid = self.session
                        session['admin'] = (user, sessionid)
                        session.save()
                        # session._store.delete_former_session(user, sessionid)
                        return self.redirect("/admin/products")
                    else:
                        return self.flash("此账户被禁止登录，请联系管理员。")
                else:
                    self.flash("密码错误")
            except Exception, e:
                logging.info(traceback.format_exc())
                self.flash("此用户不存在")
        else:
            self.flash("请输入用户名密码")
        self.render("/admin/login.html", next=self.next_url)


@Route(r'/admin/logout', name='admin_logout')  # 后台退出
class LogoutHandler(AdminBaseHandler):
    def get(self):
        if "admin" in self.session[0]:
            del self.session[0]["admin"]
            self.session[0].save()
        self.render('admin/login.html')


@Route(r'/admin/products', name='admin_products')  # 产品列表
class ProductHandler(AdminBaseHandler):
    def get(self):
        page = int(self.get_argument("page", '1'))
        # category = self.get_argument('category', 1)
        keyword = self.get_argument("keyword", None)
        active = int(self.get_argument("status", 1))
        pagesize = setting.ADMIN_PAGESIZE
        ft = (Product.id > 0)
        if active:
            ft &= (Product.active == active)
        if keyword:
            ft &= (Product.name.contains(keyword))
        products = Product.select().where(ft)
        total = products.count()
        if total % pagesize > 0:
            totalpage = total / pagesize + 1
        else:
            totalpage = total / pagesize
        products = products.order_by(Product.created.desc()).paginate(page, pagesize).aggregate_rows()
        # categories = Category.select().where(Category.active==1)

        self.render('admin/product.html', active='p_product', products=products, total=total,
                    page=page, pagesize=pagesize, totalpage=totalpage,
                    keyword=keyword, status=active, pid=[])


@Route(r'/admin/product_edit/(\d+)', name='admin_product_edit')  # 产品添加
class ProductEditHandler(AdminBaseHandler):
    def get(self, pid):
        pid = int(pid)
        product = None
        if 0 < pid:
            product = Product.get(id=pid)

        self.render('admin/product_edit.html', active='product', product=product)

    def post(self, pid):
        result = {'flag': 0, 'msg': ''}
        name = self.get_body_argument('name', None)
        price = self.get_body_argument('price', None)
        price = float(price) if price else 0
        score_referrer = self.get_body_argument('score_referrer', None)
        score_referrer = int(score_referrer) if score_referrer else 0
        score_buy = self.get_body_argument('score_buy', None)
        score_buy = int(score_buy) if score_buy else 0
        number = self.get_body_argument('number', None)
        number = int(number) if number else 0

        resume = self.get_body_argument('resume', '')

        if pid == '0':
            product = Product()
            product.created = int(time.time())
            product.active = 1
        else:
            product = Product.get(id=pid)
        product.name = name
        product.price = price
        product.score_referrer = score_referrer
        product.score_buy = score_buy
        product.resume = resume
        product.number = number
        product.save()

        # if pid == '0':
        #     content = '添加商品:p_id%d' % product.id
        # else:
        #     content = '编辑商品:p_id%s' % pid
        # AdminUserLog.create(admin_user=self.get_admin_user(), created=int(time.time()), content=content)
        result['flag'] = 1
        self.write(simplejson.dumps(result))


@Route(r'/admin/product_del/(\d+)', name='admin_product_del')  # 产品删除
class ProductDelHandler(AdminBaseHandler):
    def get(self, pid):
        pid = int(pid)
        try:
            product = Product.get(id=pid)
            product.active = 0
            product.save()
        except:
            pass
        self.redirect('/admin/products')


#----------------------------------------------------------------------------
"""后台用户管理"""
#----------
@Route(r'/admin/admin_user', name='admin_admin_user')  # 后台管理用户列表
class AdminUserHandler(AdminBaseHandler):
    def get(self):
        page = int(self.get_argument("page", '1'))
        # category = self.get_argument('category', 1)
        keyword = self.get_argument("keyword", None)
        active = int(self.get_argument("status", 1))
        pagesize = setting.ADMIN_PAGESIZE
        ft = (AdminUser.id > 0)
        if active:
            ft &= (AdminUser.active == active)
        if keyword:
            ft &= (AdminUser.username.contains(keyword))
        adminUsers = AdminUser.select().where(ft)
        total = adminUsers.count()
        if total % pagesize > 0:
            totalpage = total / pagesize + 1
        else:
            totalpage = total / pagesize
        adminUsers = adminUsers.order_by(AdminUser.created.desc()).paginate(page, pagesize).aggregate_rows()
        # categories = Category.select().where(Category.active==1)

        self.render('admin/admin_user.html', active='admin_user', adminUsers=adminUsers, total=total,
                    page=page, pagesize=pagesize, totalpage=totalpage,
                    keyword=keyword, status=active, pid=[])

@Route(r'/admin/admin_user_edit/(\d+)', name='admin_admin_user_edit')  # 后台用户添加
class AdminUserEditHandler(AdminBaseHandler):
    def get(self, pid):
        pid = int(pid)
        adminUser = None
        if 0 < pid:
            adminUser = AdminUser.get(id=pid)

        self.render('admin/admin_user_edit.html', active='admin_user', adminUser=adminUser)

    def post(self, pid):
        result = {'flag': 0, 'msg': ''}
        username = self.get_body_argument('username', None)
        mobile = self.get_body_argument('mobile', None)
        email = self.get_body_argument('email', None)
        password = self.get_body_argument('password', None)

        if pid == '0':
            adminUser = AdminUser()
            adminUser.created = int(time.time())
            adminUser.active = 1
        else:
            adminUser = AdminUser.get(id=pid)
        adminUser.username = username
        adminUser.mobile = mobile
        adminUser.email = email
        adminUser.password = AdminUser.create_password(password)
        adminUser.save()

        result['flag'] = 1
        self.write(simplejson.dumps(result))

@Route(r'/admin/admin_user_del/(\d+)', name='admin_admin_user_del')  # 用户删除
class AdminUserDelHandler(AdminBaseHandler):
    def get(self, pid):
        pid = int(pid)
        try:
            adminUser = AdminUser.get(id=pid)
            adminUser.active = 0
            adminUser.save()
        except:
            pass
        self.redirect('/admin/admin_admin_user')
#-----------------------------------------------------------------------------

@Route(r'/admin/shop_manager', name='admin_shop_manager')  # 店长列表
class AdminShopManagerHandler(AdminBaseHandler):
    def get(self):
        page = int(self.get_argument("page", '1'))
        keyword = self.get_argument("keyword", None)
        pagesize = setting.ADMIN_PAGESIZE
        ft = User.grade.contains('A')
        if keyword:
            ft &= (User.name.contains(keyword))
        users = User.select().where(ft)
        total = users.count()
        if total % pagesize > 0:
            totalpage = total / pagesize + 1
        else:
            totalpage = total / pagesize
        users = users.paginate(page, pagesize)

        self.render('admin/shop_manager.html', active='shop_manager', users=users, total=total,
                    page=page, pagesize=pagesize, totalpage=totalpage, keyword=keyword)


@Route(r'/admin/user', name='admin_user')  # 客户列表
class UserHandler(AdminBaseHandler):
    def get(self):
        page = int(self.get_argument("page", '1'))
        keyword = self.get_argument("keyword", None)
        pagesize = setting.ADMIN_PAGESIZE
        ft = User.grade.contains('C')
        if keyword:
            ft &= (User.name.contains(keyword))
        users = User.select().where(ft)
        total = users.count()
        if total % pagesize > 0:
            totalpage = total / pagesize + 1
        else:
            totalpage = total / pagesize
        users = users.paginate(page, pagesize)

        self.render('admin/user.html', active='user', users=users, total=total,
                    page=page, pagesize=pagesize, totalpage=totalpage, keyword=keyword)


@Route(r'/admin/manager', name='admin_manager')  # 店长添加
class ManagerHandler(AdminBaseHandler):
    def get(self):
        province = self.get_argument("province", '')
        city = self.get_argument("city", '')
        keyword = self.get_argument("keyword", '')
        page = int(self.get_argument("page", '1') if len(self.get_argument("page", '1')) > 0 else '1')
        pagesize = self.settings['admin_pagesize']
        status = self.get_argument("status", '')
        download = self.get_argument('download', '')
        default_province = ''
        default_city = ''
        ft = (User.status != 0)
        if status:
            status = int(status)
            ft = (User.status == status)
        if city and city != '':
            default_province = city[:4]
            default_city = city
            city += '%'
            ft &= (User.area_code % city)
        elif province and province != '':
            default_province = province
            province += '%'
            ft &= (User.area_code % province)
        if keyword:
            ft &= ((User.name.contains(keyword)) | (User.mobile.contains(keyword)))

        cfs = User.select().where(ft)
        # if download == '1':
        #     fp = open('/home/www/workspace/czj/upload/stores.csv', 'w')
        #     fp.write(u'店名,联系人,电话,地址,详细地址,创建时间,自注册起出单数,积分\n'.encode('gb18030'))
        #     for store in Store.select().where(ft).order_by(Store.area_code.asc()):
        #         io_count = InsuranceOrder.select().where(InsuranceOrder.store == store,
        #                                                  InsuranceOrder.status == 3).count()
        #         string = '%s,%s,%s,%s,%s,%s,%s,%s\n' % (store.name, store.linkman, store.mobile,
        #                                                 Area.get_detailed_address(store.area_code), store.address,
        #                                                 time.strftime('%Y-%m-%d', time.localtime(store.created)),
        #                                                 io_count, store.score)
        #         fp.write(string.encode('gb18030'))
        #     fp.close()
        #     self.redirect('/upload/stores.csv')
        total = cfs.count()
        if total % pagesize > 0:
            totalpage = total / pagesize + 1
        else:
            totalpage = total / pagesize if (total / pagesize) > 0 else 1
        cfs = cfs.paginate(page, pagesize)
        items = Area.select().where(Area.pid == 0)
        print(items.count())
        self.render('/admin/manager.html', users=cfs, total=total, page=page, pagesize=pagesize,
                    totalpage=totalpage, active='manager', status=status, keyword=keyword, Area=Area, items=items,
                    province=default_province, city=default_city)


@Route(r'/admin/manager_del/(\d+)', name='admin_manager_del')  # 店长删除
class ManagerDelHandler(AdminBaseHandler):
    def get(self, pid):
        pid = int(pid)
        try:
            product = Product.get(id=pid)
            product.active = 0
            product.save()
        except:
            pass
        self.redirect('/admin/products')


@Route(r'/admin/upload_file', name='admin_upload_file')  # 图片上传
class UploadFileHandler(AdminBaseHandler):
    def get(self):
        data = self.get_argument('data', '')
        self.render('admin/add_file.html', active='pic', data=data)


@Route(r'/admin/recommend', name='admin_recommend')  # 推荐奖励
class RecommendHandler(AdminBaseHandler):
    def get(self):
        rules = Rule.select().where(Rule.type == 1, Rule.active == 1)
        self.render('admin/recommend.html', active='recommend', rules=rules)


@Route(r'/admin/recommend_edit/(\d+)', name='admin_recommend_edit')  # 推荐奖励添加
class RecommendEditHandler(AdminBaseHandler):
    def get(self, pid):
        pid = int(pid)
        rule = None
        if 0 < pid:
            rule = Rule.get(id=pid)

        self.render('admin/recommend_edit.html', active='recommend', rule=rule)

    def post(self, pid):
        result = {'flag': 0, 'msg': ''}
        score = self.get_body_argument('score', None)
        score = int(score) if score else 0
        number = self.get_body_argument('number', None)
        number = int(number) if number else 0

        if pid == '0':
            rule = Rule()
            rule.created = int(time.time())
            rule.active = 1
            rule.type = 1
        else:
            rule = Rule.get(id=pid)
        rule.score = score
        rule.number = number
        rule.save()
        result['flag'] = 1
        self.write(simplejson.dumps(result))


@Route(r'/admin/recommend_del/(\d+)', name='admin_recommend_del')  # 产品删除
class RecommendDelHandler(AdminBaseHandler):
    def get(self, pid):
        pid = int(pid)
        try:
            rule = Rule.get(id=pid)
            rule.active = 0
            rule.save()
        except:
            pass
        self.redirect('/admin/recommend')


@Route(r'/admin/consumption', name='admin_consumption')  # 消费奖励
class ConsumptionHandler(AdminBaseHandler):
    def get(self):
        rules = Rule.select().where(Rule.type == 0, Rule.active == 1)
        self.render('admin/consumption.html', active='consumption', rules=rules)


@Route(r'/admin/consumption_edit/(\d+)', name='admin_consumption_edit')  # 推荐奖励添加
class ConsumptionEditHandler(AdminBaseHandler):
    def get(self, pid):
        pid = int(pid)
        rule = None
        if 0 < pid:
            rule = Rule.get(id=pid)

        self.render('admin/consumption_edit.html', active='consumption', rule=rule)

    def post(self, pid):
        result = {'flag': 0, 'msg': ''}
        score = self.get_body_argument('score', None)
        score = int(score) if score else 0
        number = self.get_body_argument('number', None)
        number = int(number) if number else 0

        if pid == '0':
            rule = Rule()
            rule.created = int(time.time())
            rule.active = 1
            rule.type = 0
        else:
            rule = Rule.get(id=pid)
        rule.score = score
        rule.number = number
        rule.save()
        result['flag'] = 1
        self.write(simplejson.dumps(result))


@Route(r'/admin/consumption_del/(\d+)', name='admin_consumption_del')  # 产品删除
class ConsumptionDelHandler(AdminBaseHandler):
    def get(self, pid):
        pid = int(pid)
        try:
            rule = Rule.get(id=pid)
            rule.active = 0
            rule.save()
        except:
            pass
        self.redirect('/admin/consumption')


@Route(r'/admin/area_statistics', name='admin_area_statistics')  # 地区统计
class AreaStatisticsHandler(AdminBaseHandler):
    def get(self):
        province = self.get_argument('begin_date', '')
        begin_date = self.get_argument('begin_date', '')
        end_date = self.get_argument('end_date', '')
        download = self.get_argument('download', '')
        begin = None
        end = None
        if begin_date and end_date:
            begin = time.mktime(time.strptime(begin_date + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
            end = time.mktime(time.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        else:
            begin = time.mktime(time.strptime(time.strftime('%Y-%m', time.localtime()), "%Y-%m"))
            end = time.time()

        self.render('admin/area_statistics.html', active='area_statistics', begin_date=begin_date,
                    end_date=end_date)


@Route(r'/admin/manager_statistics', name='admin_manager_statistics')  # 店长统计
class ManagerStatisticsHandler(AdminBaseHandler):
    def get(self):
        province = self.get_argument('begin_date', '')
        begin_date = self.get_argument('begin_date', '')
        end_date = self.get_argument('end_date', '')
        download = self.get_argument('download', '')
        begin = None
        end = None
        if begin_date and end_date:
            begin = time.mktime(time.strptime(begin_date + " 00:00:00", "%Y-%m-%d %H:%M:%S"))
            end = time.mktime(time.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S"))
        else:
            begin = time.mktime(time.strptime(time.strftime('%Y-%m', time.localtime()), "%Y-%m"))
            end = time.time()

        self.render('admin/area_statistics.html', active='area_statistics', begin_date=begin_date,
                    end_date=end_date)


# ---------------------------------------------微信端---------------------------------------------------
@Route(r'/mobile/v1/qrcode/(\d+)/(\d+)', name='mobile_qrcode')  # 扫描二维码
class MobileQrcodeHandler(WXBaseHandler):
    def create_user(self, openid, nickname, mobile, yz_user_info):
        try:
            user = User()
            user.name = nickname
            user.token = setting.user_token_prefix + str(uuid.uuid4())
            user.openid = openid
            user.mobile = mobile
            user.created = int(time.time())
            user.grade = 'C'
            user.yz_user_info = yz_user_info
            user.save()
            return user
        except Exception:
            logging.log(traceback.format_exc())
            return None

    def create_yz_user(self):
        pass

    def add_score(self, user, product_id, num, yz, fans_id):
        product_id = int(product_id)
        num = int(num)
        if ScoreRecord.select(id).where(ScoreRecord.product == product_id, ScoreRecord.qrcode_num == num,
                                     ScoreRecord.active == 1).count() == 0:
            try:
                product = Product.get(id=product_id)
            except:
                logging.info('Warning: product not found, product id=%s' % product_id)
                return
            # 调用接口加积分
            yz.add_score(product.score_buy, fans_id=fans_id)
            ScoreRecord.create(user=user, product=product_id, qrcode_num=num, score=product.score_buy,
                               info=u'购买二维码产品赠送积分', created=int(time.time()))
            if user.pid > 0:
                try:
                    p_user = User.get(id=user.pid)
                    if 'A' not in p_user.grade:
                        yz.add_score(product.score_referrer, mobile=p_user.mobile)
                        ScoreRecord.create(user=p_user, product=product_id, qrcode_num=num, score=product.score_referrer,
                                           info=u'下线购买二维码产品赠送积分', created=int(time.time()), sub_user=user)
                except:
                    logging.info('Warning: product not found, product id=%s' % product_id)
                    return

    def get(self, product_id, num):
        code = self.get_argument('code', '')
        openid, _ = handler.get_access_token_from_code(code)
        logging.info('----------%s' % openid)
        if openid in ['', None, 'NULL', 'None']:
            url = 'http%3A%2F%2Fwxstore.solrxchina.com%2Fmobile%2Fv1%2Fqrcode%2F' + str(product_id) + '%2F' + str(num)
            self.redirect("https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx831c87012e567c2e&"
                          "redirect_uri=" + url + "&response_type=code&scope=snsapi_base")
            return
        Yz = YzScore()
        Yz.get_token()
        users = User.select().where(User.openid == openid)
        if users.count() >= 1:
            user = users[0]
            token = user.token
            token = self.update_token(token)
            user.token = token
            self.set_token(user.token, user.id)
            if 'A' not in user.grade:
                try:
                    fans_id = simplejson.loads(user.yz_user_info)['response']['user']['user_id']
                    self.add_score(user, product_id, num, Yz, fans_id)

                    _product = Product.select().where(Product.id == product_id)
                    price = _product.price
                    user.amount_of_consumption += price
                    user.save()
                    p_ruleIDs = Rule.select().where(Rule.number < user.amount_of_consumption, Rule.type == 0)  # 符合奖励积分条件的所有
                    if p_ruleIDs.count() > 0:
                        # 满足最低增加积分要求
                        recorders = ScoreRecord.select().where(ScoreRecord.user == user.id)
                        ruleRecoder = []
                        for recorde in recorders:
                            ruleRecoder.append(recorde.rule)  # 此用户所有已经完成的推荐奖励 id
                        for __id in p_ruleIDs:
                            if __id.id not in ruleRecoder:
                                # 如此奖励未发放
                                score = Rule.get(id=__id.id)
                                Yz.add_score(score, fans_id=fans_id)  # 增加积分
                                # 添加记录
                                record = ScoreRecord()
                                record.user = user.id
                                record.score = score
                                record.info = u'下线购买二维码产品赠送积分'
                                record.created = time.time()
                                record.rule = __id.id
                                record.save()
                except:
                    pass
            self.redirect('https://h5.youzan.com/v2/usercenter/8sbIpUkeGQ?reft=1518450450886&spm=f69815501')
        else:
            access_token = handler.get_access_token()
            userinfo = handler.get_user_info(access_token, openid)
            logging.info('-----wx user info: %s' % userinfo)
            if 'nickname' in userinfo:
                self.application.memcachedb.set(str(product_id)+str(num), openid, setting.user_expire)
                self.render('wx/qrcode.html')
            else:
                self.render('wx/guanzhu.html')

    def post(self, product_id, num):
        mobile = self.get_body_argument('mobile', '')
        p_mobile = self.get_body_argument('p_mobile', '')
        access_token = handler.get_access_token()
        openid = self.application.memcachedb.get(str(product_id)+str(num))
        logging.info('-----openid=%s' % openid)
        userinfo = handler.get_user_info(access_token, openid)
        logging.info('-----nickname: %s' % userinfo['nickname'])
        nickname = userinfo['nickname'] if 'nickname' in userinfo else ''

        Yz = YzScore()
        Yz.get_token()
        yz_user_info = Yz.funs_info(openid)
        logging.info('---yz_user_info:---%s' % yz_user_info)
        try:
            fans_id = simplejson.loads(yz_user_info)['response']['user']['user_id']
        except:
            return self.write(yz_user_info)
        if User.select().where(User.openid == openid).count() <= 0:
            user = self.create_user(openid, nickname, mobile, yz_user_info)
            session, sessionid = self.session
            session['user'] = (user, sessionid)
            session.save()
            if p_mobile:
                p_users = User.select().where(User.mobile == p_mobile)
                if p_users.count() > 0:
                    p_user = p_users[0]
                    user.pid = p_user.id
                    p_user.sub_user_count += 1    # 推荐人数加1
                    user.save()
                else:
                    p_openid = Yz.get_user_openid(p_mobile)
                    p_users = User.select().where(User.openid == p_openid)
                    if p_users.count() > 0:
                        p_user = p_users[0]
                        user.pid = p_user.id
                        user.sub_user_count += 1    # 推荐人数加1
                        user.save()
                        if not p_user.mobile:
                            p_user.mobile = p_mobile
                            p_user.save()
                        p_ruleIDs = Rule.select().where(Rule.number < user.sub_user_count, Rule.type == 1)  # 符合奖励积分条件的所有
                        if p_ruleIDs.count() > 0:
                            # 满足最低增加积分要求
                            recorders = ScoreRecord.select().where(ScoreRecord.user == p_user.id)
                            ruleRecoder = []
                            for recorde in recorders:
                                ruleRecoder.append(recorde.rule)    # 此用户所有已经完成的推荐奖励 id
                            for __id in p_ruleIDs:
                                if __id.id not in ruleRecoder:
                                    # 如此奖励未发放
                                    score = Rule.get(id=__id.id)
                                    Yz.add_score(score, mobile=p_user.mobile)   # 增加积分
                                    # 添加记录
                                    record = ScoreRecord()
                                    record.user = p_user.id
                                    record.score = score
                                    record.info = u'推荐用户数目达一定数目赠送积分'
                                    record.created = time.time()
                                    record.rule = __id  .id
                                    record.save()

            if 'A' not in user.grade:
                logging.info('fans_id=%s' % fans_id)
                self.add_score(user, product_id, num, Yz, fans_id)

        self.redirect('https://h5.youzan.com/v2/usercenter/8sbIpUkeGQ?reft=1518450450886&spm=f69815501')


@Route(r'/mobile/myinfo/(\d+)', name='mobile_myinfo')  # 完善个人信息
class MyinfoHandler(WXBaseHandler):
    def get(self, user_id):
        code = self.get_argument('code', '')
        code = self.get_argument('code', '')
        user = User.get(id=user_id)
        items = Area.select().where(Area.pid == 0)
        logging.info('----------%s' % items.count())
        self.render('wx/myinfo.html', areas=items, user=user)


@Route(r'/mobile/manager/(\d+)', name='mobile_manager')  # 完善个人信息
class ManagerHandler(WXBaseHandler):
    def get(self, user_id):
        code = self.get_argument('code', '')
        code = self.get_argument('code', '')
        user = User.get(id=user_id)
        items = Area.select().where(Area.pid == 0)
        logging.info('----------%s' % items.count())
        logging.info('--------user id--%s' % user.id)
        self.render('wx/manager.html', areas=items, user=user)

    def post(self, user_id):
        result = {'flag': 0, 'msg': ''}
        mobile = self.get_body_argument('mobile', '')
        birthday = self.get_body_argument('birthday', '')
        real_name = self.get_body_argument('real_name', '')
        store_name = self.get_body_argument('store_name', '')
        district = self.get_body_argument('district', '')
        if not (mobile and birthday and real_name and store_name and district):
            result['msg'] = u'请补全所有参数'
            return self.write(simplejson.dumps(result))
        else:
            try:
                time.mktime(time.strptime(birthday, '%Y-%m-%d'))
            except:
                result['msg'] = u'请按照规则填写生日，如：1993-5-15'
                return self.write(simplejson.dumps(result))
        user = User.get(id=user_id)
        user.mobile = mobile
        user.real_name = real_name
        user.store_name = store_name
        user.birthday = birthday
        user.area_code = district
        user.save()
        result['flag'] = 1
        result['msg'] = u'保存成功'
        return self.write(simplejson.dumps(result))

# ---------------------------------------------请求---------------------------------------------------
@Route(r'/ajax/create_qrcode', name='ajax_create_qrcode')  # 生成二维码
class AjaxCreateQrcodeHandler(AdminBaseHandler):
    def create_qrcode(self, filename, content='default content'):
        qr = qrcode.make(content)
        filename += '.jpeg'
        qr.save(filename, format='jpeg')

    def create_dir(self, p_name, num):
        dir_name = p_name + '_' + str(num) + '_' + time.strftime('%Y-%m-%d', time.localtime())
        path = os.path.join(setting.upload_path, dir_name)
        if not os.path.exists(path):
            os.mkdir(path)
        return path

    def post(self):
        result = {'flag': 0, 'msg': ''}
        pid = self.get_body_argument('pid', '')
        num = self.get_body_argument('num', '')
        if pid and num:
            pid = int(pid)
            num = int(num)
        else:
            result['msg'] = u'打印数量必须大于0'
            return self.write(simplejson.dumps(result))
        product = Product.get(id=pid)
        path = self.create_dir(product.name, num)
        for i in range(num):
            p_num = i+1+product.number
            url = 'http://www.baidu.com/qrcode?pid=%s&p_num=%s' % (pid, p_num)
            self.create_qrcode(os.path.join(path, str(p_num)), url)


@Route(r'/ajax/create_qrcode_url', name='ajax_create_qrcode_url')  # 生成二维码链接
class AjaxCreateQrcodeUrlHandler(AdminBaseHandler):
    def post(self):
        result = {'flag': 0, 'msg': ''}
        pid = self.get_body_argument('pid', '')
        num = self.get_body_argument('num', '')
        if pid and num:
            pid = int(pid)
            num = int(num)
        else:
            result['msg'] = u'打印数量必须大于0'
            return self.write(simplejson.dumps(result))
        product = Product.get(id=pid)
        txt = os.path.join(setting.upload_path, 'qr_code_url.txt')
        fp = open(txt, 'w')
        for i in range(num):
            p_num = i+1+product.number
            url = 'http://wxstore.solrxchina.com/mobile/v1/qrcode/%s/%s\r\n' % (pid, p_num)
            fp.write(url)
        fp.close()
        product.number += num
        product.save()
        result['flag'] = 1
        self.write(simplejson.dumps(result))


@Route(r'/ajax/GetSubAreas', name='ajax_GetSubAreas')  # 获取下级区域
class AjaxGetSubAreas(BaseHandler):
    def get(self):
        result = {'flag': 0, 'data': [], 'msg': ''}
        try:
            parent_code = self.get_argument("pcode", '')
            keyword = '' + parent_code + '0%'
            ft = (Area.code % keyword)
            items = Area.select().where(ft)
            result["flag"] = 1
            result["data"] = []
            for item in items:
                result["data"].append({
                    'id': item.id,
                    'code': item.code,
                    'name': item.name
                })
            else:
                result['msg'] = u'无对应子区域'
        except Exception, ex:
            result["flag"] = 0
            result["msg"] = ex.message
        self.write(simplejson.dumps(result))


@Route(r'/ajax/user_to_manager', name='ajax_user_to_manager')  # 获取下级区域
class AjaxUserToManager(BaseHandler):
    def post(self):
        result = {'flag': 0, 'data': [], 'msg': ''}
        id = self.get_body_argument("id", '')
        state_type = self.get_body_argument("state_type", '')
        print id, state_type
        try:
            id = int(id)
            state_type = int(state_type)
            user = User.get(id=id)
            if state_type == 2:
                if 'A' not in user.grade:
                    user.grade += 'A'
            else:
                user.grade = user.grade.strip('A')
            user.status = state_type
            user.save()
            result['flag'] = 1
        except Exception, ex:
            result["msg"] = ex.message
        return self.write(simplejson.dumps(result))










