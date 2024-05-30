import time

from wechatpy import parse_message
from wechatpy.replies import create_reply
from channel.wechatmp.common import *
from channel.wechatmp.wechatmp_channel import WechatMPChannel
from channel.wechatmp.wechatmp_message import WeChatMPMessage
from tool.log import logger
from tool.utils import split_string_by_utf8_length



class Query:
    def GET(self):
        return verify_server(web.input())

    def POST(self):
        try:
            args = web.input()
            verify_server(args)
            request_time = time.time()
            channel = WechatMPChannel()
            message = web.data()
            encrypt_func = lambda x: x
            if args.get("encrypt_type") == "aes":
                logger.debug("[wechatmp] Receive encrypted post data:\n" + message.decode("utf-8"))
                if not channel.crypto:
                    raise Exception("Crypto not initialized, Please set wechatmp_aes_key in config.json")
                message = channel.crypto.decrypt_message(message, args.msg_signature, args.timestamp, args.nonce)
                encrypt_func = lambda x: channel.crypto.encrypt_message(x, args.nonce, args.timestamp)
            else:
                logger.debug("[wechatmp] Receive post data:\n" + message.decode("utf-8"))
            msg = parse_message(message)
            if msg.type in ["text"]:
                wechatmp_msg = WeChatMPMessage(msg, client=channel.client)
                from_user = wechatmp_msg.from_user_id
                content = wechatmp_msg.content
                message_id = wechatmp_msg.msg_id

                supported = True
                if "【收到不支持的消息类型，暂无法显示】" in content:
                    supported = False  # not supported, used to refresh

                if (
                    from_user not in channel.cache_dict
                    and from_user not in channel.running
                    or content.startswith("#")
                    and message_id not in channel.request_cnt  # insert the godcmd
                ):
                    context = channel._compose_context(wechatmp_msg.ctype, content, isgroup=False, msg=wechatmp_msg)
                    logger.debug("[wechatmp] context: {} {} {}".format(context, wechatmp_msg, supported))

                    if supported and context:
                        channel.running.add(from_user)
                        channel.produce(context)
                request_cnt = channel.request_cnt.get(message_id, 0) + 1
                channel.request_cnt[message_id] = request_cnt
                logger.info(
                    "[wechatmp] Request {} from {} {} {}:{}\n{}".format(
                        request_cnt, from_user, message_id, web.ctx.env.get("REMOTE_ADDR"), web.ctx.env.get("REMOTE_PORT"), content
                    )
                )

                task_running = True
                waiting_until = request_time + 4
                while time.time() < waiting_until:
                    if from_user in channel.running:
                        time.sleep(0.1)
                    else:
                        task_running = False
                        break

                reply_text = ""
                if task_running:
                    if request_cnt < 3:
                        time.sleep(2)
                        return "success"
                    else:
                        reply_text = "【正在思考中，回复任意文字尝试获取回复】"
                        replyPost = create_reply(reply_text, msg)
                        return encrypt_func(replyPost.render())
                channel.request_cnt.pop(message_id)
                if from_user not in channel.cache_dict and from_user not in channel.running:
                    return "success"
                try:
                    (reply_type, reply_content) = channel.cache_dict.pop(from_user)
                except KeyError:
                    return "success"

                if reply_type == "text":
                    if len(reply_content.encode("utf8")) <= MAX_UTF8_LEN:
                        reply_text = reply_content
                    else:
                        continue_text = "\n【未完待续，回复任意文字以继续】"
                        splits = split_string_by_utf8_length(
                            reply_content,
                            MAX_UTF8_LEN - len(continue_text.encode("utf-8")),
                            max_split=1,
                        )
                        reply_text = splits[0] + continue_text
                        channel.cache_dict[from_user] = ("text", splits[1])

                    logger.info(
                        "[wechatmp] Request {} do send to {} {}: {}\n{}".format(
                            request_cnt,
                            from_user,
                            message_id,
                            content,
                            reply_text,
                        )
                    )
                    replyPost = create_reply(reply_text, msg)
                    return encrypt_func(replyPost.render())
            else:
                logger.info("暂且不处理")
            return "success"
        except Exception as exc:
            logger.exception(exc)
            return exc
