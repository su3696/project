import signal
import sys

from channel import channel_factory
from tool.log import logger
from config import conf, load_config


def sigterm_handler_wrap(_signo):
    old_handler = signal.getsignal(_signo)

    def func(_signo, _stack_frame):
        logger.info("signal {} received, exiting...".format(_signo))
        conf().save_user_datas()
        if callable(old_handler):  #  check old_handler
            return old_handler(_signo, _stack_frame)
        sys.exit(0)

    signal.signal(_signo, func)


def run():
    try:
        # load config
        load_config()
        # ctrl + c
        sigterm_handler_wrap(signal.SIGINT)
        # kill signal
        sigterm_handler_wrap(signal.SIGTERM)

        # create channel
        channel_name = conf().get("channel_type", "wx")

        if "--cmd" in sys.argv:
            channel_name = "terminal"

        channel = channel_factory.create_channel(channel_name)
        #if channel_name in ["wechatmp"]:
        #    PluginManager().load_plugins()

        # startup channel
        channel.startup()
    except Exception as e:
        logger.error("startup failed!")
        logger.exception(e)


if __name__ == "__main__":
    run()
