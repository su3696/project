# encoding:utf-8

import json
import logging
import os
import pickle

from tool.log import logger


available_setting = {

    "model": "wenxin",    
    "single_chat_prefix": ["bot", "@bot"],  # 前缀触发机器人
    "single_chat_reply_prefix": "[bot] ",  # 自动回复的前缀
    "single_chat_reply_suffix": "",  # 自动回复的后缀
    "baidu_wenxin_model": "eb-instant", # 默认使用ERNIE-Bot-turbo模型
    "baidu_wenxin_api_key": "", # Baidu api key
    "baidu_wenxin_secret_key": "", # Baidu secret key
    "wechatmp_token": "",  # 微信公众平台的Token
    "wechatmp_port": 8080,  # 微信公众平台的端口,需要端口转发到80或443
    "wechatmp_app_id": "",  # 微信公众平台的appID
    "wechatmp_app_secret": "",  # 微信公众平台的appsecret
    "wechatmp_aes_key": "",  # 微信公众平台的EncodingAESKey，加密模式需要
    "channel_type": "wechatmp",  # 通道类型
    "subscribe_msg": "",  # 订阅消息,
    "debug": False,  # 是否开启debug模式，开启后会打印更多日志
}


class Config(dict):
    def __init__(self, d=None):
        super().__init__()
        if d is None:
            d = {}
        for k, v in d.items():
            self[k] = v
        self.user_datas = {}

    def __getitem__(self, key):
        if key not in available_setting:
            raise Exception("key {} not in available_setting".format(key))
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if key not in available_setting:
            raise Exception("key {} not in available_setting".format(key))
        return super().__setitem__(key, value)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError as e:
            return default
        except Exception as e:
            raise e

    def get_user_data(self, user) -> dict:
        if self.user_datas.get(user) is None:
            self.user_datas[user] = {}
        return self.user_datas[user]

    def load_user_datas(self):
        try:
            with open(os.path.join(get_appdata_dir(), "user_datas.pkl"), "rb") as f:
                self.user_datas = pickle.load(f)
                logger.info("[Config] User datas loaded.")
        except FileNotFoundError as e:
            logger.info("[Config] User datas file not found, ignore.")
        except Exception as e:
            logger.info("[Config] User datas error: {}".format(e))
            self.user_datas = {}

    def save_user_datas(self):
        try:
            with open(os.path.join(get_appdata_dir(), "user_datas.pkl"), "wb") as f:
                pickle.dump(self.user_datas, f)
                logger.info("[Config] User datas saved.")
        except Exception as e:
            logger.info("[Config] User datas error: {}".format(e))


config = Config()


def load_config():
    global config
    config_path = "./config.json"
    if not os.path.exists(config_path):
        logger.info("配置文件不存在")
        config_path = "./config-template.json"

    config_str = read_file(config_path)
    logger.debug("[INIT] config str: {}".format(config_str))
    config = Config(json.loads(config_str))
    for name, value in os.environ.items():
        name = name.lower()
        if name in available_setting:
            logger.info("[INIT] override config by environ args: {}={}".format(name, value))
            try:
                config[name] = eval(value)
            except:
                if value == "false":
                    config[name] = False
                elif value == "true":
                    config[name] = True
                else:
                    config[name] = value
    if config.get("debug", False):
        logger.setLevel(logging.DEBUG)
        logger.debug("[INIT] set log level to DEBUG")

    logger.info("[INIT] load config: {}".format(config))

    config.load_user_datas()


def get_root():
    return os.path.dirname(os.path.abspath(__file__))


def read_file(path):
    with open(path, mode="r", encoding="utf-8") as f:
        return f.read()


def conf():
    return config


def get_appdata_dir():
    data_path = os.path.join(get_root(), conf().get("appdata_dir", ""))
    if not os.path.exists(data_path):
        logger.info("[INIT] data path not exists, create it: {}".format(data_path))
        os.makedirs(data_path)
    return data_path



global_config = {
    "admin_users": []
}
