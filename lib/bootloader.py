#!/usr/bin/env python
# coding=utf8
# 启动

import memcache
from jinja2 import Environment, FileSystemLoader
from jinja2 import MemcachedBytecodeCache
import setting
from util import setting_from_object
from database import Db

settings = setting_from_object(setting)

memcachedb = memcache.Client([settings['memcache_host']])

jinja_environment = Environment(
    loader=FileSystemLoader(settings['template_path']),
    bytecode_cache=MemcachedBytecodeCache(memcachedb) if not settings['debug'] else None,  # 如果不是debug将模板编译的结果存到memcache
    auto_reload=True,  # 如果auto_reload 为False但是bytecode_cache使用了的话，当html代码修改时因为模板从memcach中取，所以页面将不能及时更新；
    autoescape=settings['autoescape'])

db = Db({'db': settings['db_name'], 'host': settings['db_host'], 'port': settings['db_port'],
         'user': settings['db_user'], 'passwd': settings['db_passwd'], 'charset': 'utf8',
         'max_connections':settings['max_connections'], 'stale_timeout':settings['stale_timeout']})


