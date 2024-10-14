import os
import sys
try:
    import tkinter as tk
except:
    print(
        "[ERROR] Python dependencies not installed. Please follow start guide: https://github.com/mathoudebine/turing-smart-screen-python/wiki/System-monitor-:-how-to-start")
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