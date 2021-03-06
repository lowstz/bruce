# coding: utf-8

import time
import tornado.web

import config
from helpers import getAvatar, getDay, getMonth, formatDate, formatDate2, showPost, replyContent
from extensions import md
from .base import BaseHandler
from database import db

from models import Post, Reply

import sqlalchemy as sa

config = config.rec()

def getRecentReplys():
    return db.query(Reply).order_by(sa.desc(Reply.created_date)).limit(6)

class HomeHandler(BaseHandler):
    def get(self, page = 1):
        page = int(page)
        count = db.query(Post).count();
        page_count = (count + config.paged - 1) // config.paged
        posts = db.query(Post).order_by(sa.desc(Post.created_date)).offset((page - 1) *
                config.paged).limit(config.paged)
        self.render("home.html", posts=posts, getDay=getDay, getMonth=getMonth, \
                getAvatar=getAvatar, replyContent=replyContent, formatDate=formatDate, formatDate2=formatDate2, showPost=showPost, page=page,
                page_count=page_count)

class ArchiveHandler(BaseHandler):
    def get(self, page = 1):
        page = int(page)
        count = db.query(Post).count()
        page_count = (count + config.archive_paged - 1) // config.archive_paged
        posts = db.query(Post).order_by(sa.desc(Post.created_date)).offset((page - 1) *
                config.archive_paged).limit(config.archive_paged)
        self.render("archive.html", posts=posts, formatDate2=formatDate2, page=page,
                page_count=page_count)

class PostHandler(BaseHandler):
    def get(self, pid):
        replyer = self.replyerGet()
        if replyer is None:
            replyer = {}
            replyer['name'] = ''
            replyer['email'] = ''
            replyer['website'] = ''
        if self.currentUserGet():
            replyer = {}
            replyer['name'] = config.admin_username
            replyer['email'] = config.admin_email
            replyer['website'] = config.url
        post = db.query(Post).get(pid)
        if not post: raise tornado.web.HTTPError(404)
        replys = db.query(Reply).filter(Reply.pid == pid).all()
        self.render("post.html", post=post, replys=replys, \
                formatDate=formatDate, formatDate2=formatDate2,
                getAvatar=getAvatar, replyer=replyer)

class PostAddHandler(BaseHandler):
    def get(self):
        self.checkAdmin()
        self.render("postadd.html", title='', origin_content='')

    def post(self):
        self.checkAdmin()
        title = self.get_argument("post[title]", '')
        origin_content = self.get_argument("post[content]", '')
        content = md(origin_content)
        if title != '' and origin_content != '':
            db.add(Post(title=title, content=content,
                origin_content=origin_content))
            db.commit()
            self.redirect("/")
        else:
            self.render("postadd.html", error=u"标题或内容不能为空。",
                    title=title, origin_content=origin_content)

class PostEditHandler(BaseHandler):
    def get(self, pid):
        self.checkAdmin()
        post = db.query(Post).get(pid)
        if post is None:
            tornado.web.HTTPError(404)
        self.render("postedit.html", post=post)

    def post(self, pid):
        self.checkAdmin()
        title = self.get_argument("post[title]", default='')
        origin_content = self.get_argument("post[content]", default='')
        content = md(origin_content)
        post = db.query(Post).get(pid)
        post.title = title
        post.origin_content = origin_content
        post.content = content
        if title != '' and origin_content != '':
            db.commit()
            self.redirect("/post/%d" % (int(pid)))
        else:
            self.render("postedit.html", error=u"标题或内容不能为空。",
                    post=post)

class FeedHandler(BaseHandler):
    def get(self):
        updated_time = int(time.time())
        posts =\
        db.query(Post).order_by(sa.desc(Post.created_date)).limit(12)
        self.set_header("Content-Type", "application/atom+xml")
        self.render("feed.xml", posts=posts, formatDate2=formatDate2,
                updated_time=updated_time, config=config)

class RecentReplysModule(tornado.web.UIModule):
    def render(self, recent_replys, getAvatar=getAvatar,
            replyContent=replyContent):
        return self.render_string("modules/recentreplys.html",
                recent_replys=recent_replys, getAvatar=getAvatar,
                replyContent=replyContent)
