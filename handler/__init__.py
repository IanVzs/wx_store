#!/usr/bin/env python
# coding=utf8


from tornado.web import RequestHandler
from lib.model import User
from lib.session import Session
from lib.mixin import FlashMessagesMixin
import logging
import functools
import simplejson
import random as rand
import hashlib
import string
import urllib
import urllib2
import time
import traceback
import setting
import uuid

appid = 'wx831c87012e567c2e'
secret = '0269e5bd0cb9db0543d37ef90a8b723d'


class MobilePageNotFoundHandler(RequestHandler):
    def get(self):
        self.set_status(404)
        return self.write('not found')


class MobileBaseHandler(RequestHandler):
    def check_xsrf_cookie(self):
        pass

    def options(self):
        pass

    def get_user(self):
        user = None
        token = self.request.headers.get('token', None)
        if token:
            data = self.application.memcachedb.get(token)
            if data is not None:
                try:
                    user = User.get(id=data)
                except:
                    user = None
        return user

    def get_store_area_code(self):
        user = self.get_user()
        if user is None:
            area_code = self.get_default_area_code()  # 默认使用西安市的code
        else:
            area_code = user.store.area_code
        return area_code

    def get_default_area_code(self):
        return '00270001'  # 默认使用西安市的code

    def render_string(self, template_name, **context):
        context.update({
            'xsrf': self.xsrf_form_html,
            'request': self.request}
        )

        return self._jinja_render(path=self.get_template_path(), filename=template_name,
                                  auto_reload=self.settings['debug'], **context)

    def _jinja_render(self, path, filename, **context):
        template = self.application.jinja_env.get_template(filename, parent=path)
        return template.render(**context)


class BaseHandler(RequestHandler, FlashMessagesMixin):
    def set_default_headers(self):
        self.clear_header('Server')

    def render_string(self, template_name, **context):
        context.update({
            'xsrf': self.xsrf_form_html,
            'module': self.ui.modules,
            'request': self.request,
            'user': self.current_user,
            'admin': self.get_admin_user(),
            'handler': self,
            'store': self.get_store_user()}
        )

        return self._jinja_render(path=self.get_template_path(), filename=template_name,
                                  auto_reload=self.settings['debug'], **context)

    def _jinja_render(self, path, filename, **context):
        template = self.application.jinja_env.get_template(filename, parent=path)
        return template.render(**context)

    @property
    def is_xhr(self):
        return self.request.headers.get('X-Requested-With', '').lower() == 'xmlhttprequest'

    @property
    def memcachedb(self):
        return self.application.memcachedb

    @property
    def session(self):
        if hasattr(self, '_session'):
            if not getattr(self, 'sessionid'):
                self.sessionid = None
            return self._session, self.sessionid
        else:
            self.sessionid = self.get_secure_cookie('sid')
            self._session = Session(self.application.session_store, self.sessionid, expires_days=1)
            if not self.sessionid:
                self.set_secure_cookie('sid', self._session.id, expires_days=1)
            return self._session, self.sessionid

    def get_current_user(self):
        try:
            return User.get(id=self.session[0]['user'][0].id) if 'user' in self.session[0] else None
        except Exception:
            return None

    def get_admin_user(self):
        sid = self.get_secure_cookie('sid')
        try:
            user, sessionid = self.application.session_store.get_session(sid, 'data')['admin']
            if sid == sessionid:
                return user
            else:
                return None
        except Exception, e:
            return None

    def get_store_user(self):
        return self.session[0]['store'] if 'store' in self.session[0] else None

    def get_user_role(self):
        user = self.get_admin_user()
        if not user:
            return []
        else:
            return list(user.roles)

    @property
    def next_url(self):
        return self.get_argument("next", "/login")

    def write_error(self, status_code, **kwargs):
        import traceback

        msg = '<h2>未显示错误！</h2>'
        if "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br>" % line for line in traceback.format_exception(*exc_info)])
            request_info = ''.join(
                ["%s: %s <br>" % (k, self.request.__dict__[k]) for k in self.request.__dict__.keys()])
            error = exc_info[1]
            msg = u"""Error:<br>
                %s<br>
                Traceback:<br>
                %s<br>
                Request Info<br>
                %s""" % (error, trace_info, request_info)
        self.set_status(status_code)
        msg = msg if self.settings['debug'] else None
        return self.render('error.html', msg=msg)


class AdminPageNotFoundHandler(BaseHandler):
    def get(self):
        self.set_status(404)
        return self.render('404.html')


class AdminBaseHandler(BaseHandler):
    def prepare(self):
        if not self.get_admin_user():
            self.redirect("/admin/login")
        super(AdminBaseHandler, self).prepare()

    def vrole(self, rolelist):
        userrole = self.get_user_role()
        for n in userrole:
            if rolelist.count(n) > 0:
                return True
        return False


