"""
Message sending channel abstract class
"""

from connect.connect import Connect
from connect.context import Context
from connect.reply import *


def create_channel(channel_type):
    """
    create a channel instance
    :param channel_type: channel type code
    :return: channel instance
    """
    if channel_type == "wechatmp":
        from channel.wechatmp.wechatmp_channel import WechatMPChannel
        return WechatMPChannel(wechatmp_reply=True)
        
    raise RuntimeError


class Channel(object):

    def startup(self):
        """
        init channel
        """
        raise NotImplementedError

    def handle_text(self, msg):
        """
        process received msg
        :param msg: message object
        """
        raise NotImplementedError

    # 统一的发送函数，每个Channel自行实现，根据reply的type字段发送不同类型的消息
    def send(self, reply: Reply, context: Context):
        """
        send message to user
        :param msg: message content
        :param receiver: receiver channel account
        :return:
        """
        raise NotImplementedError

    def build_reply_content(self, query, context: Context = None) -> Reply:
        return Connect().fetch_reply_content(query, context)




