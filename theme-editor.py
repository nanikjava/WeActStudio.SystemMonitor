#!/usr/bin/env python
# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/

# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
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

# theme-editor.py: Allow to easily edit themes for System Monitor (main.py) in a preview window on the computer
# The preview window is refreshed as soon as the theme file is modified

import locale
import logging
import os
import platform
import subprocess
import sys
import time
import copy
import gettext

sys.path.append(os.path.dirname(__file__))
MIN_PYTHON = (3, 8)
if sys.version_info < MIN_PYTHON:
    print("[ERROR] Python %s.%s or later is required." % MIN_PYTHON)
    try:
        sys.exit(0)
    except:
        os._exit(0)

import tkinter
from tkinter import ttk
from tkinter import colorchooser
from tkinter import scrolledtext
from tkinter import messagebox
from PIL import ImageTk

if len(sys.argv) != 2:
    print("Usage :")
    print("        theme-editor.py theme-name")
    print("Examples : ")
    print("        theme-editor.py 3.5inchTheme2")
    print("        theme-editor.py Landscape6Grid")
    print("        theme-editor.py Cyberpunk")
    try:
        sys.exit(0)
    except:
        os._exit(0)

import library.log

# Hardcode specific configuration for theme editor
from library import config

config.CONFIG_DATA["config"][
    "HW_SENSORS"
] = "STATIC"  # For theme editor always use stub data
config.CONFIG_DATA["config"]["THEME"] = sys.argv[1]  # Theme is given as argument

config.load_theme()

# For theme editor, always use simulated LCD
if config.THEME_DATA["display"].get("DISPLAY_SIZE", "320x480") == "480x800":
    config.CONFIG_DATA["display"]["REVISION"] = "SIMU_480x800"
else:
    config.CONFIG_DATA["display"]["REVISION"] = "SIMU_320x480"

from library.display import display  # Only import display after hardcoded config is set


class dict_tools:
    def sort_dict_by_order(d, order):
        """
        根据指定的顺序对字典的键进行排序，并返回一个新的字典。
        如果原始字典中有不在指定顺序中的键，它们将被添加到结果字典的末尾（保持插入顺序）。

        参数:
        d (dict): 原始字典。
        order (list): 包含排序顺序的键的列表。

        返回:
        dict: 按键排序后的新字典。
        """
        # 初始化一个空字典来存储排序后的键值对
        sorted_dict = {}

        # 遍历order列表，如果键在字典d中，则添加到sorted_dict中
        for key in order:
            if key in d:
                sorted_dict[key] = d[key]

        # 遍历字典d的剩余键（即那些不在order中的键），并将它们添加到sorted_dict中
        # 注意：这将保持这些键在sorted_dict中的添加顺序（Python 3.7+）
        for key in d:
            if key not in sorted_dict:
                sorted_dict[key] = d[key]

        return sorted_dict


class file_tools:
    res_fonts_path = "res/fonts/"

    def list_res_fonts():
        fonts = list()
        for root, dirs, files in os.walk(file_tools.res_fonts_path):
            for file in files:
                if file.lower().endswith(".ttf"):
                    fonts.append(root[len(file_tools.res_fonts_path) :] + "/" + file)
                elif file.lower().endswith(".otf"):
                    fonts.append(root[len(file_tools.res_fonts_path) :] + "/" + file)
        return fonts

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
                    pic.append(file)
        return pic


file_tools.list_res_fonts()


