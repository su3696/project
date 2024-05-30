# encoding:utf-8

from enum import Enum


class ReplyType(Enum):
    TEXT = 1 
    INFO = 9
    ERROR = 10

    def __str__(self):
        return self.name


class Reply:
    def __init__(self, type: ReplyType = None, content=None):
        self.type = type
        self.content = content

    def __str__(self):
        return "Reply(type={}, content={})".format(self.type, self.content)
