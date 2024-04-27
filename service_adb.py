import requests
import json
import tkinter as tk
from tkinter import messagebox
import time
import threading
import sys

first_url = "http://192.168.1.1/ui/dboard/prod?version"
second_url = "http://192.168.1.254/ui/dboard/prod"

def check_availability(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False

def perform_checks(url):
    with requests.session() as session:
        response = session.get(url)
        software_ver = response.text.replace("software_ver=", "")
        print("Software Version:", software_ver)
        """
        response = session.get(second_url)
        data = response.text.splitlines()
        boardman = None
        board_SERIAL = None

        for line in data:
            if line.startswith("boardman:"):
                boardman = line.split(':')[1].strip()
            elif line.startswith("board_SERIAL:"):
                board_SERIAL = line.split(':')[1].strip()

        data_dict = {
            "software_ver": software_ver,
            "boardman": boardman,
            "board_SERIAL": board_SERIAL
        }

        """
        data_dict = {"software_ver": software_ver}
        json_data = json.dumps(data_dict)
        """
        try:
            java_url = "https://app.oneumbrella.pl/adb/firmwareAgent/post"
            headers = {"Content-Type": "application/json"}
            response = requests.post(java_url, data=json_data, headers=headers)
        except Exception as e:
        print(e)
        """
        print(json_data)

        return json_data

def start_service():
    global is_service_on
    if is_service_on:
        print("Service is already ON")
        messagebox.showinfo("Service", "Service is already ON")
    else:
        is_service_on = True
        lbl_service_status.config(text="SERVICE IS ON", bg="green")
        print("Service is ON")
        threading.Thread(target=perform_checks_periodically).start()

def stop_service():
    global is_service_on
    if not is_service_on:
        print("Service is already OFF")
        messagebox.showinfo("Service", "Service is already OFF")
    else:
        is_service_on = False
        lbl_service_status.config(text="SERVICE IS OFF", bg="red")
        print("Service is OFF")

def perform_checks_periodically():
    while is_service_on:
        print("Checking connection...")
        if check_availability(first_url):
            perform_checks(first_url)
        else:
            print("No connection available...")
        time.sleep(5)  # Poczekaj 5 sekund przed kolejnym sprawdzeniem

# GUI
root = tk.Tk()
root.title("ADB Service Control")
root.geometry("400x400")
root.resizable(False, False)
is_service_on = False

frame_service_status = tk.Frame(root, bg="white", width=200, height=50)
frame_service_status.pack(pady=10)

lbl_service_status = tk.Label(frame_service_status, text="SERVICE IS OFF", bg="red", fg="white", font=("Arial", 12))
lbl_service_status.pack(fill="both", expand=True)

frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

btn_service_on = tk.Button(frame_buttons, text="SERVICE ON", command=start_service, bg="green", fg="white", width=10)
btn_service_on.pack(side="left", padx=5)

btn_service_off = tk.Button(frame_buttons, text="SERVICE OFF", command=stop_service, bg="red", fg="white", width=10)
btn_service_off.pack(side="left", padx=5)

frame_terminal = tk.Frame(root)
frame_terminal.pack(pady=10)

lbl_terminal = tk.Label(frame_terminal, text="Terminal:", font=("Arial", 12))
lbl_terminal.pack()

txt_terminal = tk.Text(frame_terminal, width=40, height=10)
txt_terminal.pack()

# Funkcja do przekierowania standardowego wyjścia na Text Widget
def redirect_stdout_to_text_widget():
    class StdoutRedirector:
        def __init__(self, text_widget):
            self.text_widget = text_widget

        def write(self, message):
            self.text_widget.insert("end", message)
            self.text_widget.see("end")

        def flush(self):
            pass

    sys.stdout = StdoutRedirector(txt_terminal)

lbl_terminal.pack()

redirect_stdout_to_text_widget()

# GUI
root.mainloop()