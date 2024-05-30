import os
import re
import threading
import time
from asyncio import CancelledError
from concurrent.futures import Future, ThreadPoolExecutor

from connect.context import *
from connect.reply import *
from channel.channel import Channel
from tool.dequeue import Dequeue
from tool.log import logger
from config import conf


class ChatChannel(Channel):
    name = None  
    user_id = None  
    futures = {}  
    sessions = {}  
    lock = threading.Lock()  
    handler_pool = ThreadPoolExecutor(max_workers=8) 

    def __init__(self):
        _thread = threading.Thread(target=self.consume)
        _thread.setDaemon(True)
        _thread.start()

    
    def _compose_context(self, ctype: ContextType, content, **kwargs):
        context = Context(ctype, content)
        context.kwargs = kwargs
        if "origin_ctype" not in context:
            context["origin_ctype"] = ctype
        first_in = "receiver" not in context
        if first_in: 
            config = conf()
            cmsg = context["msg"]
            user_data = conf().get_user_data(cmsg.from_user_id)
            context["session_id"] = cmsg.other_user_id
            context["receiver"] = cmsg.other_user_id
        if ctype == ContextType.TEXT:
            if first_in and "」\n- - - - - - -" in content:  
                logger.debug("[WX]reference query skipped")
                return None
            match_prefix = check_prefix(content, conf().get("single_chat_prefix", [""]))
            if match_prefix is not None:  
                content = content.replace(match_prefix, "", 1).strip()
            else:
                return None
            content = content.strip()
            context.content = content.strip()
        return context

    def _handle(self, context: Context):
        if context is None or not context.content:
            return
        logger.debug("[WX] ready to handle context: {}".format(context))
        reply = self._generate_reply(context)
        logger.debug("[WX] ready to decorate reply: {}".format(reply))
        reply = self._decorate_reply(context, reply)
        self._send_reply(context, reply)

    def _generate_reply(self, context: Context, reply: Reply = Reply()) -> Reply:
        if context.type == ContextType.TEXT: 
            reply = super().build_reply_content(context.content, context)
        return reply

    def _decorate_reply(self, context: Context, reply: Reply) -> Reply:
        
        if reply.type == ReplyType.TEXT:
            reply_text = reply.content
            reply_text = conf().get("single_chat_reply_prefix", "") + reply_text + conf().get("single_chat_reply_suffix", "")
            reply.content = reply_text
        return reply

    def _send_reply(self, context: Context, reply: Reply):
        logger.debug("[WX] ready to send reply: {}, context: {}".format(reply, context))
        self._send(reply, context)

    def _send(self, reply: Reply, context: Context, retry_cnt=0):
        try:
            self.send(reply, context)
        except Exception as e:
            logger.error("[WX] sendMsg error: {}".format(str(e)))
            if isinstance(e, NotImplementedError):
                return
            logger.exception(e)
            if retry_cnt < 2:
                time.sleep(3 + 3 * retry_cnt)
                self._send(reply, context, retry_cnt + 1)

    def _success_callback(self, session_id, **kwargs):  
        logger.debug("Worker return success, session_id = {}".format(session_id))

    def _fail_callback(self, session_id, exception, **kwargs):  
        logger.exception("Worker return exception: {}".format(exception))

    def _thread_pool_callback(self, session_id, **kwargs):
        def func(worker: Future):
            try:
                worker_exception = worker.exception()
                if worker_exception:
                    self._fail_callback(session_id, exception=worker_exception, **kwargs)
                else:
                    self._success_callback(session_id, **kwargs)
            except CancelledError as e:
                logger.info("Worker cancelled, session_id = {}".format(session_id))
            except Exception as e:
                logger.exception("Worker raise exception: {}".format(e))
            with self.lock:
                self.sessions[session_id][1].release()

        return func

    def produce(self, context: Context):
        session_id = context["session_id"]
        with self.lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = [
                    Dequeue(),
                    threading.BoundedSemaphore(4),
                ]
            if context.type == ContextType.TEXT and context.content.startswith("#"):
                self.sessions[session_id][0].putleft(context) 
            else:
                self.sessions[session_id][0].put(context)


    def consume(self):
        while True:
            with self.lock:
                session_ids = list(self.sessions.keys())
                for session_id in session_ids:
                    context_queue, semaphore = self.sessions[session_id]
                    if semaphore.acquire(blocking=False):  
                        if not context_queue.empty():
                            context = context_queue.get()
                            logger.debug("[WX] consume context: {}".format(context))
                            future: Future = self.handler_pool.submit(self._handle, context)
                            future.add_done_callback(self._thread_pool_callback(session_id, context=context))
                            if session_id not in self.futures:
                                self.futures[session_id] = []
                            self.futures[session_id].append(future)
                        elif semaphore._initial_value == semaphore._value + 1:  
                            self.futures[session_id] = [t for t in self.futures[session_id] if not t.done()]
                            assert len(self.futures[session_id]) == 0, "thread pool error"
                            del self.sessions[session_id]
                        else:
                            semaphore.release()
            time.sleep(0.1)

    
    def cancel_session(self, session_id):
        with self.lock:
            if session_id in self.sessions:
                for future in self.futures[session_id]:
                    future.cancel()
                cnt = self.sessions[session_id][0].qsize()
                if cnt > 0:
                    logger.info("Cancel {} messages in session {}".format(cnt, session_id))
                self.sessions[session_id][0] = Dequeue()

    def cancel_all_session(self):
        with self.lock:
            for session_id in self.sessions:
                for future in self.futures[session_id]:
                    future.cancel()
                cnt = self.sessions[session_id][0].qsize()
                if cnt > 0:
                    logger.info("Cancel {} messages in session {}".format(cnt, session_id))
                self.sessions[session_id][0] = Dequeue()


def check_prefix(content, prefix_list):
    if not prefix_list:
        return None
    for prefix in prefix_list:
        if content.startswith(prefix):
            return prefix
    return None


def check_contain(content, keyword_list):
    if not keyword_list:
        return None
    for ky in keyword_list:
        if content.find(ky) != -1:
            return True
    return None
