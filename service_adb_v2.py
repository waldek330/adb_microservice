import requests
import json
import tkinter as tk
from tkinter import messagebox
import time
import threading
import sys

first_url = "https://192.168.1.254/ui/dboard/prod?version"
second_url = "https://192.168.1.254/ui/dboard/prod"

second_url_data = None  # Przechowuje dane z second_url
is_data_sent = False # przechowuje dane czy zostało wysłane zapytanie do serwisu java_url


"""
Funkcja sprawdza dostępność strony podanej w argumencie , z uwzględnieniem pominięcia certyfikatu ssl oraz z timeout 3 sec, zwraca wartość logiczną
"""
def check_availability(url):
    try:
        response = requests.get(url, verify=False, timeout=3)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException:
        return False

"""
Funkcja ustawie dwie zmienne globalne które odpowiadają kolejno za dane z drugiej strony dostępnej na routerze tylko raz po resecie oraz warunek logiczny is_data_sent czy dane zostały wysłane do serwisu.
Następnie logowana jest sesja HTTP która pobiera z pierwszego adresu tekst odnośnie software, jeżeli w zwrotce nie tekst nie zaczyna się od software_ver podajemy że nie ma połączenia z routerem.
Po pobraniu tekstu z pierwszego adresu sprawdzamy dostępność kolejnego adresu HTTP który po reset dostępny jest tylko raz do wyświetlenia.
Dwa następny ify odnoszą się do tego czy adres jest osiągalny lub nie, zależnie od wyniku wyświetla zwrotkę lub przechodzi dalej do pobrania tekstu i wyciągnięciu z nich numery seryjnego oraz mac adresu.
Tworzymy słownik do którego umieszczamy pobrane dane i konwertujemy je na JSONa, jeżeli nie można było uzupełnić któregoś rekordu w kolejnym if waliduje warości puste.

Ostatni etap to wysłanie requestu POST do serwisu z danymi w json. Zmieniamy dane is_data_sent na wartość logiczną true oraz ustawiamy None dla second_url_data żeby zresetować tą wartość.
"""
def perform_checks(url):
    global second_url_data
    global is_data_sent

    if is_data_sent:
        print("Software has been uploaded to the system, please unplug the router")
        return
    
    with requests.session() as session:
        response = session.get(url, verify=False,timeout=3)
        software_ver = response.text.strip()

        if not software_ver.startswith("software_ver"):
            print("There is no connection ")
            is_data_sent = False
        elif software_ver.startswith("software_ver"):
            software_ver = response.text.replace("software_ver=", "")
            print("Software Version:", software_ver)
            
            if second_url_data is None:
                response = session.get(second_url, allow_redirects=False, verify=False,timeout=3)
                if response.status_code == 200:
                    second_url_data = response.text
            
            if second_url_data is not None:
                data = second_url_data.strip().split("\n")

                board_mac = None
                board_serial = None 

                for line in data:
                    key, value = line.split("=")
                    if key.strip() == "board_mac":
                        board_mac = value.strip()
                    elif key.strip() == "board_serial":
                        board_serial = value.strip()

            print("board_mac:", board_mac)
            print("board_serial:", board_serial)

            data_dict = {
                "software_VER": software_ver,
                "boardman": board_mac,
                "board_SERIAL": board_serial
            }

            json_data = json.dumps(data_dict)
            print(json_data)
            
            if "null" in json_data:
                print("Invalid data. Cannot send null values.")
                return

            try:

                java_url = "https://172.16.4.90:1030/adb/firmwareAgent/post"
                headers = {"Content-Type": "application/json"}
                timeout = 12
                response = requests.post(java_url, data=json_data, headers=headers, verify=False,timeout=timeout)
                if response.status_code == 200:
                    is_data_sent = True
                    second_url_data = None
                    time.sleep(3)
            except Exception as e:
                print(e)

            if is_data_sent:
                print("Software has been uploaded to the system, please plug in the next device")

            return json_data
        
#Funkcja uruchamiająca serwis i ustawiająca zmienną is_service_on jako globalną. Odpowiada również za zmianę guzika uruchamiającego serwis.
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

"""
Funkcja która w pętli uruchamia serwis i sprawdza dostępność pierwszego adresu url a następnie wykonuje główny kod tzn sprawdzenie danych.
W przypadku gdy adres jest niedostępny loguje w terminalu no connection available.
"""
def perform_checks_periodically():
    global is_data_sent
    while is_service_on:        
        print("Checking connection...")
        if check_availability(first_url):
            perform_checks(first_url)
        else:
            is_data_sent = False
            print("No connection available...")
        time.sleep(5)  # Poczekaj 5 sekund przed kolejnym sprawdzeniem


# GUI
root = tk.Tk()
root.title("ADB Service Control")
root.geometry("500x500")
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

txt_terminal = tk.Text(frame_terminal, width=55, height=35)
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
