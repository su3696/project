from bot.bot import create_bot
from connect.context import Context
from connect.reply import Reply
from tool.log import logger
from tool.singleton import singleton
from config import conf


@singleton
class Connect(object):
    def __init__(self):
        self.btype = {
            "chat": "chat",
        }
        model_type = conf().get("model")
        if model_type in ["wenxin"]:
            self.btype["chat"] = "baidu"
        self.bots = {}

    def get_bot(self, typename):
        if self.bots.get(typename) is None:
            logger.info("create bot {} for {}".format(self.btype[typename], typename))
            if typename == "chat":
                self.bots[typename] = create_bot(self.btype[typename])
        return self.bots[typename]

    def get_bot_type(self, typename):
        return self.btype[typename]

    def fetch_reply_content(self, query, context: Context) -> Reply:
        return self.get_bot("chat").reply(query, context)


    def reset_bot(self):
        self.__init__()
