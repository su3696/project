import threading
import time

from wechatpy.client import WeChatClient
from wechatpy.exceptions import APILimitedException

from tool.log import logger


class WechatMPClient(WeChatClient):
    def __init__(self, appid, secret, access_token=None, session=None, timeout=None, auto_retry=True):
        super(WechatMPClient, self).__init__(appid, secret, access_token, session, timeout, auto_retry)
        self.fetch_access_token_lock = threading.Lock()
        self.clear_quota_lock = threading.Lock()
        self.last_clear_quota_time = -1

    def clear_quota(self):
        return self.post("clear_quota", data={"appid": self.appid})

    def clear_quota_v2(self):
        return self.post("clear_quota/v2", params={"appid": self.appid, "appsecret": self.secret})

    def fetch_access_token(self):  
        with self.fetch_access_token_lock:
            access_token = self.session.get(self.access_token_key)
            if access_token:
                if not self.expires_at:
                    return access_token
                timestamp = time.time()
                if self.expires_at - timestamp > 60:
                    return access_token
            return super().fetch_access_token()

    def _request(self, method, url_or_endpoint, **kwargs):  
        try:
            return super()._request(method, url_or_endpoint, **kwargs)
        except APILimitedException as e:
            logger.error("[wechatmp] API quata has been used up. {}".format(e))
            if self.last_clear_quota_time == -1 or time.time() - self.last_clear_quota_time > 60:
                with self.clear_quota_lock:
                    if self.last_clear_quota_time == -1 or time.time() - self.last_clear_quota_time > 60:
                        self.last_clear_quota_time = time.time()
                        response = self.clear_quota_v2()
                        logger.debug("[wechatmp] API quata has been cleard, {}".format(response))
                return super()._request(method, url_or_endpoint, **kwargs)
            else:
                logger.error("[wechatmp] last clear quota time is {}, less than 60s, skip clear quota")
                raise e
