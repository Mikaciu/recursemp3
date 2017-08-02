#!/usr/bin/env python3
import logging

from colorlog import ColoredFormatter


class LoggerConfig:
    LOGGER_2DO = logging.INFO + 1

    def __init__(self):
        super()

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

        # create console handler and set level to debug
        ch = logging.StreamHandler()

        # add formatter to ch
        ch.setFormatter(self.formatter)

        logging.basicConfig(level=logging.WARNING, handlers=[ch])

        logging.addLevelName(LoggerConfig.LOGGER_2DO, '2DO')

    def getLogger(self, logger_name):
        return logging.getLogger(logger_name)
