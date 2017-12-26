#!/usr/bin/env python3

import logging
from tqdm import tqdm
from colorlog import ColoredFormatter


class LoggerHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)

        # {color}, fg_{color}, bg_{color}: Foreground and background colors.
        # The color names are black, red, green, yellow, blue, purple, cyan and white.
        # bold, bold_{color}, fg_bold_{color}, bg_bold_{color}: Bold/bright colors.
        # reset: Clear all formatting (both foreground and background colors).
        self.formatter = ColoredFormatter(
            "%(fg_yellow)s%(asctime)s%(reset)s %(log_color)s%(levelname)-8s%(reset)s [%(module)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                'DEBUG': 'purple',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
                '2DO': 'blue',
            },
            secondary_log_colors={},
            style='%'
        )

    def emit(self, record):
        msg = self.format(record)
        tqdm.write(msg)


class LoggerConfig:
    LOGGER_2DO = logging.INFO + 1

    def __init__(self):
        super()

        # create console handler and set level to debug
        console_handler = LoggerHandler()

        logging.basicConfig(level=logging.WARNING, handlers=[console_handler])

        logging.addLevelName(LoggerConfig.LOGGER_2DO, '2DO')

    @staticmethod
    def get_logger(logger_name):
        return logging.getLogger(logger_name)
