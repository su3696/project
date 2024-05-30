# -*- coding: utf-8 -*-
import asyncio
import threading
import time

from connect.context import *
from connect.reply import *
from channel.chat_channel import ChatChannel
from channel.wechatmp.common import *
from channel.wechatmp.wechatmp_client import WechatMPClient
from tool.log import logger
from tool.singleton import singleton
from tool.utils import split_string_by_utf8_length
from config import conf


@singleton
class WechatMPChannel(ChatChannel):
    def __init__(self, wechatmp_reply=True):
        super().__init__()
        self.wechatmp_reply = wechatmp_reply
        self.NOT_SUPPORT_REPLYTYPE = []
        appid = conf().get("wechatmp_app_id")
        secret = conf().get("wechatmp_app_secret")
        token = conf().get("wechatmp_token")
        aes_key = conf().get("wechatmp_aes_key")
        self.client = WechatMPClient(appid, secret)
        self.crypto = None
        if aes_key:
            self.crypto = WeChatCrypto(token, aes_key, appid)
        if self.wechatmp_reply:
            self.cache_dict = dict()
            self.running = set()
            self.request_cnt = dict()
            self.delete_media_loop = asyncio.new_event_loop()
            t = threading.Thread(target=self.start_loop, args=(self.delete_media_loop,))
            t.setDaemon(True)
            t.start()

    def startup(self):
        if self.wechatmp_reply:
            urls = ("/wx", "channel.wechatmp.wechatmp_reply.Query")
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("wechatmp_port", 8080)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def start_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def delete_media(self, media_id):
        logger.debug("[wechatmp] permanent media {} will be deleted in 10s".format(media_id))
        await asyncio.sleep(10)
        self.client.material.delete(media_id)
        logger.info("[wechatmp] permanent media {} has been deleted".format(media_id))

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if self.wechatmp_reply:
            if reply.type == ReplyType.TEXT or reply.type == ReplyType.INFO or reply.type == ReplyType.ERROR:
                reply_text = reply.content
                logger.info("[wechatmp] text cached, receiver {}\n{}".format(receiver, reply_text))
                self.cache_dict[receiver] = ("text", reply_text)
            
        else:
            if reply.type == ReplyType.TEXT or reply.type == ReplyType.INFO or reply.type == ReplyType.ERROR:
                reply_text = reply.content
                texts = split_string_by_utf8_length(reply_text, MAX_UTF8_LEN)
                if len(texts) > 1:
                    logger.info("[wechatmp] text too long, split into {} parts".format(len(texts)))
                for i, text in enumerate(texts):
                    self.client.message.send_text(receiver, text)
                    if i != len(texts) - 1:
                        time.sleep(0.5)  # 休眠0.5秒，防止发送过快乱序
                logger.info("[wechatmp] Do send text to {}: {}".format(receiver, reply_text))
        return

    def _success_callback(self, session_id, context, **kwargs):  
        logger.debug("[wechatmp] Success to generate reply, msgId={}".format(context["msg"].msg_id))
        if self.wechatmp_reply:
            self.running.remove(session_id)

    def _fail_callback(self, session_id, exception, context, **kwargs): 
        logger.exception("[wechatmp] Fail to generate reply to user, msgId={}, exception={}".format(context["msg"].msg_id, exception))
        if self.wechatmp_reply:
            assert session_id not in self.cache_dict
            self.running.remove(session_id)
