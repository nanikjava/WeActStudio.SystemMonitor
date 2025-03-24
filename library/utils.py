import os
import sys
import requests,datetime
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
    main = tk.Tk()

    main.title(title)

    screen_width = main.winfo_screenwidth()  
    screen_height = main.winfo_screenheight()  
    height = 50
    width = 300 
    position_top = int(screen_height / 2 - height / 2)  
    position_right = int(screen_width / 2 - width / 2)  
    main.geometry(f'{width}x{height}+{position_right}+{position_top}')

    main.resizable(False, False)
    main.attributes('-topmost',True)
    main.attributes("-toolwindow", True)

    label = tk.Label(
        main, text=message, anchor="w"
    )
    label.grid(row=0, column=0,columnspan=2,padx=5, pady=10, ipadx=100, ipady=5, sticky="w")

    main.update()
    # screen_width = main.winfo_screenwidth()
    # screen_height = main.winfo_screenheight()
    # main_window_width = main.winfo_width()
    # main_window_height = main.winfo_height()
    # x = (screen_width - main_window_width) // 2
    # y = (screen_height - main_window_height) // 2
    # main.geometry(f"{main_window_width}x{main_window_height}+{x}+{y}")
    # main.deiconify()

    if delay > 0:
        main.after(delay, lambda: (main.destroy() if main.winfo_viewable() else None))

    return main

def app_is_running(lockfile):  
    if os.path.exists(lockfile):  
        value = open(lockfile).read().strip()
        try:  
            pid = int(value)  
            p = psutil.Process(pid)  
            p.is_running()
        except:
            # PID doesn't exist anymore, so we can safely delete the lockfile and proceed  
            os.remove(lockfile)    
            return False  
        return True
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