

from connect.context import Context
from connect.reply import Reply


def create_bot(bot_type):

    if bot_type == "baidu":
        from bot.baidu_wenxin import BaiduWenxinBot
        return BaiduWenxinBot()
    raise RuntimeError


class Bot(object):
    def reply(self, query, context: Context = None) -> Reply:
        raise NotImplementedError
