import os
import sys
import requests,datetime
import subprocess
from pathlib import Path
import threading
try:
    import tkinter as tk
    import psutil
    import ping3
except:
    print("[ERROR] Python dependencies not installed.")
    try:
        sys.exit(0)
    except:
        os._exit(0)

def show_messagebox(message, title="", delay=3000):
    def create_and_run_messagebox():
        nonlocal root
        root = tk.Tk()
        root.title(title)

        root.resizable(False, False)
        root.attributes('-topmost', True)
        root.attributes("-toolwindow", True)

        label = tk.Label(root, text=message, anchor="w")
        label.grid(row=1, column=0, padx=5, pady=10, sticky="w")
        
        # Center the window on the screen
        root.withdraw()
        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        main_window_width = root.winfo_reqwidth() if root.winfo_reqwidth() > 250 else 250
        main_window_height = root.winfo_reqheight()
        x = (screen_width - main_window_width) // 2
        y = (screen_height - main_window_height) // 2
        root.geometry(f"{main_window_width}x{main_window_height}+{x}+{y}")
        root.deiconify()

        if delay > 0:
            root.after(delay, root.destroy)

        root.mainloop()

    root = None
    messagebox_thread = threading.Thread(target=create_and_run_messagebox)
    messagebox_thread.start()

    while root is None:
        pass

    def close_messagebox():
        if root and root.winfo_exists():
            print("Closing message box...") 
            root.after(0, root.destroy)

    return close_messagebox

def app_is_running(lockfile):
    if not os.path.exists(lockfile):
        return False
        
    try:
        with open(lockfile) as f:
            pid = int(f.read().strip())
            
        p = psutil.Process(pid)
        process_path = Path(p.exe()).parent
        expected_path = Path(__file__).resolve().parent.parent / "Python"
        cmdline = p.cmdline()
        lockfile_name = Path(lockfile).stem
        if cmdline and len(cmdline) > 1 and lockfile_name in cmdline[1] and process_path.samefile(expected_path) and p.is_running():
            print("Process is running")
            return True
            
    except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    try:
        os.remove(lockfile)
    except OSError:
        pass
        
    return False

def app_set_running(lockfile):
    with open(lockfile, 'w') as f:  
        f.write(str(os.getpid()))

def app_end_running(lockfile):
    os.remove(lockfile)

LANGUAGE_MAPPING = {
    "Chinese": "zh",
    "Chinese (Simplified)": "zh",
    "English": "en",
    "Japanese": "ja",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Russian": "ru",
    "Portuguese": "pt",
    "Italian": "it",
    "Korean": "ko",
    "Arabic": "ar",
    "Hindi": "hi",
    "Turkish": "tr",
    "Dutch": "nl",
    "Swedish": "sv",
    "Polish": "pl",
    "Thai": "th",
    "Vietnamese": "vi",
    "Greek": "el",
    "Czech": "cs",
    "Danish": "da",
    "Finnish": "fi",
    "Hebrew": "he",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Norwegian": "no",
    "Romanian": "ro",
    "Slovak": "sk",
    "Ukrainian": "uk"
}

def get_language_code(language_name: str) -> str:
    return LANGUAGE_MAPPING.get(language_name, "Unknown")

import locale, gettext
from library.utils import get_language_code

def set_language(file_path):
    lang, encoding = locale.getlocale()
    lang = lang.split("_")
    _file_name = os.path.basename(file_path)
    file_name = os.path.splitext(_file_name)[0]
    print(f"Language: {lang[0]}, Country: {lang[1]}, Encoding: {encoding}")
    lang_set = get_language_code(lang[0])
    localedir = os.path.join(os.path.dirname(file_path), f"res\\language\\{file_name}")
    available_languages = []
    if os.path.exists(localedir):
        for item in os.listdir(localedir):
            if os.path.isdir(os.path.join(localedir, item)):
                available_languages.append(item)
    if lang_set in available_languages:
        print(f"Use language: {lang_set}")
        language = lang_set
        domain = lang_set
    else:
        print(f"No found language: {lang[0]}, use the default language: English")
        language = "en"
        domain = "en"
    lang_translation = gettext.translation(domain, localedir, languages=[language], fallback=True)
    lang_translation.install(domain)
    return lang_translation.gettext

TEMPERATURE_UNIT_MAP = {"metric": "metric - °C", "imperial": "imperial - °F", "standard": "standard - °K"}

