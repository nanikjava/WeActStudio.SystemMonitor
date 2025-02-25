import os
import sys
try:
    import tkinter as tk
    import psutil
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
    width = 350 
    position_top = int(screen_height / 2 - height / 2)  
    position_right = int(screen_width / 2 - width / 2)  
    main.geometry(f'{width}x{height}+{position_right}+{position_top}')

    main.resizable(False, False)
    main.attributes('-topmost',True)
    main.attributes("-toolwindow", True)

    label = tk.Label(
        main, text=message
    )
    label.pack(
        side=tk.TOP, padx=5, pady=10, anchor=tk.W
    )

    main.update()

    if delay > 0:
        main.after(delay, lambda: (main.destroy() if not main.winfo_viewable() else None))

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