class WXBaseHandler(BaseHandler):
    def get_wx_user(self):
        user = None
        token = self.request.headers.get('token', None)
        if token:
            data = self.application.memcachedb.get(token)
            if data is not None:
                try:
                    user = User.get(id=data)
                except:
                    user = None
        return user

    def set_token(self, token, user_id):
        self.application.memcachedb.set(token, str(user_id), setting.user_expire)

    def update_token(self, token):
        if token:
            data = self.application.memcachedb.get(token)
            if data is None:
                token = setting.user_token_prefix + str(uuid.uuid4())
        else:
            token = setting.user_token_prefix + str(uuid.uuid4())

        return token

    def get_access_token(self):
        self.weixin_app_id = appid
        self.weixin_secret = secret
        self.url_access_token = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" % (
            self.weixin_app_id, self.weixin_secret)
        return simplejson.loads(urllib2.urlopen(self.url_access_token).read())["access_token"]

    def get_jsapi_ticket(self):
        self.url_access_token = "https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi" % (
            self.get_access_token())
        return simplejson.loads(urllib2.urlopen(self.url_access_token).read())["ticket"]

    def create_nonce_str(self):
        return ''.join(rand.choice(string.ascii_letters + string.digits) for _ in range(15))

    def create_timestamp(self):
        return int(time.time())

    def sign(self, ret={}):
        string1 = '&'.join(['%s=%s' % (key.lower(), ret[key]) for key in sorted(ret)])
        ret['signature'] = hashlib.sha1(string1).hexdigest()
        return ret

    def get_js_sdk_sign(self, url):
        ret = {
            'nonceStr': self.create_nonce_str(),
            'jsapi_ticket': self.get_jsapi_ticket(),
            'timeStamp': self.create_timestamp(),
            'url': url
        }
        ret = self.sign(ret)
        ret['appid'] = appid
        return ret


def require_auth(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        token = self.request.headers.get('token')
        if token:
            data = self.application.memcachedb.get(token)
            if data is None:
                self.set_status(401)
                self.finish()
            else:
                return method(self, *args, **kwargs)
        else:
            self.set_status(401)
            self.finish()

    return wrapper


def wx_check_bind_car(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if len(args) > 0:
            activity_id = args[0]
        else:
            activity_id = ''
        user = self.get_current_user()
        if user:
            if user.user_car_libs.count() > 0:
                return method(self, *args, **kwargs)
        return self.redirect('/user_car_list?activity_id=%s' % activity_id)

    return wrapper


def wx_check_bind_mobile(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        user = self.get_current_user()
        if user:
            return method(self, *args, **kwargs)
        return self.redirect(
            "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxf23313db028ab4bc&redirect_uri=http%3A%2F%2Fwx.520czj.com%2Fwxapi%2Flogin&response_type=code&scope=snsapi_base&state=100douhao0000xiegang00mine#wechat_redirect")

    return wrapper


# 微信
def wx_notify(product_id, num):
    local_url = 'http%3A%2F%2Fwxstore.solrxchina.com%2Fwx%2Fv1%2Fqrcode%2F'+str(product_id)+'%2F'+str(num)
    wx_url = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxf23313db028ab4bc'+\
    '&redirect_uri='+urllib.quote(local_url)+'&response_type=code&scope=snsapi_base&'+\
    'state=100douhao0000xiegang00mine#wechat_redirect'
    logging.info(wx_url)
    urllib2.urlopen(wx_url)


def get_access_token_from_code(code):
    get_access_token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    grant_type = "authorization_code"
    try:
        _code = code
        url = get_access_token_url + "?appid=" + appid + "&secret=" + secret + "&code=" + _code +\
              "&grant_type=" + grant_type
        result = urllib2.urlopen(url).read()
        result = simplejson.loads(result)
        return (result['openid'], result['access_token']) if 'openid' in result and 'access_token' in result else ('', '')
    except Exception, e:
        logging.error(traceback.format_exc())
        return '', ''


def get_access_token():
    url_access_token = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&" \
                       "appid=%s&secret=%s" % (appid, secret)
    result = urllib2.urlopen(url_access_token).read()
    return simplejson.loads(result)["access_token"] if "access_token" in result else None


def get_user_info(access_token, openid):
    try:
        url = "https://api.weixin.qq.com/cgi-bin/user/info?access_token=%s&openid=%s&lang=zh_CN" % (
            access_token, openid)
        result = urllib2.urlopen(url).read()
        logging.info(result)
        return simplejson.loads(result)
    except Exception, e:
        logging.error(traceback.format_exc())
        return {}











