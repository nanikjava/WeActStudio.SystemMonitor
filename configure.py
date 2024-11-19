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

# This file is the system monitor configuration GUI

import os
import subprocess
import sys
import webbrowser
import traceback
import shutil

sys.path.append(os.path.dirname(__file__))
MIN_PYTHON = (3, 8)
if sys.version_info < MIN_PYTHON:
    print("[ERROR] Python %s.%s or later is required." % MIN_PYTHON)
    try:
        sys.exit(0)
    except:
        os._exit(0)

try:
    import tkinter.ttk as ttk
    import tkinter
    from tkinter import messagebox
    from PIL import ImageTk
    from pathlib import Path
except:
    try:
        sys.exit(0)
    except:
        os._exit(0)

try:
    import platform
    import psutil
    import ruamel.yaml
    import sv_ttk
    from PIL import Image
    from serial.tools.list_ports import comports
    from tktooltip import ToolTip

except:
    try:
        sys.exit(0)
    except:
        os._exit(0)

# Loading Language
import locale,gettext
lang, encoding = locale.getlocale()
print(f"Language: {lang}, Encoding: {encoding}")
localedir = os.path.join(
    os.path.dirname(__file__), "res\\language\\configure"
) 
if lang.startswith("Chinese"):
    language = "zh"
    domain = "zh"
else:
    language = "en"
    domain = "en"
lang = gettext.translation(domain, localedir, languages=[language], fallback=True)
lang.install(domain)
_ = lang.gettext

import library.utils as utils
import time
LOCKFILE = os.path.join(os.path.dirname(__file__), os.path.basename(__file__)+".lock")
if utils.app_is_running(LOCKFILE):
    print("Error: Another instance of the program is already running.")
    utils.show_messagebox("Error: Another instance of the program is already running.",_("WeAct Studio System Monitor Configuration"),3000)
    time.sleep(3)
    try:
        sys.exit(0)
    except:
        os._exit(0)
else:
    utils.app_set_running(LOCKFILE)

def app_exit():
    global LOCKFILE
    utils.app_end_running(LOCKFILE)
    try:
        sys.exit(0)
    except:
        os._exit(0)

from library.sensors.sensors_python import sensors_fans, is_cpu_fan
from library.lcd.lcd_comm import Orientation

WEACT_A_MODEL = "WeAct Studio Display FS V1"
SIMULATED_A_MODEL = "Simulated 320x480"
SIMULATED_B_MODEL = "Simulated 480x800"

SIZE_1 = "320x480"
SIZE_2 = "480x800"

size_list = (SIZE_1, SIZE_2)
orientation_list = (_("portrait"), _("landscape"))

# Maps between config.yaml values and GUI description
revision_to_model_map = {
    "A_320x480": WEACT_A_MODEL,
    "SIMU_320x480": SIMULATED_A_MODEL,
    "SIMU_480x800": SIMULATED_B_MODEL,
}

model_to_revision_map = {
    WEACT_A_MODEL: "A_320x480",
    SIMULATED_A_MODEL: "SIMU_320x480",
    SIMULATED_B_MODEL: "SIMU_480x800",
}

model_to_size_map = {
    WEACT_A_MODEL: SIZE_1,
    SIMULATED_A_MODEL: SIZE_1,
    SIMULATED_B_MODEL: SIZE_2,
}

hw_lib_map = {
    "AUTO": _("Automatic"),
    "LHM": "LibreHardwareMonitor",
    "PYTHON": "Python libraries",
    "STUB": _("Fake random data"),
    "STATIC": _("Fake static data"),
}
reverse_map = {False: _("Classic"), True: _("Reverse")}

themes_dir = "res/themes"


def get_theme_data(name: str):
    dir = os.path.join(themes_dir, name)
    # checking if it is a directory
    if os.path.isdir(dir):
        # Check if a theme.yaml file exists
        theme = os.path.join(dir, "theme.yaml")
        if os.path.isfile(theme):
            # Get display size from theme.yaml
            with open(theme, "rt", encoding="utf8") as stream:
                theme_data, ind, bsi = ruamel.yaml.util.load_yaml_guess_indent(stream)
                return theme_data
    return None


def get_themes(size: str):
    themes = []
    for filename in os.listdir(themes_dir):
        theme_data = get_theme_data(filename)
        if theme_data and theme_data["display"].get("DISPLAY_SIZE", SIZE_1) == size:
            themes.append(filename)
    return sorted(themes, key=str.casefold)


def get_theme_size(name: str) -> str:
    theme_data = get_theme_data(name)
    return theme_data["display"].get("DISPLAY_SIZE", SIZE_1)


def get_com_ports():
    com_ports_names = [
        _("Automatic detection")
    ]  # Add manual entry on top for automatic detection
    com_ports = comports()
    for com_port in com_ports:
        com_ports_names.append(com_port.name)
    return com_ports_names


def get_net_if():
    if_list = list(psutil.net_if_addrs().keys())
    if_list.insert(
        0, "None"
    )  # Add manual entry on top for unavailable/not selected interface
    return if_list


def get_fans():
    fan_list = list()
    auto_detected_cpu_fan = "None"
    for name, entries in sensors_fans().items():
        for entry in entries:
            fan_list.append(
                "%s/%s (%d%% - %d RPM)"
                % (name, entry.label, entry.percent, entry.current)
            )
            if (
                is_cpu_fan(entry.label) or is_cpu_fan(name)
            ) and auto_detected_cpu_fan == "None":
                auto_detected_cpu_fan = "Auto-detected: %s/%s" % (name, entry.label)

    fan_list.insert(
        0, auto_detected_cpu_fan
    )  # Add manual entry on top if auto-detection succeeded
    return fan_list


