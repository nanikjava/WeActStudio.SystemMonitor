# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/

# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
# Copyright (C) 2022-2023  Rollbacke
# Copyright (C) 2022-2023  Ebag333
# Copyright (C) 2024-2024  WeAct Studio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import queue
import sys

import yaml

from library.log import logger


def load_yaml(configfile):
    with open(configfile, "rt", encoding='utf8') as stream:
        yamlconfig = yaml.safe_load(stream)
        return yamlconfig


PATH = sys.path[0]
CONFIG_DATA = load_yaml("config.yaml")
THEME_DEFAULT = load_yaml("res/configs/default.yaml")
THEME_SETTING = load_yaml("res/configs/theme_setting.yaml")
THEME_EXAMPLE = load_yaml("res/configs/theme_example.yaml")
THEME_DATA = None
THEME_DATA_EDIT = None

def copy_default(default, theme):
    """recursively supply default values into a dict of dicts of dicts ...."""
    for k, v in default.items():
        if k not in theme:
            theme[k] = v
        if type(v) == type({}):
            copy_default(default[k], theme[k])

def load_theme_edit():
    global THEME_DATA_EDIT
    try:
        theme_path = "res/themes/" + CONFIG_DATA['config']['THEME'] + "/"
        logger.info("Loading edit theme %s from %s" % (CONFIG_DATA['config']['THEME'], theme_path + "theme.yaml"))
        THEME_DATA_EDIT = load_yaml(theme_path + "theme.yaml")
        THEME_DATA_EDIT['PATH'] = theme_path
        THEME_SETTING['PATH'] = None
    except:
        logger.error("Theme not found or contains errors!")
        try:
            sys.exit(0)
        except:
            os._exit(0)

def load_theme():
    global THEME_DATA
    try:
        theme_path = "res/themes/" + CONFIG_DATA['config']['THEME'] + "/"
        logger.info("Loading theme %s from %s" % (CONFIG_DATA['config']['THEME'], theme_path + "theme.yaml"))
        THEME_DATA = load_yaml(theme_path + "theme.yaml")
        THEME_DATA['PATH'] = theme_path
    except:
        logger.error("Theme not found or contains errors!")
        try:
            sys.exit(0)
        except:
            os._exit(0)

    copy_default(THEME_DEFAULT, THEME_DATA)

def load_edit(edit):
    global THEME_DATA
    import copy
    THEME_DATA = copy.deepcopy(edit)
    copy_default(THEME_DEFAULT, THEME_DATA)

def save_to_file(edit):
    theme_path = "res/themes/" + CONFIG_DATA['config']['THEME'] + "/"
    yaml_path = theme_path + 'theme.yaml'
    import copy
    save = copy.deepcopy(edit)
    del save['PATH']
    with open(yaml_path, 'w' ,encoding='utf-8') as file:  
        yaml.dump(save, file, allow_unicode=True)

def check_theme_compatible(display_size: str):
    global THEME_DATA
    # Check if theme is compatible with hardware revision
    if display_size != THEME_DATA['display'].get("DISPLAY_SIZE", '320x480'):
        logger.error("The selected theme " + CONFIG_DATA['config'][
            'THEME'] + " is not compatible with your display revision " + CONFIG_DATA["display"]["REVISION"])
        try:
            sys.exit(0)
        except:
            os._exit(0)

load_theme_edit()
# Load theme on import
load_theme()

# Queue containing the serial requests to send to the screen
update_queue = queue.Queue()