class theme_editor:
    def __init__(self) -> None:
        self.image_scaler_process = None

        self.RGB_LED_MARGIN = 12

        self.x0 = 0
        self.y0 = 0

        self.theme_refresh = False
        self.theme_file_unsave = False

        self.image_scaler = None

        library.log.logger.setLevel(
            logging.NOTSET
        )  # Disable system monitor logging for the editor

        # Create a logger for the editor
        self.logger = logging.getLogger("theme-editor")
        self.logger.setLevel(logging.DEBUG)

        # Apply system locale to this program
        locale.setlocale(locale.LC_ALL, "")

        self.logger.debug("Starting WeAct Studio System Monitor Theme Editor...")

        # Get theme file to edit
        self.theme_file = config.THEME_DATA["PATH"] + "theme.yaml"
        self.last_edit_time = os.path.getmtime(self.theme_file)
        self.logger.debug("Using theme file " + self.theme_file)

        # Open theme in default editor. You can also open the file manually in another program
        self.logger.debug(
            "Opening theme file in your default editor. If it does not work, open it manually in the "
            "editor of your choice"
        )
        # if platform.system() == 'Darwin':  # macOS
        #     subprocess.call(('open', "./" + self.theme_file))
        # elif platform.system() == 'Windows':  # Windows
        #     os.startfile(".\\" + self.theme_file)
        # else:  # linux variants
        #     subprocess.call(('xdg-open', "./" + self.theme_file))

        # Load theme file and generate first preview
        self.refresh_theme()

        # Create preview window
        self.logger.debug("Opening theme preview window with static data")

        self.main = tkinter.Tk()

        self.main.title(_("WeAct Studio System Monitor Theme Editor"))

        self.main.iconphoto(True, tkinter.PhotoImage(file="res/icons/logo.png"))
        self.main.geometry(
            str(display.lcd.get_width() + 3 * self.RGB_LED_MARGIN + 450)
            + "x"
            + str(display.lcd.get_height() + 4 * self.RGB_LED_MARGIN + 40 + 100)
        )
        self.main.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.main.resizable(False, False)

        self.viewer = tkinter.Frame(self.main)
        self.viewer.config(cursor="cross")
        # Display RGB backplate LEDs color as background color
        led_color = config.THEME_DATA["display"].get("DISPLAY_RGB_LED", (255, 255, 255))
        if isinstance(led_color, str):
            led_color = tuple(map(int, led_color.split(", ")))
        self.viewer.configure(bg="#%02x%02x%02x" % led_color)
        # viewer.pack(fill=tkinter.BOTH, expand=True)
        self.viewer.place(
            x=0,
            y=0,
            width=display.lcd.get_width() + 2 * self.RGB_LED_MARGIN,
            height=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN + 40,
        )

        # Display preview in the window
        self.display_image = ImageTk.PhotoImage(display.lcd.screen_image)
        self.viewer_picture = tkinter.Label(
            self.viewer, image=self.display_image, borderwidth=0
        )
        self.viewer_picture.place(x=self.RGB_LED_MARGIN, y=self.RGB_LED_MARGIN)

        # Allow to click on preview to show coordinates and draw zones
        self.viewer_picture.bind("<ButtonPress-1>", self.on_button1_press)
        self.viewer_picture.bind("<B1-Motion>", self.on_button1_press_and_drag)
        self.viewer_picture.bind("<ButtonRelease-1>", self.on_button1_release)

        self.label_coord = tkinter.Label(
            self.viewer, text=_("Click or draw a zone to show coordinates")
        )
        self.label_coord.place(
            x=0,
            y=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN,
            width=display.lcd.get_width() + 2 * self.RGB_LED_MARGIN,
        )

        self.label_info = tkinter.Label(
            self.viewer,
            text=_("This preview size: ")
            + f"{display.lcd.get_width()}x{display.lcd.get_height()}",
        )
        self.label_info.place(
            x=0,
            y=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN + 20,
            width=display.lcd.get_width() + 2 * self.RGB_LED_MARGIN,
        )

        self.label_zone = tkinter.Label(
            self.viewer, bg="#%02x%02x%02x" % tuple(map(lambda x: 255 - x, led_color))
        )
        self.label_zone.bind("<ButtonRelease-1>", self.on_zone_click)

        self.file_frame_init()
        self.theme_init()
        self.editor_init()
        self.logger_frame_init()
        # self.editor_refresh()
        self.main_refresh()

        self.logger.debug(
            "You can now edit the theme file in the editor. When you save your changes, the preview window will "
            "update automatically"
        )

        self.main.mainloop()

    def file_frame_init(self):
        self.file_frame = tkinter.Frame(self.main)
        self.file_frame.place(
            x=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN,
            y=0,
            width=450,
            height=30,
        )
        button = ttk.Button(
            self.file_frame,
            text=_("Save to file"),
            command=self.on_file_save_button_press,
        )
        button.pack(side="left")

        button_imgae = ttk.Button(
            self.file_frame,
            text=_("Image Scaler"),
            command=self.on_file_image_scaler_button_press,
        )
        button_imgae.pack(side="left")

    def on_file_save_button_press(self):
        self.logger.info("Start Save THEME_DATA_EDIT To File")
        config.save_to_file(config.THEME_DATA_EDIT)

    def on_file_image_scaler_button_press(self):
        if self.image_scaler_process != None:
            if self.image_scaler_process.poll() == None:
                messagebox.showerror("Error", "image scaler tool is running !")
                return
        sys.path.append(".")
        self.image_scaler_process = subprocess.Popen(
            (
                "python",
                os.path.join(os.getcwd(), "image_scaler_tool.py")
            ),
            shell=True,
        )

    def logger_frame_init(self):
        self.logger_frame = tkinter.Frame(self.main)
        self.logger_frame.place(
            x=0,
            y=display.lcd.get_height() + 3 * self.RGB_LED_MARGIN + 40,
            width=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN + 450,
            height=100,
        )
        self.log_text = scrolledtext.ScrolledText(
            self.logger_frame, wrap=tkinter.WORD, state="disabled"
        )
        self.log_text.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)

        def clear_log():
            self.log_text.config(state="normal")  # 允许修改文本
            self.log_text.delete(1.0, tkinter.END)
            self.log_text.config(state="disabled")

        popup_menu = tkinter.Menu(self.logger_frame, tearoff=0)
        popup_menu.add_command(label=_("Clear log"), command=clear_log)

        def show_popup(event):
            try:
                # 尝试获取当前选中的文本区域（如果没有选中的话，则为None）
                text_widget = event.widget
                popup_menu.tk_popup(event.x_root, event.y_root)
            finally:
                # 确保菜单在点击其他位置时消失
                popup_menu.grab_release()

        self.log_text.bind("<Button-3>", show_popup)

        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("normal", foreground="black")

        self.logger_normal_message("Start System Monitor Theme Editor")

    def logger_normal_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(
            tkinter.END, f"{time.strftime('%H:%M:%S')}> {message}\n", "normal"
        )
        self.log_text.config(state="disabled")
        self.log_text.yview(tkinter.END)

    def logger_error_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(
            tkinter.END, f"{time.strftime('%H:%M:%S')}> {message}\n", "error"
        )
        self.log_text.config(state="disabled")
        self.log_text.yview(tkinter.END)

    def theme_init(self):
        self.theme = tkinter.Frame(self.main)
        self.theme_tree = ttk.Treeview(self.theme, show="tree")
        self.theme_tree.pack(side="left", fill=tkinter.BOTH, expand=True)
        # self.theme_tree.bind("<Double-1>", self.on_theme_tree_item_double_click)
        self.theme_tree.bind(
            "<Button-3>",
            lambda e, f=self.theme: self.on_theme_tree_item_right_click(
                event=e, frame=f
            ),
        )
        self.theme_tree.bind("<<TreeviewSelect>>", self.on_theme_tree_select)
        vsb = ttk.Scrollbar(
            self.theme, orient="vertical", command=self.theme_tree.yview
        )
        vsb.pack(side="right", fill=tkinter.Y, expand=False)
        self.theme_tree.configure(yscrollcommand=vsb.set)

        self.theme_tree_root_node = self.theme_tree.insert(
            "", "end", text=self.theme_file
        )

        order = ["author", "display", "static_images", "static_text"]
        sorted_d = dict_tools.sort_dict_by_order(config.THEME_DATA_EDIT, order)
        import copy

        config.THEME_DATA_EDIT = copy.deepcopy(sorted_d)

        self.theme_tree_add_data(self.theme_tree_root_node, config.THEME_DATA_EDIT)
        self.theme_tree.item(self.theme_tree_root_node, open=True)

        self.theme.place(
            x=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN,
            y=25 + self.RGB_LED_MARGIN,
            width=450,
            height=display.lcd.get_height()
            + 2 * self.RGB_LED_MARGIN
            - 50
            - (25 + self.RGB_LED_MARGIN),
        )

    def theme_tree_add_data(self, node, data):
        for index, key in enumerate(data):
            iid = f"{node}-{index}"  # 生成唯一的iid
            children_data = data[key]
            if isinstance(children_data, dict):
                children_node = self.theme_tree.insert(node, "end", iid=iid, text=key)
                self.theme_tree_add_data(children_node, children_data)
            elif isinstance(children_data, str):
                self.theme_tree.insert(
                    node, "end", iid=iid, text=key + ": " + children_data
                )
            else:
                self.theme_tree.insert(
                    node, "end", iid=iid, text=key + ": " + str(children_data)
                )

    def theme_tree_get_item_id_split_length(self, item_id):
        length = len(item_id.split("-"))
        return length

    def theme_tree_item_get_setting_config_value(self, item_id):
        item_id_split = item_id.split("-")
        config_theme = item_id_split[0]
        config_data = config.THEME_DATA_EDIT
        config_value = ""
        length = len(item_id_split) - 1
        for i, path in enumerate(item_id_split[1:]):
            config_theme = config_theme + "-" + path
            config_id = self.theme_tree.item(config_theme, "text").split(": ")[0]
            if i == length - 1:
                break
            else:
                config_value = config_data[config_id]
                if isinstance(config_value, dict):
                    config_data = config_value
        try:
            return config.THEME_SETTING[config_id]
        except:
            return None

    def theme_tree_item_get_config_value(self, config_data, item_id):
        item_id_split = item_id.split("-")
        config_theme = item_id_split[0]
        config_value = ""
        for path in item_id_split[1:]:
            config_theme = config_theme + "-" + path
            config_id = self.theme_tree.item(config_theme, "text").split(": ")[0]
            config_value = config_data[config_id]
            if isinstance(config_value, dict):
                config_data = config_value
        return config_value

    def theme_tree_item_get_config_dict(self, config_data, item_id):
        item_id_split = item_id.split("-")
        config_theme = item_id_split[0]
        config_value = ""
        length = len(item_id_split) - 1
        config_key = None
        for i, path in enumerate(item_id_split[1:]):
            config_theme = config_theme + "-" + path
            config_key = self.theme_tree.item(config_theme, "text").split(": ")[0]
            if i == length - 1:
                break
            else:
                config_value = config_data[config_key]
                if isinstance(config_value, dict):
                    config_data = config_value
                else:
                    return None
        try:
            if length:
                return config_data[config_key]
            else:
                return config_data
        except:
            return None

    def theme_tree_item_get_config_last_dict(self, config_data, item_id):
        item_id_split = item_id.split("-")
        config_theme = item_id_split[0]
        config_value = ""
        length = len(item_id_split) - 1
        if length == 1:
            return config_data
        config_key = None
        for i, path in enumerate(item_id_split[1:]):
            config_theme = config_theme + "-" + path
            config_key = self.theme_tree.item(config_theme, "text").split(": ")[0]

            if i == length - 2:
                break
            else:
                config_value = config_data[config_key]
                if isinstance(config_value, dict):
                    config_data = config_value
                else:
                    return None
        try:
            if length:
                return config_data[config_key]
            else:
                return config_data
        except:
            return None

    def theme_tree_item_set_config_value(self, config_data, item_id, value):
        item_id_split = item_id.split("-")
        config_theme = item_id_split[0]
        config_value = ""
        length = len(item_id_split) - 1
        for i, path in enumerate(item_id_split[1:]):
            config_theme = config_theme + "-" + path
            config_id = self.theme_tree.item(config_theme, "text").split(": ")[0]
            if i == length - 1:
                config_data[config_id] = value
            else:
                config_value = config_data[config_id]
                if isinstance(config_value, dict):
                    config_data = config_value

    def theme_tree_item_delete_config_value(self, config_data, item_id):
        item_id_split = item_id.split("-")
        config_theme = item_id_split[0]
        config_value = ""
        length = len(item_id_split) - 1
        for i, path in enumerate(item_id_split[1:]):
            config_theme = config_theme + "-" + path
            config_id = self.theme_tree.item(config_theme, "text").split(": ")[0]
            if i == length - 1:
                del config_data[config_id]
            else:
                config_value = config_data[config_id]
                if isinstance(config_value, dict):
                    config_data = config_value

    def on_theme_tree_delete_item(self):
        # 获取被右键点击的项的iid
        selection = self.theme_tree.selection()[0]
        if selection:
            selection_s = selection.split("-")
            # 不删除主节点
            if len(selection_s) > 1:
                # 删除选中的项
                self.theme_tree_item_delete_config_value(
                    config.THEME_DATA_EDIT, selection
                )
                # 删除所有节点
                children = self.theme_tree.get_children("")
                for child in children:
                    self.theme_tree.delete(child)
                self.theme_tree_root_node = self.theme_tree.insert(
                    "", "end", text=self.theme_file
                )
                self.theme_tree_add_data(
                    self.theme_tree_root_node, config.THEME_DATA_EDIT
                )
                # 重新打开节点
                selection_s[0] = self.theme_tree_root_node
                node = selection_s[0]
                self.theme_tree.item(node, open=True)
                for i in selection_s[1:-1]:
                    node = node + "-" + i
                    print(node)
                    self.theme_tree.item(node, open=True)
                self.theme_refresh = True

    def on_theme_tree_add_item(self, config_dict, item_key, item_value):
        config_dict[item_key] = item_value

        order = ["author", "display", "static_images", "static_text"]
        sorted_d = dict_tools.sort_dict_by_order(config_dict, order)
        import copy

        config_dict = copy.deepcopy(sorted_d)

        selection = self.theme_tree.selection()[0]
        if selection:
            selection_s = selection.split("-")
            # 删除所有节点
            children = self.theme_tree.get_children("")
            for child in children:
                self.theme_tree.delete(child)
            self.theme_tree_root_node = self.theme_tree.insert(
                "", "end", text=self.theme_file
            )
            self.theme_tree_add_data(self.theme_tree_root_node, config.THEME_DATA_EDIT)
            # 重新打开节点
            selection_s[0] = self.theme_tree_root_node
            node = selection_s[0]
            try:
                self.theme_tree.item(node, open=True)
                for i in selection_s[1:]:
                    node = node + "-" + i
                    self.theme_tree.item(node, open=True)
                self.theme_tree.selection_set(node)
                self.theme_tree.see(node)
            except:
                print("reopen error")
            self.theme_refresh = True

    def on_theme_tree_item_right_click(self, event, frame):
        item = self.theme_tree.identify("item", event.x, event.y)
        if item:
            selection = self.theme_tree.selection()
            if selection:
                if selection[0] == item:
                    selection_length = self.theme_tree_get_item_id_split_length(
                        selection[0]
                    )
                    config_value = self.theme_tree_item_get_config_value(
                        config.THEME_DATA_EDIT, selection[0]
                    )
                    item_text = self.theme_tree.item(
                            selection[0], "text"
                    )

                    self.theme_tree.focus_set()
                    popup_menu = tkinter.Menu(frame, tearoff=0)
                    
                    if True:
                        if selection_length > 1:
                            can_add_delete = False
                            if selection_length == 2:
                                if isinstance(config_value, dict) and item_text != 'display':
                                    can_add_delete = True
                            else:
                                can_add_delete =  True
                                
                            if can_add_delete:
                                popup_menu.add_command(
                                    label="Delete", command=self.on_theme_tree_delete_item
                                )

                        if isinstance(config_value, dict) or selection_length == 1:
                            show_add_menu = True

                            theme_example = self.theme_tree_item_get_config_dict(
                                config.THEME_EXAMPLE, selection[0]
                            )
                            if theme_example != None:

                                theme_example_keys = theme_example.keys()

                                theme_edit = self.theme_tree_item_get_config_dict(
                                    config.THEME_DATA_EDIT, selection[0]
                                )
                                theme_edit_keys = theme_edit.keys()

                                for key in theme_example_keys:
                                    if key not in theme_edit_keys:
                                        item_value = copy.deepcopy(theme_example[key])
                                        if show_add_menu:
                                            show_add_menu = False
                                            add_menu = tkinter.Menu(popup_menu, tearoff=0)
                                            popup_menu.add_cascade(
                                                label="Add", menu=add_menu
                                            )

                                        add_menu.add_command(
                                            label=key,
                                            command=lambda c=theme_edit, k=key, i=item_value: self.on_theme_tree_add_item(
                                                config_dict=c, item_key=k, item_value=i
                                            ),
                                        )
                    try:
                        popup_menu.tk_popup(event.x_root, event.y_root)
                    finally:
                        popup_menu.grab_release()

    def on_theme_tree_select(self, event):
        self.editor_refresh()

    def editor_init(self):
        self.editor = tkinter.Frame(self.main)
        self.editor_set_free()
        self.theme_tree_selection = None
        self.theme_tree_selection_last = None

    def editor_set_free(self):
        self.editor.destroy()
        self.editor = tkinter.Frame(self.main)
        self.label_top = tkinter.Label(
            self.editor, text=_("Waiting selection"), font=("Arial", 12, "bold")
        )
        self.label_top.grid(row=0, column=0, columnspan=10, sticky="w")
        self.editor.place(
            x=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN,
            y=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN - 50,
            width=450,
            height=100,
        )

    def editor_display(self, selection, title, value):
        self.editor.destroy()

        self.editor = tkinter.Frame(self.main)
        self.editor.place(
            x=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN,
            y=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN - 50,
            width=450,
            height=100,
        )

        label = tkinter.Label(
            self.editor, text=title + _(" Editor"), font=("Arial", 12, "bold")
        )
        label.grid(row=0, column=0, columnspan=10, sticky="w")

        label_tips = tkinter.Label(self.editor, text="", font=("Arial", 10))
        label_tips["text"] = _("Please input")
        label_tips.grid(row=1, column=0, columnspan=10, sticky="w")

        setting_row = 2

        setting_value = None
        is_colorchooser = 0
        is_combobox = 0

        # Get standard Settings
        try:
            setting_value = self.theme_tree_item_get_setting_config_value(selection)
        except:
            self.logger.debug("No Found Setting Value")
        # Query whether any standard Settings are available
        if setting_value != None and type(setting_value) == dict:
            combobox_list = list()
            combobox_select = 0
            for index, key in enumerate(setting_value):
                v = setting_value[key]
                combobox_list.append(v)
                if v == value:
                    combobox_select = index
            if title == "FORMAT":
                combobox = ttk.Combobox(self.editor)
            else:
                combobox = ttk.Combobox(self.editor, state="readonly")
            combobox["value"] = combobox_list
            combobox.current(combobox_select)
            combobox.grid(row=setting_row, column=0, columnspan=10, sticky="w" + "e")

            label_tips["text"] = _("Please Select")

            def on_confirm():
                v = combobox.get()
                if v != value:
                    self.theme_tree_item_set_config_value(
                        config.THEME_DATA_EDIT, selection, v
                    )
                    if type(v) != str:
                        v = str(v)
                    self.theme_tree.item(selection, text=title + ": " + v)
                    self.editor_display(selection, title, v)
                    self.theme_refresh = True

            confirm_button = ttk.Button(
                self.editor, text=_("Confirm"), command=on_confirm
            )
            confirm_button.grid(
                row=setting_row, column=11, columnspan=1, sticky="w" + "e"
            )
        else:
            if type(value) == int:

                def restrict_entry(event):
                    current_text = event.widget.get()
                    cursor_index = event.widget.index(tkinter.INSERT)
                    new_char = event.char

                    # 如果用户按下的是Backspace键（ASCII码为8）或Delete键（在Mac上可能是127）
                    # 则允许删除操作
                    if new_char in ("", "\x7f", "\x08"):
                        return

                    if (
                        cursor_index == 0 and event.char == "-"
                    ) or event.char.isdigit():
                        return
                    else:
                        event.widget.delete(len(current_text), tkinter.END)
                        return "break"

                entry = ttk.Entry(self.editor, width=50)
                entry.bind("<Key>", restrict_entry)
                entry.grid(row=setting_row, column=0, columnspan=10, sticky="w" + "e")
                entry.insert(0, str(value))
                entry.focus_set()
            elif type(value) == str:
                if title == "FONT":
                    label_tips["text"] = _("Select the font in the res/fonts/")
                    is_combobox = 1
                elif title == "PATH" or title == "BACKGROUND_IMAGE":
                    label_tips["text"] = (
                        _("Select the picture in ") + config.THEME_DATA_EDIT["PATH"]
                    )
                    is_combobox = 2
                elif title.endswith("COLOR") or title == "DISPLAY_RGB_LED":
                    label_tips["text"] = _("Select the color you like")
                    is_colorchooser = 1
                    is_combobox = 0
                else:
                    is_colorchooser = 0
                    is_combobox = 0
                if is_combobox:
                    combobox_list = list()
                    combobox_select = 0
                    if is_combobox == 1:
                        res_list = file_tools.list_res_fonts()
                    elif is_combobox == 2:
                        res_list = file_tools.list_theme_pic()
                    for index, font in enumerate(res_list):
                        combobox_list.append(font)
                        if font == value:
                            combobox_select = index

                    combobox = ttk.Combobox(self.editor, width=45, state="readonly")
                    combobox["value"] = combobox_list
                    combobox.current(combobox_select)
                    combobox.grid(
                        row=setting_row, column=0, columnspan=10, sticky="w" + "e"
                    )
                elif is_colorchooser:
                    color_v = value.split(", ")
                    color = "#{:02x}{:02x}{:02x}".format(
                        int(color_v[0]), int(color_v[1]), int(color_v[2])
                    )

                    def on_canvas_click(event, init_color):
                        color = colorchooser.askcolor(initialcolor=init_color)
                        if len(color) == 2:
                            if color[0] != None:
                                v = "{:0d}, {:0d}, {:0d}".format(
                                    color[0][0], color[0][1], color[0][2]
                                )
                                self.theme_tree_item_set_config_value(
                                    config.THEME_DATA_EDIT, selection, v
                                )
                                self.theme_tree.item(selection, text=title + ": " + v)
                                self.editor_display(selection, title, v)
                                self.theme_refresh = True

                    canvas = tkinter.Canvas(self.editor, width=75, height=25)
                    canvas.delete("all")
                    canvas.create_rectangle(2, 2, 75, 25, fill=color, outline="black")
                    canvas.grid(
                        row=setting_row, column=0, columnspan=10, sticky="w" + "e"
                    )
                    canvas.bind("<Button-1>", lambda e, c=color: on_canvas_click(e, c))
                else:
                    entry = ttk.Entry(self.editor, width=50)
                    entry.grid(
                        row=setting_row, column=0, columnspan=10, sticky="w" + "e"
                    )
                    entry.insert(0, value)
                    entry.focus_set()
            elif type(value) == bool:
                bool_var = tkinter.BooleanVar()
                bool_var.set(value)
                check_button = ttk.Checkbutton(
                    self.editor, text=title, variable=bool_var
                )
                check_button.grid(
                    row=setting_row, column=0, columnspan=10, sticky="w" + "e"
                )

            if is_colorchooser == 0:
                def on_confirm(event=None):
                    if type(value) == str:
                        if is_combobox:
                            v = combobox.get()
                        else:
                            v = entry.get()
                        if v != value:
                            self.theme_tree_item_set_config_value(
                                config.THEME_DATA_EDIT, selection, v
                            )
                            self.theme_tree.item(selection, text=title + ": " + v)
                            self.editor_display(selection, title, v)
                            self.theme_refresh = True
                    elif type(value) == int:
                        v = entry.get()
                        if v != str(value):
                            self.theme_tree_item_set_config_value(
                                config.THEME_DATA_EDIT, selection, int(v)
                            )
                            self.theme_tree.item(selection, text=title + ": " + v)
                            self.editor_display(selection, title, int(v))
                            self.theme_refresh = True
                    elif type(value) == bool:
                        v = bool_var.get()
                        if v != value:
                            self.theme_tree_item_set_config_value(
                                config.THEME_DATA_EDIT, selection, v
                            )
                            self.theme_tree.item(selection, text=title + ": " + str(v))
                            self.editor_display(selection, title, v)
                            self.theme_refresh = True

                try:
                    entry.bind("<Return>", on_confirm)
                except:
                    pass

                confirm_button = ttk.Button(
                    self.editor, text=_("Confirm"), command=on_confirm
                )
                confirm_button.grid(
                    row=setting_row, column=11, columnspan=1, sticky="w" + "e"
                )

    def editor_display_dict(self, selection, title):
        self.editor.destroy()

        self.editor = tkinter.Frame(self.main)
        self.editor.place(
            x=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN,
            y=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN - 50,
            width=450,
            height=100,
        )

        label = tkinter.Label(self.editor, text=_("Name Editor"))
        label.grid(row=0, column=0, columnspan=10, sticky="w")

        def restrict_entry(event):
            # 获取当前Entry的内容
            current_text = event.widget.get()
            # 获取刚刚输入的字符（如果是粘贴，则为空字符串）
            new_char = event.char

            # 如果用户按下的是Backspace键（ASCII码为8）或Delete键（在Mac上可能是127）
            # 则允许删除操作
            if new_char in ("", "\x08", "\x7f", "_", "-"):
                return

            if event.state == 0x04:
                return

            # 否则，检查新字符是否是数字或字母
            if not new_char.isalnum():
                # 如果不是，则阻止该事件（即不更新Entry的内容）
                event.widget.delete(len(current_text), tkinter.END)
                return "break"

        entry = ttk.Entry(self.editor, width=50)
        entry.bind("<Key>", restrict_entry)
        entry.grid(row=1, column=0, columnspan=10, sticky="w" + "e")
        entry.insert(0, title)
        entry.focus_set()

        def on_confirm():
            selcection_value = dict(
                self.theme_tree_item_get_config_dict(config.THEME_DATA_EDIT, selection)
            )
            selcection_up_value = self.theme_tree_item_get_config_last_dict(
                config.THEME_DATA_EDIT, selection
            )
            if entry.get() not in selcection_up_value.keys():
                self.theme_tree_item_delete_config_value(
                    config.THEME_DATA_EDIT, selection
                )

                self.on_theme_tree_add_item(
                    selcection_up_value, entry.get(), selcection_value
                )
                self.theme_refresh = True
            else:
                self.logger.error("Have Same Name")

        confirm_button = ttk.Button(self.editor, text=_("Confirm"), command=on_confirm)
        confirm_button.grid(row=1, column=11, columnspan=1, sticky="w" + "e")

    def editor_refresh(self):
        selection = self.theme_tree.selection()
        if selection:
            self.theme_tree_selection = selection[0]
            if self.theme_tree_selection != self.theme_tree_selection_last:
                self.theme_tree_selection_last = self.theme_tree_selection
                length = self.theme_tree_get_item_id_split_length(
                    self.theme_tree_selection
                )
                if length > 1:
                    config_value = self.theme_tree_item_get_config_value(
                        config.THEME_DATA_EDIT, self.theme_tree_selection
                    )
                    if not isinstance(config_value, dict):
                        item_text = self.theme_tree.item(
                            self.theme_tree_selection, "text"
                        )
                        title = item_text.split(": ")[0]

                        if length == 2 and title == "PATH":
                            self.editor_set_free()
                        else:
                            self.editor_display(
                                self.theme_tree_selection,
                                title,
                                config_value,
                            )
                    else:
                        parent_item = self.theme_tree.parent(self.theme_tree_selection)
                        if parent_item != "":
                            parent_text = self.theme_tree.item(parent_item, "text")
                            if length == 3 and (
                                parent_text == "static_images"
                                or parent_text == "static_text"
                            ):
                                item_text = self.theme_tree.item(
                                    self.theme_tree_selection, "text"
                                )
                                self.editor_display_dict(
                                    self.theme_tree_selection, item_text
                                )
                            else:
                                self.editor_set_free()
                        else:
                            self.editor_set_free()
        else:
            self.theme_tree_selection_last = None
            self.editor_set_free()

    def main_resize(self):
        self.main.geometry(
            str(display.lcd.get_width() + 3 * self.RGB_LED_MARGIN + 450)
            + "x"
            + str(display.lcd.get_height() + 4 * self.RGB_LED_MARGIN + 40 + 100)
        )
        self.viewer.place(
            x=0,
            y=0,
            width=display.lcd.get_width() + 2 * self.RGB_LED_MARGIN,
            height=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN + 40,
        )

        self.viewer_picture.place(x=self.RGB_LED_MARGIN, y=self.RGB_LED_MARGIN)

        self.label_coord.place(
            x=0,
            y=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN,
            width=display.lcd.get_width() + 2 * self.RGB_LED_MARGIN,
        )

        self.label_info.place(
            x=0,
            y=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN + 20,
            width=display.lcd.get_width() + 2 * self.RGB_LED_MARGIN,
        )

        self.theme.place(
            x=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN,
            y=25 + self.RGB_LED_MARGIN,
            width=450,
            height=display.lcd.get_height()
            + 2 * self.RGB_LED_MARGIN
            - 50
            - (25 + self.RGB_LED_MARGIN),
        )

        self.editor.place(
            x=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN,
            y=display.lcd.get_height() + 2 * self.RGB_LED_MARGIN - 50,
            width=450,
            height=100,
        )

        self.file_frame.place(
            x=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN,
            y=0,
            width=450,
            height=30,
        )

        self.logger_frame.place(
            x=0,
            y=display.lcd.get_height() + 3 * self.RGB_LED_MARGIN + 40,
            width=display.lcd.get_width() + 3 * self.RGB_LED_MARGIN + 450,
            height=100,
        )

    def main_refresh(self):
        if (
            os.path.exists(self.theme_file)
            and os.path.getmtime(self.theme_file) > self.last_edit_time
        ) or self.theme_refresh == True:

            if self.theme_refresh == True:
                log = "The preview window will refresh"
                self.theme_file_unsave = True
            else:
                log = "The theme file has been updated, the preview window will refresh"
                self.theme_file_unsave = False

            self.logger.debug(log)

            self.logger_normal_message(log)

            self.refresh_theme()

            self.main_resize()

            self.last_edit_time = os.path.getmtime(self.theme_file)

            # Update the preview.png that is in the theme folder
            if self.theme_refresh != True:
                display.lcd.screen_image.save(
                    config.THEME_DATA["PATH"] + "preview.png", "PNG"
                )

            # Display new picture
            self.display_image = ImageTk.PhotoImage(display.lcd.screen_image)
            self.viewer_picture.config(image=self.display_image)

            # Refresh RGB backplate LEDs color
            self.led_color = config.THEME_DATA["display"].get(
                "DISPLAY_RGB_LED", (255, 255, 255)
            )
            if isinstance(self.led_color, str):
                self.led_color = tuple(map(int, self.led_color.split(", ")))
            self.viewer.configure(bg="#%02x%02x%02x" % self.led_color)
            self.label_zone.configure(
                bg="#%02x%02x%02x" % tuple(map(lambda x: 255 - x, self.led_color))
            )

            self.theme_refresh = False

        # Regularly update the viewer window even if content unchanged
        self.main.after(100, self.main_refresh)

    def refresh_theme(self):

        if self.theme_refresh == True:
            config.load_edit(config.THEME_DATA_EDIT)
        else:
            config.load_theme()
            config.load_theme_edit()

        import traceback

        try:
            # Initialize the display
            display.initialize_display()

            # Create all static images
            display.display_static_images()

            # Create all static texts
            display.display_static_text()

            # Display all data on screen once
            import library.stats as stats

            if config.THEME_DATA["STATS"]["CPU"]["PERCENTAGE"].get("INTERVAL", 0) > 0:
                stats.CPU.percentage()
            if config.THEME_DATA["STATS"]["CPU"]["FREQUENCY"].get("INTERVAL", 0) > 0:
                stats.CPU.frequency()
            if config.THEME_DATA["STATS"]["CPU"]["LOAD"].get("INTERVAL", 0) > 0:
                stats.CPU.load()
            if config.THEME_DATA["STATS"]["CPU"]["TEMPERATURE"].get("INTERVAL", 0) > 0:
                stats.CPU.temperature()
            if config.THEME_DATA["STATS"]["CPU"]["FAN_SPEED"].get("INTERVAL", 0) > 0:
                stats.CPU.fan_speed()
            if config.THEME_DATA["STATS"]["GPU"].get("INTERVAL", 0) > 0:
                stats.Gpu.stats()
            if config.THEME_DATA["STATS"]["MEMORY"].get("INTERVAL", 0) > 0:
                stats.Memory.stats()
            if config.THEME_DATA["STATS"]["DISK"].get("INTERVAL", 0) > 0:
                stats.Disk.stats()
            if config.THEME_DATA["STATS"]["NET"].get("INTERVAL", 0) > 0:
                stats.Net.stats()
            if config.THEME_DATA["STATS"]["DATE"].get("INTERVAL", 0) > 0:
                stats.Date.stats()
            if config.THEME_DATA["STATS"]["UPTIME"].get("INTERVAL", 0) > 0:
                stats.SystemUptime.stats()
            if config.THEME_DATA["STATS"]["CUSTOM"].get("INTERVAL", 0) > 0:
                stats.Custom.stats()
            if (
                config.THEME_DATA["STATS"]["LCD_SENSOR"]["TEMPERATURE"].get(
                    "INTERVAL", 0
                )
                > 0
            ):
                stats.LcdSensor.temperature()
            if (
                config.THEME_DATA["STATS"]["LCD_SENSOR"]["HUMIDNESS"].get("INTERVAL", 0)
                > 0
            ):
                stats.LcdSensor.humidness()
        # except AssertionError as e:
        #     self.logger_error_message(e)
        # except ValueError as e:
        #     self.logger_error_message(e)
        # except UnboundLocalError as e:
        #     self.logger_error_message(e)
        except Exception as e:
            self.logger_error_message(e)
            traceback.print_exc()

    def on_closing(self):
        if self.theme_file_unsave == False:
            self.logger.debug("Exit Theme Editor...")
            try:
                sys.exit(0)
            except:
                os._exit(0)
        else:
            self.close_theme_frame = tkinter.Toplevel(self.main)
            self.close_theme_frame.title(_("Confirm"))
            main_window_x = self.main.winfo_x()
            main_window_y = self.main.winfo_y()
            main_window_width = self.main.winfo_width()
            main_window_height = self.main.winfo_height()
            width = 265
            height = 60
            x = main_window_x + (main_window_width // 2) - (width // 2)
            y = main_window_y + (main_window_height // 2) - (height // 2)
            self.close_theme_frame.geometry(f"{width}x{height}+{x}+{y}")

            def on_close_theme_frame_closing():
                self.close_theme_frame.grab_release()
                self.close_theme_frame.destroy()

            self.close_theme_frame.protocol(
                "WM_DELETE_WINDOW", on_close_theme_frame_closing
            )
            self.close_theme_frame.resizable(False, False)
            self.close_theme_frame.grab_set()

            self.delete_theme_label = ttk.Label(
                self.close_theme_frame, text=_("Do you need to save it?")
            )
            self.delete_theme_label.grid(
                row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5
            )

            def on_close_theme_frame_no():
                self.close_theme_frame.grab_release()
                self.close_theme_frame.destroy()
                self.logger.debug("Exit Theme Editor...")
                try:
                    sys.exit(0)
                except:
                    os._exit(0)

            cancel_button = ttk.Button(
                self.close_theme_frame,
                text="Cancel",
                command=on_close_theme_frame_closing,
            )
            cancel_button.grid(row=1, column=2)

            no_button = ttk.Button(
                self.close_theme_frame, text=_("NO"), command=on_close_theme_frame_no
            )
            no_button.grid(row=1, column=1)

            def on_close_theme_frame_ok():
                self.on_file_save_button_press()
                self.close_theme_frame.grab_release()
                self.close_theme_frame.destroy()
                self.logger.debug("Exit Theme Editor...")
                try:
                    sys.exit(0)
                except:
                    os._exit(0)

            ok_button = ttk.Button(
                self.close_theme_frame, text=_("OK"), command=on_close_theme_frame_ok
            )
            ok_button.grid(row=1, column=0)

    def draw_zone(self, x0, y0, x1, y1):
        x = min(self.x0, x1)
        y = min(self.y0, y1)
        width = max(self.x0, x1) - min(x0, x1)
        height = max(self.y0, y1) - min(y0, y1)
        if width > 0 and height > 0:
            self.label_zone.place(
                x=x + self.RGB_LED_MARGIN,
                y=y + self.RGB_LED_MARGIN,
                width=width,
                height=height,
            )
        else:
            self.label_zone.place_forget()

    def on_button1_press(self, event):
        self.x0, self.y0 = event.x, event.y
        self.label_zone.place_forget()

    def on_button1_press_and_drag(self, event):
        x1, y1 = event.x, event.y

        # Do not draw zone outside of theme preview
        if x1 < 0:
            x1 = 0
        elif x1 >= display.lcd.get_width():
            x1 = display.lcd.get_width() - 1
        if y1 < 0:
            y1 = 0
        elif y1 >= display.lcd.get_height():
            y1 = display.lcd.get_height() - 1

        self.label_coord.config(
            text=_("Drawing zone from [{},{}] to [{},{}]").format(
                self.x0, self.y0, x1, y1
            )
        )
        self.draw_zone(self.x0, self.y0, x1, y1)

    def on_button1_release(self, event):
        x1, y1 = event.x, event.y
        if x1 != self.x0 or y1 != self.y0:
            # Do not draw zone outside of theme preview
            if x1 < 0:
                x1 = 0
            elif x1 >= display.lcd.get_width():
                x1 = display.lcd.get_width() - 1
            if y1 < 0:
                y1 = 0
            elif y1 >= display.lcd.get_height():
                y1 = display.lcd.get_height() - 1

            # Display drawn zone and coordinates
            self.draw_zone(self.x0, self.y0, x1, y1)

            # Display relative zone coordinates, to set in theme
            x = min(self.x0, x1)
            y = min(self.y0, y1)
            width = max(self.x0, x1) - min(self.x0, x1)
            height = max(self.y0, y1) - min(self.y0, y1)
            self.label_coord.config(
                text=_("Zone: X={}, Y={}, width={} height={}").format(
                    x, y, width, height
                )
            )
        else:
            # Display click coordinates
            self.label_coord.config(
                text=_("X={}, Y={} (click and drag to draw a zone)").format(
                    self.x0, self.y0, abs(x1 - self.x0), abs(y1 - self.y0)
                )
            )

    def on_zone_click(self, event):
        self.label_zone.place_forget()


if __name__ == "__main__":
    lang, encoding = locale.getlocale()
    print(f"Language: {lang}, Encoding: {encoding}")
    localedir = os.path.join(
        os.path.dirname(__file__), "res\\language\\theme-editor"
    )  # 替换为你的.mo文件所在的目录
    if encoding == "936":
        language = "zh"
        domain = "zh"
    else:
        language = "en"
        domain = "en"
    lang = gettext.translation(domain, localedir, languages=[language], fallback=True)
    lang.install(domain)
    _ = lang.gettext

    te = theme_editor()
