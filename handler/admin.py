#!/usr/bin/env python
# coding=utf8

from handler import BaseHandler, AdminBaseHandler, WXBaseHandler
from lib.route import Route
from lib.model import *
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
        # if category:
        #     ft &= (Product.category == category)
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
            user.save()
            self.set_token(user.token, user.id)
            if 'A' not in user.grade:
                try:
                    fans_id = simplejson.loads(user.yz_user_info)['response']['user']['user_id']
                    self.add_score(user, product_id, num, Yz, fans_id)
                except:
                    pass
            self.redirect('https://h5.youzan.com/v2/usercenter/8sbIpUkeGQ?reft=1518450450886&spm=f69815501')
        else:
            self.application.memcachedb.set(str(product_id)+str(num), openid, setting.user_expire)
            self.render('wx/qrcode.html')

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
                    user.save()
                    if not p_user.mobile:
                        p_user.mobile = p_mobile
                        p_user.save()
                # else:
                #     # 根据手机号获取用户信息
                #     p_openid = Yz.get_user_openid(p_mobile)
                #     if p_openid:
                #         p_users = User.select().where(User.mobile == p_mobile)
                #         if p_users.count() > 0:
                #             p_user = p_users[0]
                #             user.pid = p_user.id
                #             user.save()
                #             p_user.mobile = p_mobile
                #             p_user.save()2123啊
            if 'A' not in user.grade:
                logging.info('fans_id=%s' % fans_id)
                self.add_score(user, product_id, num, Yz, fans_id)

        self.redirect('https://h5.youzan.com/v2/usercenter/8sbIpUkeGQ?reft=1518450450886&spm=f69815501')


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