WEATHER_LANG_MAP = {"sq": "Albanian", "af": "Afrikaans", "ar": "Arabic", "az": "Azerbaijani", "eu": "Basque",
                    "be": "Belarusian", "bg": "Bulgarian", "ca": "Catalan", "zh_cn": "Chinese Simplified",
                    "zh_tw": "Chinese Traditional", "hr": "Croatian", "cz": "Czech", "da": "Danish", "nl": "Dutch",
                    "en": "English", "fi": "Finnish", "fr": "French", "gl": "Galician", "de": "German", "el": "Greek",
                    "he": "Hebrew", "hi": "Hindi", "hu": "Hungarian", "is": "Icelandic", "id": "Indonesian",
                    "it": "Italian", "ja": "Japanese", "kr": "Korean", "ku": "Kurmanji (Kurdish)", "la": "Latvian",
                    "lt": "Lithuanian", "mk": "Macedonian", "no": "Norwegian", "fa": "Persian (Farsi)", "pl": "Polish",
                    "pt": "Portuguese", "pt_br": "Português Brasil", "ro": "Romanian", "ru": "Russian", "sr": "Serbian",
                    "sk": "Slovak", "sl": "Slovenian", "sp": "Spanish", "sv": "Swedish", "th": "Thai", "tr": "Turkish",
                    "ua": "Ukrainian", "vi": "Vietnamese", "zu": "Zulu"}

def get_weather(lat, lon, api_key, units, lang):
    WEATHER_UNITS = {'metric': '°C', 'imperial': '°F', 'standard': '°K'}
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang={lang}'
    desc = ''
    result = False
    deg = WEATHER_UNITS.get(units, '°?')
    temp = f"{0}{deg}"
    feel = f"({0}{deg})"
    humidity = f"{0}%"
    now = datetime.datetime.now()
    time = f"@{now.hour:02d}:{now.minute:02d}"
    if api_key:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                temp = f"{data['main']['temp']:.1f}{deg}"
                feel = f"({data['main']['feels_like']:.1f}{deg})"
                desc = data['weather'][0]['description'].capitalize()
                humidity = f"{data['main']['humidity']:.0f}%"
                result = True
            else:
                print(f"Error {response.status_code} fetching OpenWeatherMap API:")
                desc = response.json().get('message')
        except Exception as e:
            print(f"Error fetching OpenWeatherMap API: {str(e)}")
            desc = "Error fetching OpenWeatherMap API"
    else:
        print("No OpenWeatherMap API key provided in config.yaml")
        desc = "No OpenWeatherMap API key"
    return temp, feel, desc, humidity, time, result

def get_ping_delay(host):
    delay = ping3.ping(host)
    if delay is not False:
        return delay
    else:
        return -1
    
class run:
    python_name = 'WeActStudioSystemMonitor'
    current_file = Path(__file__).resolve()
    parent_dir = current_file.parent
    grandparent_dir = parent_dir.parent

    @classmethod
    def get_executable_name(cls):
        if sys.platform == 'win32':
            exec_name = f"{cls.python_name}.exe"
        else:
            exec_name = cls.python_name
        python_cmd = cls.grandparent_dir / "Python" / exec_name
        if not python_cmd.exists():
            print(f"[Info] {python_cmd} not found. Using python.exe")
            python_cmd = cls.grandparent_dir / "Python" / "python.exe"
        return python_cmd
        
    @classmethod
    def main(cls):
        exec_name = cls.get_executable_name()
        main_py = cls.grandparent_dir / "main.py"
        return subprocess.Popen([exec_name, str(main_py)], shell=True)

    @classmethod
    def configure(cls):
        exec_name = cls.get_executable_name()
        configure_py = cls.grandparent_dir / "configure.py"
        return subprocess.Popen([exec_name, str(configure_py)], shell=True)
    
    @classmethod
    def weact_device_setting(cls):
        exec_name = cls.get_executable_name()
        weact_device_setting_py = cls.grandparent_dir / "weact_device_setting.py"
        return subprocess.Popen([exec_name, str(weact_device_setting_py)], shell=True)
    
    @classmethod
    def theme_editor(cls,theme_name):
        exec_name = cls.get_executable_name()
        theme_editor_py = cls.grandparent_dir / "theme-editor.py"
        return subprocess.Popen([exec_name, str(theme_editor_py),f"\"{theme_name}\""], shell=True)
    
    @classmethod
    def image_scaler_tool(cls):
        exec_name = cls.get_executable_name()
        image_scaler_tool_py = cls.grandparent_dir / "image_scaler_tool.py"
        return subprocess.Popen([exec_name, str(image_scaler_tool_py)], shell=True)
    
    @classmethod
    def image_gif2png_scaler_tool(cls):
        exec_name = cls.get_executable_name()
        image_gif2png_scaler_tool_py = cls.grandparent_dir / "image_gif2png_scaler_tool.py"
        return subprocess.Popen([exec_name, str(image_gif2png_scaler_tool_py)], shell=True)
    
def get_version():
    version_file = Path(__file__).parent.parent / "version"
    try:
        with open(version_file, 'r') as f:
            version = f.read().strip()
            return version
    except Exception as e:
        print(f"Error reading version file: {e}")
        return "V0.0.0"