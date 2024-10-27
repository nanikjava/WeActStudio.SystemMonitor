import os

import library.config as config
from library.display import display
from library.log import logger
import random 

def get_theme_file_path(name):
    if name:
        return os.path.join(config.THEME_DATA['PATH'], name)
    else:
        return None

def list_theme_pic():
        pic = list()
        for root, dirs, files in os.walk(config.THEME_DATA_EDIT["PATH"]):
            for file in files:
                file_l = file.lower()
                if (
                    file_l.endswith(".png")
                    or file_l.endswith(".jpg")
                    or file_l.endswith(".bmp")
                ):
                    if len(root) > len(config.THEME_DATA_EDIT["PATH"]):
                        root_path = root[len(config.THEME_DATA_EDIT["PATH"]) :]
                        if root_path.startswith("Photos\\") or root_path.startswith("Photos/") or root_path == "Photos":
                            path = root[len(config.THEME_DATA_EDIT["PATH"]) :] + "/" + file
                            pic.append(get_theme_file_path(path))
                    # else:
                    #     pic.append(file)
        return pic

class photo_album:
    theme_data = []
    theme_data_ok = False
    background_image = ''
    background_color = ''
    show = False
    show_sequential = True
    x = 0
    y = 0
    align = ''
    max_width = 0
    max_height = 0
    auto_refresh = False
    interval = 3
    theme_pic_list = []
    theme_pic_id = 0
    @classmethod
    def init(cls):
        cls.show = False
        cls.theme_data_ok = False
        cls.theme_pic_id = 0
        cls.show_sequential = True
        cls.align = 'left'
        cls.auto_refresh = False
        if config.THEME_DATA.get('photo_album', False):
            cls.theme_data = config.THEME_DATA['photo_album']
            cls.show = cls.theme_data.get("SHOW", False)
            if cls.show == True:
                cls.background_image = get_theme_file_path(cls.theme_data.get("BACKGROUND_IMAGE", None))
                cls.background_color = cls.theme_data.get("BACKGROUND_COLOR", (0, 0, 0))
                cls.show_sequential = not cls.theme_data.get("SHOW_RANDOM", False)
                cls.interval = cls.theme_data.get("INTERVAL", 3)
                cls.x = cls.theme_data.get("X", 0)
                cls.y = cls.theme_data.get("Y", 0)
                cls.align = cls.theme_data.get("ALIGN",'left')
                cls.max_width = cls.theme_data.get("MAX_WIDTH", 0)
                cls.max_height = cls.theme_data.get("MAX_HEIGHT", 0)
                if cls.max_width == 0:
                    cls.max_width = display.lcd.get_width()
                if cls.max_height == 0:
                    cls.max_height = display.lcd.get_height()
                cls.auto_refresh = cls.theme_data.get("AUTO_REFRESH", False)
                cls.theme_pic_list = list_theme_pic()
                cls.theme_data_ok = True
                return
        cls.theme_data_ok = False

    @classmethod
    def handle(cls):
        refresh = False
        if cls.theme_data_ok:

            if config.update_queue.qsize() > 50:
                print(f"serial queue overload: {config.update_queue.qsize()}")
                return refresh
            
            if cls.auto_refresh == True:
                cls.theme_pic_list = list_theme_pic()

            if  len(cls.theme_pic_list) == 0:
                cls.theme_pic_id = 0
                return refresh
            
            if cls.show_sequential == True:
                pic_path = cls.theme_pic_list[cls.theme_pic_id]
                cls.theme_pic_id = cls.theme_pic_id + 1
                if cls.theme_pic_id > len(cls.theme_pic_list) - 1:
                    cls.theme_pic_id = 0
            else:
                pic_path= random.choice(cls.theme_pic_list)

            display.lcd.DisplayImage2(
                    x=cls.x,
                    y=cls.y,
                    max_width=cls.max_width,
                    max_height=cls.max_height,
                    image=pic_path,
                    align=cls.align,
                    background_color=cls.background_color,
                    background_image=cls.background_image)
            refresh = True

        return refresh