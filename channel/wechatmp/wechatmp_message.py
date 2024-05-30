# -*- coding: utf-8 -*-#

from connect.context import ContextType
from channel.chat_message import ChatMessage



class WeChatMPMessage(ChatMessage):
    def __init__(self, msg, client=None):
        super().__init__(msg)
        self.msg_id = msg.id
        self.create_time = msg.time
        self.is_group = False

        if msg.type == "text":
            self.ctype = ContextType.TEXT
            self.content = msg.content
        else:
            raise NotImplementedError("Unsupported message type: Type:{} ".format(msg.type))

        self.from_user_id = msg.source
        self.to_user_id = msg.target
        self.other_user_id = msg.source
