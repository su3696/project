# encoding:utf-8

import requests, json
from bot.bot import Bot
from connect.reply import Reply, ReplyType
from bot.session_manager import SessionManager
from connect.context import ContextType
from tool.log import logger
from config import conf
from bot.baidu_wenxin_session import BaiduWenxinSession

BAIDU_API_KEY = conf().get("baidu_wenxin_api_key")
BAIDU_SECRET_KEY = conf().get("baidu_wenxin_secret_key")

class BaiduWenxinBot(Bot):

    def __init__(self):
        super().__init__()
        self.sessions = SessionManager(BaiduWenxinSession, model=conf().get("baidu_wenxin_model") or "eb-instant")

    def reply(self, query, context=None):
        # acquire reply content
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[BAIDU] query={}".format(query))
                session_id = context["session_id"]
                reply = None
                session = self.sessions.session_query(query, session_id)
                result = self.reply_text(session)
                total_tokens, completion_tokens, reply_content = (
                    result["total_tokens"],
                    result["completion_tokens"],
                    result["content"],
                )
                logger.debug(
                    "[BAIDU] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(session.messages, session_id, reply_content, completion_tokens)
                )

                if total_tokens == 0:
                    reply = Reply(ReplyType.ERROR, reply_content)
                else:
                    self.sessions.session_reply(reply_content, session_id, total_tokens)
                    reply = Reply(ReplyType.TEXT, reply_content)
            return reply
            

    def reply_text(self, session: BaiduWenxinSession, retry_count=0):
        try:
            logger.info("[BAIDU] model={}".format(session.model))
            access_token = self.get_access_token()
            if access_token == 'None':
                logger.warn("[BAIDU] access token 获取失败")
                return {
                    "total_tokens": 0,
                    "completion_tokens": 0,
                    "content": 0,
                    }
            url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/" + session.model + "?access_token=" + access_token
            headers = {
                'Content-Type': 'application/json'
            }
            payload = {'messages': session.messages}
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            response_text = json.loads(response.text)
            res_content = response_text["result"]
            total_tokens = response_text["usage"]["total_tokens"]
            completion_tokens = response_text["usage"]["completion_tokens"]
            logger.info("[BAIDU] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except Exception as e:
            need_retry = retry_count < 2
            logger.warn("[BAIDU] Exception: {}".format(e))
            need_retry = False
            self.sessions.clear_session(session.session_id)
            result = {"completion_tokens": 0, "content": "出错了: {}".format(e)}
            return result

    def get_access_token(self):
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": BAIDU_API_KEY, "client_secret": BAIDU_SECRET_KEY}
        return str(requests.post(url, params=params).json().get("access_token"))
