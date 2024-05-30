


def create_channel(channel_type):
    if channel_type == "wechatmp":
        from channel.wechatmp.wechatmp_channel import WechatMPChannel
        return WechatMPChannel(wechatmp_reply=True)
        
    raise RuntimeError