class ConfigWindow:
    def __init__(self):

        self.theme_editor_process = None
        self.display_other_config_process = None

        self.window = tkinter.Tk()
        self.window.title(_("WeAct Studio System Monitor Configuration"))
        self.window.geometry("770x600")

        # When window gets focus again, reload theme preview in case it has been updated by theme editor
        self.window.bind("<FocusIn>", self.on_theme_change)
        self.window.after(0, self.on_fan_speed_update)
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.iconphoto(True, tkinter.PhotoImage(file="res/icons/logo.png"))
        # Make TK look better with Sun Valley ttk theme
        # sv_ttk.set_theme("light")

        self.theme_preview_img = None
        self.theme_preview = ttk.Label(self.window)
        self.theme_preview.place(x=10, y=10)

        self.theme_author = ttk.Label(self.window)

        sysmon_label = ttk.Label(
            self.window, text=_("Display configuration"), font=("Arial", 13, "bold")
        )
        sysmon_label.place(x=320, y=5)

        self.model_label = ttk.Label(self.window, text=_("Screen model"))
        self.model_label.place(x=320, y=35)
        self.model_cb = ttk.Combobox(
            self.window,
            values=list(dict.fromkeys((revision_to_model_map.values()))),
            state="readonly",
        )
        self.model_cb.bind("<<ComboboxSelected>>", self.on_model_change)
        self.model_cb.place(x=500, y=30, width=250)

        self.size_label = ttk.Label(self.window, text=_("Screen size"))
        self.size_label.place(x=320, y=75)
        self.size_select_label = ttk.Label(
            self.window,
            text=model_to_size_map[WEACT_A_MODEL],
            font=("Arial", 12, "bold"),
        )
        self.size_select_label.place(x=500, y=72, width=250)

        self.com_label = ttk.Label(self.window, text=_("COM port"))
        self.com_label.place(x=320, y=115)
        self.com_cb = ttk.Combobox(
            self.window, values=get_com_ports(), state="readonly"
        )
        self.com_cb.place(x=500, y=112, width=150)
        self.com_refresh_button = ttk.Button(
            self.window, text=_("Refresh"), command=lambda: self.on_com_refresh_button()
        )
        self.com_refresh_button.place(x=660, y=110, width=90)

        self.orient_label = ttk.Label(self.window, text=_("Orientation"))
        self.orient_label.place(x=320, y=155)
        self.orient_cb = ttk.Combobox(
            self.window, values=list(reverse_map.values()), state="readonly"
        )
        self.orient_cb.place(x=500, y=150, width=250)

        self.brightness_string = tkinter.StringVar()
        self.brightness_label = ttk.Label(self.window, text=_("Brightness"))
        self.brightness_label.place(x=320, y=195)
        self.brightness_slider = ttk.Scale(
            self.window,
            from_=0,
            to=100,
            orient=tkinter.HORIZONTAL,
            command=self.on_brightness_change,
        )
        self.brightness_slider.place(x=550, y=195, width=180)
        self.brightness_val_label = ttk.Label(
            self.window, textvariable=self.brightness_string
        )
        self.brightness_val_label.place(x=500, y=195)

        self.live_display_bool_var = tkinter.BooleanVar()
        self.live_display_bool_var.set(False)
        self.live_display_checkbox = ttk.Checkbutton(
            self.window,
            text=_("Theme Preview, Auto Save"),
            variable=self.live_display_bool_var,
        )
        self.live_display_checkbox.place(x=500, y=228)

        self.other_setting_button = ttk.Button(
            self.window,
            text=_("Other Config"),
            command=lambda: self.on_display_other_config_click(),
        )
        self.other_setting_button.place(x=320, y=225)

        self.free_off_bool_var = tkinter.BooleanVar()
        self.free_off_bool_var.set(False)
        self.free_off_checkbox = ttk.Checkbutton(
            self.window,
            text=_("Free Off(3 min)"),
            variable=self.free_off_bool_var,
        )
        self.free_off_checkbox.place(x=500, y=258)

        # System Monitor Configuration
        sysmon_label = ttk.Label(
            self.window, text=_("System Monitor Configuration"), font=("Arial", 13, "bold")
        )
        sysmon_label.place(x=320, y=295)

        self.theme_label = ttk.Label(self.window, text=_("Theme"))
        self.theme_label.place(x=320, y=330)
        self.theme_cb = ttk.Combobox(self.window, state="readonly")
        self.theme_cb.place(x=400, y=325, width=250)
        self.theme_cb.bind("<<ComboboxSelected>>", self.on_theme_change)
        self.theme_refresh_button = ttk.Button(
            self.window, text=_("Refresh"), command=lambda: self.on_model_change()
        )
        self.theme_refresh_button.place(x=660, y=325, width=90)

        self.hwlib_label = ttk.Label(self.window, text=_("Hardware monitoring"))
        self.hwlib_label.place(x=320, y=370)
        if sys.platform != "win32":
            del hw_lib_map["LHM"]  # LHM is for Windows platforms only
        self.hwlib_cb = ttk.Combobox(
            self.window, values=list(hw_lib_map.values()), state="readonly"
        )
        self.hwlib_cb.place(x=500, y=365, width=250)
        self.hwlib_cb.bind("<<ComboboxSelected>>", self.on_hwlib_change)

        self.eth_label = ttk.Label(self.window, text=_("Ethernet interface"))
        self.eth_label.place(x=320, y=410)
        self.eth_cb = ttk.Combobox(self.window, values=get_net_if(), state="readonly")
        self.eth_cb.place(x=500, y=405, width=250)

        self.wl_label = ttk.Label(self.window, text=_("Wi-Fi interface"))
        self.wl_label.place(x=320, y=450)
        self.wl_cb = ttk.Combobox(self.window, values=get_net_if(), state="readonly")
        self.wl_cb.place(x=500, y=445, width=250)

        # For Windows platform only
        self.lhm_admin_warning = ttk.Label(
            self.window,
            text="❌ " + _("Restart as admin. or select another Hardware monitoring"),
            foreground="#f00",
        )
        # For platform != Windows
        self.cpu_fan_label = ttk.Label(self.window, text="CPU fan (？)")
        self.cpu_fan_label.config(foreground="#a3a3ff", cursor="hand2")
        self.cpu_fan_cb = ttk.Combobox(self.window, values=get_fans(), state="readonly")

        self.tooltip = ToolTip(
            self.cpu_fan_label,
            msg='If "None" is selected, CPU fan was not auto-detected.\n'
            "Manually select your CPU fan from the list.\n\n"
            "Fans missing from the list? Install lm-sensors package\n"
            "and run 'sudo sensors-detect' command, then reboot.",
        )

        self.edit_theme_btn = ttk.Button(
            self.window, text=_("Edit theme"), command=lambda: self.on_theme_editor_click()
        )
        self.edit_theme_btn.place(x=310, y=540, height=50, width=130)

        self.save_btn = ttk.Button(
            self.window, text=_("Save settings"), command=lambda: self.on_save_click()
        )
        self.save_btn.place(x=450, y=540, height=50, width=130)

        self.save_run_btn = ttk.Button(
            self.window, text=_("Save and run"), command=lambda: self.on_saverun_click()
        )
        self.save_run_btn.place(x=590, y=540, height=50, width=130)

        self.new_theme_btn = ttk.Button(
            self.window,
            text=_("New theme"),
            command=lambda: self.on_new_theme_editor_click(),
        )
        self.new_theme_btn.place(x=170, y=540, height=50, width=130)

        self.delete_theme_btn = ttk.Button(
            self.window,
            text=_("Delete theme"),
            command=lambda: self.on_delete_theme_click(),
        )
        self.delete_theme_btn.place(x=30, y=540, height=50, width=130)

        self.theme_dir_btn = ttk.Button(
            self.window,
            text=_("Theme dir"),
            command=lambda: self.on_theme_dir_click(),
        )
        self.theme_dir_btn.place(x=30, y=480, height=50, width=130)

        self.copy_theme_btn = ttk.Button(
            self.window,
            text=_("Copy theme"),
            command=lambda: self.on_copy_theme_editor_click(),
        )
        self.copy_theme_btn.place(x=170, y=480, height=50, width=130)

        if platform.system() == "Windows":
            import ctypes
            from library import schedule_service

            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if is_admin == True:
                self.schedule_task_name = "WeAct Studio System Monitor"
                self.schedule_task_path = (
                    '"' + os.path.dirname(__file__) + r"\System Monitor Main.bat" + '"'
                )
                schedule_task_exist, schedule_task_path_get = (
                    schedule_service.task_exists(self.schedule_task_name)
                )
                if (
                    schedule_task_exist == True
                    and schedule_task_path_get != self.schedule_task_path
                ):
                    print(f"error schedule task path {schedule_task_path_get}")
                    schedule_service.delete_task(self.schedule_task_name)
                    schedule_task_exist = False
                self.bootstrap_label = ttk.Label(self.window, text=_("Bootstrap"))
                self.bootstrap_label.place(x=320, y=490)
                self.bootstrap_checkbutton_var = tkinter.IntVar()
                self.bootstrap_checkbutton_var.set(schedule_task_exist)
                self.bootstrap_checkbutton = ttk.Checkbutton(
                    self.window,
                    text=_("Enable"),
                    variable=self.bootstrap_checkbutton_var,
                    command=self.on_bootstrap_checkbutton_toggle,
                )
                self.bootstrap_checkbutton.place(x=500, y=485)

        self.config = None
        self.load_config_values()

        self.display_init = False
        self.display_setting_change = True
        self.display_brightness_change = True
        self.display_step = 0
        self.display_orientation_last = reverse_map[False]
        self.display_brightness_last = int(self.brightness_slider.get())
        self.theme_select_last = self.theme_cb.get()
        self.theme_setting_change = True
        self.window_after_time = 1000

    def run(self):
        self.window_refresh()
        self.window.mainloop()

    def on_closing(self):
        self.on_closing_confirm()

    def on_closing_confirm(self):
        self.closing_confirm_frame = tkinter.Toplevel(self.window)
        self.closing_confirm_frame.title(_("Close Confirm"))
        main_window_x = self.window.winfo_x()
        main_window_y = self.window.winfo_y()
        main_window_width = self.window.winfo_width()
        main_window_height = self.window.winfo_height()
        width = 300
        height = 100
        x = main_window_x + (main_window_width // 2) - (width // 2)
        y = main_window_y + (main_window_height // 2) - (height // 2)
        self.closing_confirm_frame.geometry(f"{width}x{height}+{x}+{y}")

        def on_closing_confirm_frame_closing():
            self.closing_confirm_frame.grab_release()
            self.closing_confirm_frame.destroy()

        self.closing_confirm_frame.protocol(
            "WM_DELETE_WINDOW", on_closing_confirm_frame_closing
        )
        self.closing_confirm_frame.resizable(False, False)
        self.closing_confirm_frame.grab_set()

        self.closing_confirm_label = ttk.Label(
            self.closing_confirm_frame, text=_("Do you want to run theme?")
        )
        self.closing_confirm_label.pack(
            side=tkinter.TOP, padx=5, pady=10, anchor=tkinter.W
        )

        def on_closing_confirm_frame_no():
            if self.display_init == True:
                self.live_display_checkbox.state(["disabled"])
                self.display_off()
                self.display_init = False
            print("Exiting System Monitor Configuration...")
            self.closing_confirm_frame.grab_release()
            self.closing_confirm_frame.destroy()
            self.window.destroy()
            app_exit()

        cancel_button = ttk.Button(
            self.closing_confirm_frame, text=_("NO"), command=on_closing_confirm_frame_no
        )
        cancel_button.pack(side=tkinter.RIGHT, padx=5, pady=5)
        self.closing_confirm_frame.focus_force()

        def on_closing_confirm_frame_ok():
            if self.display_init == True:
                self.live_display_checkbox.state(["disabled"])
                self.display_off()
                self.display_init = False
            print("Exiting System Monitor Configuration...")
            self.closing_confirm_frame.grab_release()
            self.closing_confirm_frame.destroy()
            subprocess.Popen(("python", os.path.join(os.getcwd(), "main.py")), shell=True)
            self.window.destroy()
            app_exit()

        ok_button = ttk.Button(
            self.closing_confirm_frame, text=_("OK"), command=on_closing_confirm_frame_ok
        )
        ok_button.pack(side=tkinter.RIGHT, padx=5, pady=5)
        ok_button['state'] = self.save_run_btn['state']

    def display_off(self):
        print('display.turn_off')
        try:
            self.display.turn_off()
            if self.scheduler.STOPPING != True:
                # Do not stop the program now in case data transmission was in progress
                # Instead, ask the scheduler to empty the action queue before stopping
                self.scheduler.STOPPING = True

                # Allow 5 seconds max. delay in case scheduler is not responding
                wait_time = 5

                while not self.scheduler.is_queue_empty() and wait_time > 0:
                    import time
                    time.sleep(0.1)
                    wait_time = wait_time - 0.1
            print('display.lcd.lcd_serial.close')
            self.display.lcd.lcd_serial.close()
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror(_("Error"), _("error: ") + f'{e}')

    def window_refresh(self):
        if self.live_display_bool_var.get() == True:
            if self.theme_editor_process != None:
                if self.theme_editor_process.poll() == None:
                    messagebox.showerror(_("Error"), _("theme editor is running !"))
                    self.live_display_bool_var.set(False)
                    self.window.after(self.window_after_time, self.window_refresh)
                    return
            self.model_cb['state'] = "disabled"
            self.com_cb['state'] = "disabled"
            self.com_refresh_button['state'] = "disabled"
            # check setting change
            if self.display_orientation_last != self.orient_cb.get():
                self.display_orientation_last = self.orient_cb.get()
                self.display_setting_change = True
                self.theme_setting_change = True
            if self.display_brightness_last != int(self.brightness_slider.get()):
                self.display_brightness_last = int(self.brightness_slider.get())
                self.display_setting_change = True
                self.display_brightness_change = True
            if self.theme_select_last != self.theme_cb.get():
                self.theme_select_last = self.theme_cb.get()
                self.display_setting_change = True
                self.theme_setting_change = True

            if self.theme_setting_change == True or self.display_setting_change == True:
                self.save_config_values()
            # init display
            if self.display_init == False:
                try:
                    import library.scheduler as scheduler
                    from library.display import display

                    self.scheduler = scheduler
                    self.display = display
                    print("Open Display LCD Serial")
                    self.on_com_refresh_button()
                    if self.com_cb.current() == 0:
                        self.display.lcd.com_port = "AUTO"
                    else:
                        self.display.lcd.com_port = self.com_cb.get()
                    self.display.lcd.openSerial()
                        
                    print("Initialize display")
                    self.display.initialize_display()
                    print("Enable QueueHandler")
                    self.scheduler.STOPPING = False
                    self.scheduler.QueueHandler()
                    print("display_init Ok")
                    self.display_init = True
                except Exception as e:
                    traceback.print_exc()
                    messagebox.showerror(_("Error"), _("Error: ") + f'{e}')
                    self.live_display_bool_var.set(False)
                    self.display_init = True
            else:
                # display comport is open
                if self.display.lcd.lcd_serial != None:
                    if self.display.lcd.lcd_serial.is_open == False:
                        self.live_display_bool_var.set(False)
                        messagebox.showerror(_("Error"), _("error: COM Port is closed"))
            # display something
            if self.display_setting_change == True:
                try:
                    if self.display_step == 0:
                        self.display_step = 1
                        self.window_after_time = 200
                    elif self.display_step == 1:
                        if self.display_brightness_change == True:
                            print(f"display.lcd.SetBrightness {int(self.brightness_slider.get())}")
                            self.display.lcd.SetBrightness(
                                int(self.brightness_slider.get())
                            )
                            self.display_brightness_change = False
                        if self.theme_setting_change == True:
                            try:
                                theme_preview = Image.open(
                                    "res/themes/" + self.theme_cb.get() + "/preview.png"
                                )
                                print("Show preview.png")
                            except:
                                theme_preview = Image.open("res/configs/no-preview.png")
                                print("Show no-preview.png")
                            theme_data = get_theme_data(self.theme_cb.get())
                            print("display.lcd.SetOrientation")
                            d_o = theme_data.get("display")
                            if d_o["DISPLAY_ORIENTATION"] == "portrait":
                                if self.orient_cb.get() == reverse_map[True]:
                                    self.display.lcd.SetOrientation(
                                        Orientation.REVERSE_PORTRAIT
                                    )
                                else:
                                    self.display.lcd.SetOrientation(
                                        Orientation.PORTRAIT
                                    )
                            else:
                                if self.orient_cb.get() == reverse_map[True]:
                                    self.display.lcd.SetOrientation(
                                        Orientation.REVERSE_LANDSCAPE
                                    )
                                else:
                                    self.display.lcd.SetOrientation(
                                        Orientation.LANDSCAPE
                                    )
                            theme_preview_d = theme_preview.resize(
                                (
                                    self.display.lcd.get_width(),
                                    self.display.lcd.get_height(),
                                )
                            )
                            print("display.lcd.DisplayPILImage")
                            self.display.lcd.DisplayPILImage(
                                theme_preview_d,
                                image_width=theme_preview_d.width,
                                image_height=theme_preview_d.height,
                            )
                            self.theme_setting_change = False

                        self.display_setting_change = False
                except Exception as e:
                    traceback.print_exc()
                    messagebox.showerror(_("Error"), _("error: ") + f'{e}')
                    self.live_display_bool_var.set(False)
        else:
            self.model_cb['state'] = "readonly"
            self.com_cb['state'] = "readonly"
            self.com_refresh_button['state'] = "normal"
            if self.display_init == True:
                self.display_off()
                self.display_init = False
            self.display_setting_change = True
            self.theme_setting_change = True
            self.display_brightness_change = True
            self.display_orientation_last = -1
            self.display_step = 0
            self.window_after_time = 1000
        self.window.after(self.window_after_time, self.window_refresh)

    def load_theme_preview(self):
        if self.theme_cb.get() != "":
            try:
                theme_preview = Image.open(
                    "res/themes/" + self.theme_cb.get() + "/preview.png"
                )
            except:
                theme_preview = Image.open("res/configs/no-preview.png")
            finally:
                if theme_preview.width > theme_preview.height:
                    theme_preview = theme_preview.resize(
                        (300, 200), Image.Resampling.LANCZOS
                    )
                else:
                    theme_preview = theme_preview.resize(
                        (280, 420), Image.Resampling.LANCZOS
                    )
                self.theme_preview_img = ImageTk.PhotoImage(theme_preview)
                self.theme_preview.config(image=self.theme_preview_img)

                theme_data = get_theme_data(self.theme_cb.get())
                author_name = theme_data.get("author", "unknown")
                self.theme_author.config(text=_("Author: ") + author_name)
                if author_name.startswith("@"):
                    self.theme_author.config(foreground="#a3a3ff", cursor="hand2")
                    self.theme_author.bind(
                        "<Button-1>",
                        lambda e: webbrowser.open_new_tab(
                            "https://github.com/" + author_name[1:]
                        ),
                    )
                else:
                    self.theme_author.config(foreground="#a3a3a3", cursor="")
                    self.theme_author.unbind("<Button-1>")
                self.theme_author.place(x=10, y=self.theme_preview_img.height() + 15)

    def load_config_values(self):
        try:
            with open("config.yaml", "rt", encoding="utf8") as stream:
                self.config, ind, bsi = ruamel.yaml.util.load_yaml_guess_indent(stream)
        except:
            self.config = {}

        # Check if theme is valid
        config = self.config.get("config",None)
        if config is None:
            print("Config not found!!")
            self.config["config"] = {}
            self.config["config"]["THEME"] = get_themes(SIZE_1)[0]
        else:
            theme = config.get("THEME",None)
            if theme is None:
                # Theme from config.yaml is not valid: use first theme available default size 320x480
                self.config["config"]["THEME"] = get_themes(SIZE_1)[0]
        
        try:
            self.theme_cb.set(config.get("THEME",None))
        except:
            self.theme_cb.set("")

        self.load_theme_preview()

        try:
            self.hwlib_cb.set(hw_lib_map[config.get("HW_SENSORS","LHM")])
        except:
            self.hwlib_cb.current(0)

        try:
            if config.get("ETH","") == "":
                self.eth_cb.current(0)
            else:
                self.eth_cb.set(self.config["config"]["ETH"])
        except:
            self.eth_cb.current(0)

        try:
            if config.get("WLO","") == "":
                self.wl_cb.current(0)
            else:
                self.wl_cb.set(self.config["config"]["WLO"])
        except:
            self.wl_cb.current(0)

        try:
            if config.get("COM_PORT","AUTO") == "AUTO":
                self.com_cb.current(0)
            else:
                self.com_cb.set(self.config["config"]["COM_PORT"])
        except:
            self.com_cb.current(0)

        # Guess display size from theme in the configuration
        size = get_theme_size(self.config["config"]["THEME"])
        try:
            self.size_select_label["text"] = size
        except:
            self.size_select_label["text"] = SIZE_1

        # Guess model from revision and size
        display = self.config.get("display",None)
        if display is None:
            print("display config not found!!")
            self.config["display"] = {}
        try:
            revision = self.config["display"]["REVISION"]
            self.model_cb.set(revision_to_model_map[revision])
        except:
            self.model_cb.current(0)

        try:
            self.orient_cb.set(reverse_map[self.config["display"]["DISPLAY_REVERSE"]])
        except:
            self.orient_cb.current(0)

        try:
            self.brightness_slider.set(int(self.config["display"]["BRIGHTNESS"]))
        except:
            self.brightness_slider.set(50)

        try:
            if self.config["config"]["CPU_FAN"] == "AUTO":
                self.cpu_fan_cb.current(0)
            else:
                self.cpu_fan_cb.set(self.config["config"]["CPU_FAN"])
        except:
            self.cpu_fan_cb.current(0)

        try:
            self.free_off_bool_var.set(self.config["display"].get("FREE_OFF",False))
        except:
            self.free_off_bool_var.set(False)

        # Reload content on screen
        self.on_model_change()
        self.on_theme_change()
        self.on_brightness_change()
        self.on_hwlib_change()

    def save_config_values(self):
        self.config["config"]["THEME"] = self.theme_cb.get()
        self.config["config"]["HW_SENSORS"] = [
            k for k, v in hw_lib_map.items() if v == self.hwlib_cb.get()
        ][0]
        if self.eth_cb.current() == 0:
            self.config["config"]["ETH"] = ""
        else:
            self.config["config"]["ETH"] = self.eth_cb.get()
        if self.wl_cb.current() == 0:
            self.config["config"]["WLO"] = ""
        else:
            self.config["config"]["WLO"] = self.wl_cb.get()
        if self.com_cb.current() == 0:
            self.config["config"]["COM_PORT"] = "AUTO"
        else:
            self.config["config"]["COM_PORT"] = self.com_cb.get()
        if self.cpu_fan_cb.current() == 0:
            self.config["config"]["CPU_FAN"] = "AUTO"
        else:
            self.config["config"]["CPU_FAN"] = self.cpu_fan_cb.get().split(" ")[0]
        self.config["display"]["REVISION"] = model_to_revision_map[self.model_cb.get()]
        self.config["display"]["DISPLAY_REVERSE"] = [
            k for k, v in reverse_map.items() if v == self.orient_cb.get()
        ][0]
        self.config["display"]["BRIGHTNESS"] = int(self.brightness_slider.get())
        self.config["display"]["FREE_OFF"] = self.free_off_bool_var.get()
        
        with open("config.yaml", "w", encoding="utf-8") as file:
            ruamel.yaml.YAML().dump(self.config, file)

    def on_theme_change(self, e=None):
        self.load_theme_preview()

    def on_new_theme_editor_click(self):
        if self.theme_editor_process != None:
            if self.theme_editor_process.poll() == None:
                messagebox.showerror(_("Error"), _("theme editor is running !"))
                return
        self.new_theme_editor = tkinter.Toplevel(self.window)
        self.new_theme_editor.title(_("New theme"))
        main_window_x = self.window.winfo_x()
        main_window_y = self.window.winfo_y()
        main_window_width = self.window.winfo_width()
        main_window_height = self.window.winfo_height()
        width = 300
        height = 210
        x = main_window_x + (main_window_width // 2) - (width // 2)
        y = main_window_y + (main_window_height // 2) - (height // 2)
        self.new_theme_editor.geometry(f"{width}x{height}+{x}+{y}")
        self.new_theme_editor.protocol(
            "WM_DELETE_WINDOW", self.on_new_theme_editor_closing
        )
        self.new_theme_editor.resizable(False, False)
        self.new_theme_editor.grab_set()
        self.new_theme_editor_label = ttk.Label(self.new_theme_editor, text=_("Name"))
        self.new_theme_editor_label.pack(
            side=tkinter.TOP, padx=10, pady=10, anchor=tkinter.W
        )

        self.new_theme_editor_entry = ttk.Entry(self.new_theme_editor)
        self.new_theme_editor_entry.pack(fill=tkinter.X, expand=True, padx=10)
        self.new_theme_editor_entry.bind(
            "<KeyRelease>", self.new_theme_editor_entry_change
        )

        self.new_theme_editor_orientation_label = ttk.Label(
            self.new_theme_editor, text=_("Orientation")
        )
        self.new_theme_editor_orientation_label.pack(
            side=tkinter.TOP, padx=10, pady=10, anchor=tkinter.W
        )
        self.new_theme_editor_orientation_combobox = ttk.Combobox(
            self.new_theme_editor, values=orientation_list, state="readonly"
        )
        self.new_theme_editor_orientation_combobox.current(0)
        self.new_theme_editor_orientation_combobox.pack(
            fill=tkinter.X, expand=True, padx=10
        )

        cancel_button = ttk.Button(
            self.new_theme_editor,
            text=_("Cancel"),
            command=self.on_new_theme_editor_closing,
        )
        cancel_button.pack(side=tkinter.RIGHT, padx=10, pady=10)

        self.new_theme_editor_ok_button = ttk.Button(
            self.new_theme_editor, text="OK", command=self.on_new_theme_editor_button_ok
        )
        self.new_theme_editor_ok_button.pack(side=tkinter.RIGHT, padx=5, pady=10)
        self.new_theme_editor_ok_button.state(["disabled"])
        self.new_theme_editor.focus_force()

    def on_new_theme_editor_closing(self):
        self.new_theme_editor.grab_release()
        self.new_theme_editor.destroy()

    def list_theme_dir(self):
        current_directory = "res/themes/"
        entries = os.listdir(current_directory)
        folders = [
            entry
            for entry in entries
            if os.path.isdir(os.path.join(current_directory, entry))
        ]
        return folders

    def validate_entry(self, P):
        import re

        pattern = r"^[a-zA-Z0-9_\- .]+$"
        if re.match(pattern, P):
            return True
        else:
            return False

    def new_theme_editor_entry_change(self, event=None):
        content = self.new_theme_editor_entry.get()
        if self.validate_entry(content):
            if content in self.list_theme_dir():
                self.new_theme_editor_label["text"] = _("Theme name already exists.")
                self.new_theme_editor_label["foreground"] = "red"
                self.new_theme_editor_ok_button.state(["disabled"])
            else:
                self.new_theme_editor_ok_button.state(["!disabled"])
                self.new_theme_editor_label["text"] = _("Name")
                self.new_theme_editor_label["foreground"] = "black"
        else:
            self.new_theme_editor_ok_button.state(["disabled"])
            self.new_theme_editor_label["text"] = _("Error input: ") + r"^[a-zA-Z0-9_\- ]+$"
            self.new_theme_editor_label["foreground"] = "red"
            pass

    def on_new_theme_editor_button_ok(self):
        current_directory = "res/themes/"
        configs_directory = "res/configs/"
        theme_name = self.new_theme_editor_entry.get()
        new_dir = current_directory + theme_name + "/"
        try:
            os.mkdir(new_dir)
            print(f"Directory '{new_dir}' created")
            # copy yaml
            if model_to_size_map[self.model_cb.get()] == SIZE_1:
                if (
                    self.new_theme_editor_orientation_combobox.get()
                    == orientation_list[0]
                ):
                    template_name = "theme_template_320x480.yaml"
                else:
                    template_name = "theme_template_480x320.yaml"
            else:
                if (
                    self.new_theme_editor_orientation_combobox.get()
                    == orientation_list[0]
                ):
                    template_name = "theme_template_480x800.yaml"
                else:
                    template_name = "theme_template_800x480.yaml"
            dst_name = "theme.yaml"
            src_file = configs_directory + template_name
            dst_file = new_dir + dst_name
            try:
                shutil.copy2(src_file, dst_file)
                print(f"File '{src_file}' copy to '{dst_file}'")
            except FileNotFoundError:
                messagebox.showerror(_("Error"), f"Source '{src_file}' no found")
                self.new_theme_editor.destroy()
                return
            except Exception as e:
                messagebox.showerror(_("Error"), f"Error: {e}")
                self.new_theme_editor.destroy()
                return
            # new png
            template_name = "background.png"
            dst_file = new_dir + template_name
            if model_to_size_map[self.model_cb.get()] == SIZE_1:
                if (
                    self.new_theme_editor_orientation_combobox.get()
                    == orientation_list[0]
                ):
                    new_image = Image.new("RGB", (320, 480), "black")
                else:
                    new_image = Image.new("RGB", (480, 320), "black")
            else:
                if (
                    self.new_theme_editor_orientation_combobox.get()
                    == orientation_list[0]
                ):
                    new_image = Image.new("RGB", (480, 800), "black")
                else:
                    new_image = Image.new("RGB", (800, 480), "black")
            new_image.save(dst_file)
            # save theme change
            self.on_model_change()
            self.theme_cb.set(theme_name)
            self.save_config_values()
            self.on_theme_editor_click()
            self.new_theme_editor.destroy()

        except FileExistsError:
            messagebox.showerror(_("Error"), f"Directory '{new_dir}' already exists")
            self.new_theme_editor.destroy()
            return

    def on_delete_theme_click(self):
        if self.theme_editor_process != None:
            if self.theme_editor_process.poll() == None:
                messagebox.showerror(_("Error"), _("theme editor is running !"))
                return
        self.delete_theme_frame = tkinter.Toplevel(self.window)
        self.delete_theme_frame.title(_("Delete theme"))
        main_window_x = self.window.winfo_x()
        main_window_y = self.window.winfo_y()
        main_window_width = self.window.winfo_width()
        main_window_height = self.window.winfo_height()
        width = 350
        height = 120
        x = main_window_x + (main_window_width // 2) - (width // 2)
        y = main_window_y + (main_window_height // 2) - (height // 2)
        self.delete_theme_frame.geometry(f"{width}x{height}+{x}+{y}")

        def on_delete_theme_frame_closing():
            self.delete_theme_frame.grab_release()
            self.delete_theme_frame.destroy()

        self.delete_theme_frame.protocol(
            "WM_DELETE_WINDOW", on_delete_theme_frame_closing
        )
        self.delete_theme_frame.resizable(False, False)
        self.delete_theme_frame.grab_set()

        self.delete_theme_label = ttk.Label(
            self.delete_theme_frame, text=_("Delete theme: ") + f"{self.theme_cb.get()} ?",wraplength = 340
        )
        self.delete_theme_label.pack(
            side=tkinter.TOP, padx=5, pady=10, anchor=tkinter.W
        )

        cancel_button = ttk.Button(
            self.delete_theme_frame, text=_("NO"), command=on_delete_theme_frame_closing
        )
        cancel_button.pack(side=tkinter.RIGHT, padx=5, pady=5)
        self.delete_theme_frame.focus_force()

        def on_delete_theme_frame_ok():
            current_directory = "res/themes/"
            theme_name = self.theme_cb.get()
            delete_dir = current_directory + theme_name + "/"
            try:
                shutil.rmtree(delete_dir)
                print(f"dir {delete_dir} and all of its contents have been deleted")
            except OSError as error:
                print(f"Error deleting directory: {error.strerror}")
            self.on_model_change()
            self.theme_cb.current(0)
            self.save_config_values()
            self.delete_theme_frame.grab_release()
            self.delete_theme_frame.destroy()

        ok_button = ttk.Button(
            self.delete_theme_frame, text=_("OK"), command=on_delete_theme_frame_ok
        )
        ok_button.pack(side=tkinter.RIGHT, padx=5, pady=5)

    def on_theme_editor_click(self):
        if self.theme_editor_process != None:
            if self.theme_editor_process.poll() == None:
                messagebox.showerror(_("Error"), _("theme editor is running !"))
                return
        self.save_config_values()
        sys.path.append(".")
        self.theme_editor_process = subprocess.Popen(
            (
                "python",
                os.path.join(os.getcwd(), "theme-editor.py"),
                self.theme_cb.get(),
            ),
            shell=True,
        )

    def on_theme_dir_click(self):
        dir_path = Path("res/themes/" + self.theme_cb.get())
        if dir_path.exists():
            if platform.system() == "Windows":  
                os.startfile(str(dir_path))  
            elif platform.system() == "Darwin":  # macOS  
                os.system(f'open "{dir_path}"')  
            else:  # Linux  
                os.system(f'xdg-open "{dir_path}"')

    def on_copy_theme_editor_click(self):
        if self.theme_editor_process != None:
            if self.theme_editor_process.poll() == None:
                messagebox.showerror(_("Error"), _("theme editor is running !"))
                return
        self.copy_theme_editor = tkinter.Toplevel(self.window)
        self.copy_theme_editor.title(_("Copy theme"))
        main_window_x = self.window.winfo_x()
        main_window_y = self.window.winfo_y()
        main_window_width = self.window.winfo_width()
        main_window_height = self.window.winfo_height()
        width = 300
        height = 150
        x = main_window_x + (main_window_width // 2) - (width // 2)
        y = main_window_y + (main_window_height // 2) - (height // 2)
        self.copy_theme_editor.geometry(f"{width}x{height}+{x}+{y}")
        self.copy_theme_editor.protocol(
            "WM_DELETE_WINDOW", self.on_copy_theme_editor_closing
        )
        self.copy_theme_editor.resizable(False, False)
        self.copy_theme_editor.grab_set()
        self.copy_theme_editor_label = ttk.Label(self.copy_theme_editor, text=_("Name"))
        self.copy_theme_editor_label.pack(
            side=tkinter.TOP, padx=10, pady=10, anchor=tkinter.W
        )

        self.copy_theme_editor_entry = ttk.Entry(self.copy_theme_editor)
        self.copy_theme_editor_entry.pack(fill=tkinter.X, expand=True, padx=10)
        self.copy_theme_editor_entry.bind(
            "<KeyRelease>", self.copy_theme_editor_entry_change
        )

        cancel_button = ttk.Button(
            self.copy_theme_editor,
            text=_("Cancel"),
            command=self.on_copy_theme_editor_closing,
        )
        cancel_button.pack(side=tkinter.RIGHT, padx=10, pady=10)

        self.copy_theme_editor_ok_button = ttk.Button(
            self.copy_theme_editor, text="OK", command=self.on_copy_theme_editor_button_ok
        )
        self.copy_theme_editor_ok_button.pack(side=tkinter.RIGHT, padx=5, pady=10)
        self.copy_theme_editor_ok_button.state(["disabled"])

        self.copy_theme_editor_entry.insert(0,self.theme_cb.get()+'_0')
        self.copy_theme_editor_entry_change()
        self.copy_theme_editor.focus_force()

    def on_copy_theme_editor_closing(self):
        self.copy_theme_editor.grab_release()
        self.copy_theme_editor.destroy()

    def copy_theme_editor_entry_change(self, event=None):
        content = self.copy_theme_editor_entry.get()
        if self.validate_entry(content):
            if content in self.list_theme_dir():
                self.copy_theme_editor_label["text"] = _("Theme name already exists.")
                self.copy_theme_editor_label["foreground"] = "red"
                self.copy_theme_editor_ok_button.state(["disabled"])
            else:
                self.copy_theme_editor_ok_button.state(["!disabled"])
                self.copy_theme_editor_label["text"] = _("Name")
                self.copy_theme_editor_label["foreground"] = "black"
        else:
            self.copy_theme_editor_ok_button.state(["disabled"])
            self.copy_theme_editor_label["text"] = _("Error input: ") + r"^[a-zA-Z0-9_\- ]+$"
            self.copy_theme_editor_label["foreground"] = "red"
            pass

    def on_copy_theme_editor_button_ok(self):
        current_directory = "res/themes/"
        src_dir = current_directory + self.theme_cb.get()  + "/"
        dst_dir = current_directory + self.copy_theme_editor_entry.get() + "/"
        
        # copy theme
        try:
            shutil.copytree(src_dir, dst_dir)
            print(f"Directory '{src_dir}' copy to '{dst_dir}'")
        except FileNotFoundError:
            messagebox.showerror(_("Error"), f"Source '{src_dir}' no found")
            self.copy_theme_editor.destroy()
            return
        except Exception as e:
            messagebox.showerror(_("Error"), f"Error: {e}")
            self.copy_theme_editor.destroy()
            return
        # save theme change
        self.on_model_change()
        self.theme_cb.set(self.copy_theme_editor_entry.get())
        self.save_config_values()
        self.on_theme_editor_click()
        self.copy_theme_editor.destroy()

    def on_save_click(self):
        if self.theme_editor_process != None:
            if self.theme_editor_process.poll() == None:
                messagebox.showerror(_("Error"), _("theme editor is running !"))
                return
        self.save_config_values()

    def on_display_other_config_click(self):
        if self.display_other_config_process != None:
            if self.display_other_config_process.poll() == None:
                messagebox.showerror(_("Error"), _("display other config is running !"))
                return
            
        if self.display_init == True:
            self.display_off()
            self.display_init = False
            self.live_display_bool_var.set(False)

        self.display_other_config_process = subprocess.Popen(
            ("python", os.path.join(os.getcwd(), "weact_device_setting.py")), shell=True
        )

    def on_saverun_click(self):
        if self.theme_editor_process != None:
            if self.theme_editor_process.poll() == None:
                messagebox.showerror(_("Error"), _("theme editor is running !"))
                return
        if self.display_init == True:
            self.display_off()
            self.display_init = False
            self.live_display_bool_var.set(False)
        self.save_config_values()
        subprocess.Popen(("python", os.path.join(os.getcwd(), "main.py")), shell=True)
        self.window.destroy()

    def on_brightness_change(self, e=None):
        self.brightness_string.set(str(int(self.brightness_slider.get())) + "%")

    def on_model_change(self, e=None):
        model = self.model_cb.get()
        if "Simulated" in model:
            self.com_cb.configure(state="disabled", foreground="#C0C0C0")
            self.orient_cb.configure(state="disabled", foreground="#C0C0C0")
            self.brightness_slider.configure(state="disabled")
            self.brightness_val_label.configure(foreground="#C0C0C0")
        else:
            self.com_cb.configure(state="readonly", foreground="#000")
            self.orient_cb.configure(state="readonly", foreground="#000")
            self.brightness_slider.configure(state="normal")
            self.brightness_val_label.configure(foreground="#000")

            if model == WEACT_A_MODEL:
                self.other_setting_button.configure(state="normal")
            else:
                self.other_setting_button.configure(state="disabled")

        themes = get_themes(model_to_size_map[model])
        self.theme_cb.config(values=themes)

        if not self.theme_cb.get() in themes:
            # The selected theme does not exist anymore / is not allowed for this screen model : select 1st theme avail.
            if len(themes) > 0:
                self.theme_cb.set(themes[0])
            else:
                self.theme_cb.set("")

        self.size_select_label["text"] = model_to_size_map[model]

    def on_hwlib_change(self, e=None):
        hwlib = [k for k, v in hw_lib_map.items() if v == self.hwlib_cb.get()][0]
        if hwlib == "STUB" or hwlib == "STATIC":
            self.eth_cb.configure(state="disabled", foreground="#C0C0C0")
            self.wl_cb.configure(state="disabled", foreground="#C0C0C0")
        else:
            self.eth_cb.configure(state="readonly", foreground="#000")
            self.wl_cb.configure(state="readonly", foreground="#000")

        if sys.platform == "win32":
            import ctypes

            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if (hwlib == "LHM" or hwlib == "AUTO") and not is_admin:
                self.lhm_admin_warning.place(x=320, y=510)
                self.save_run_btn['state'] = "disabled"
                self.live_display_bool_var.set(False)
                self.live_display_checkbox['state'] = "disabled"
            else:
                self.lhm_admin_warning.place_forget()
                self.save_run_btn['state'] = "normal"
                self.live_display_checkbox['state'] = "normal"
        else:
            if hwlib == "PYTHON" or hwlib == "AUTO":
                self.cpu_fan_label.place(x=320, y=520)
                self.cpu_fan_cb.place(x=500, y=510, width=250)
            else:
                self.cpu_fan_label.place_forget()
                self.cpu_fan_cb.place_forget()

        self.theme_setting_change = True
        self.display_setting_change = True

    def on_fan_speed_update(self):
        # Update fan speed periodically
        prev_value = self.cpu_fan_cb.current()  # Save currently selected index
        self.cpu_fan_cb.config(values=get_fans())
        if prev_value != -1:
            self.cpu_fan_cb.current(
                prev_value
            )  # Force select same index to refresh displayed value
        self.window.after(500, self.on_fan_speed_update)

    def on_bootstrap_checkbutton_toggle(self):
        from library import schedule_service

        schedule_task_exist, schedule_task_path_get = schedule_service.task_exists(
            self.schedule_task_name
        )
        if schedule_task_exist == True:
            print(f"schedule service delete task: {self.schedule_task_name}")
            schedule_service.delete_task(self.schedule_task_name)
        v = self.bootstrap_checkbutton_var.get()
        if v == True:
            print(f"schedule service add task: {self.schedule_task_name}")
            schedule_service.create_login_task(
                self.schedule_task_name, self.schedule_task_path
            )

    def on_com_refresh_button(self):
        com_now = self.com_cb.get()
        self.com_cb['values'] = get_com_ports()
        if com_now not in self.com_cb['values']:
            self.com_cb.current(0)

if __name__ == "__main__":
    configurator = ConfigWindow()
    configurator.run()
    app_exit()