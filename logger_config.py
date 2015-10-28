#!/usr/bin/env python3
import logging
from colorlog import ColoredFormatter


# {color}, fg_{color}, bg_{color}: Foreground and background colors.
# The color names are black, red, green, yellow, blue, purple, cyan and white.
# bold, bold_{color}, fg_bold_{color}, bg_bold_{color}: Bold/bright colors.
# reset: Clear all formatting (both foreground and background colors).
formatter = ColoredFormatter(
    "%(fg_yellow)s%(asctime)s%(reset)s %(log_color)s%(levelname)-8s%(reset)s %(message)s",
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
# ch.setLevel(logging.NOTSET)

# add formatter to ch
ch.setFormatter(formatter)

logging.basicConfig(level=logging.WARNING, handlers=[ch])
