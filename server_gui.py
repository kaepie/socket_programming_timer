import tkinter as tk
from tkinter import scrolledtext
import socket
import threading
import time

# 6510450291 Chutipong Triyasith
class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Server GUI")

        self.log = scrolledtext.ScrolledText(root, state='disabled', height=10)
        self.log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        self.start_button = tk.Button(button_frame, text="Start Server", command=self.start_server, bg="lightgreen")
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(button_frame, text="Stop Server", command=self.stop_server, bg="red", state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)

        self.server_socket = None
        self.clients = []
        self.timer_thread = None

    def log_message(self, message):
        self.log.config(state='normal')
        self.log.insert(tk.END, message + '\n')
        self.log.yview(tk.END)
        self.log.config(state='disabled')

    def countdown_timer(self, duration):
        while duration > 0:
            time.sleep(1)
            duration -= 1
            self.broadcast(f"100:Time Update:time_left {duration}#")
        self.broadcast("100:Time Update:time_up#")

    def broadcast(self, message):
        for client_socket in self.clients:
            try:
                client_socket.send(message.encode())
            except BrokenPipeError:
                self.clients.remove(client_socket)

    def handle_client(self, client_socket, addr):
        self.log_message(f"Connected to {addr}")
        self.clients.append(client_socket)
        while True:
            try:
                data = client_socket.recv(1024).decode().lower()
                self.log_message(f"Received from {addr}: {data}")
            except ConnectionResetError:
                self.clients.remove(client_socket)
                break

            if data.startswith("start"):
                parts = data.split()
                if len(parts) == 3:
                    try:
                        duration = int(parts[1])
                        unit = parts[2].lower()
                        if unit == "min":
                            duration *= 60
                        elif unit == "hour":
                            duration *= 3600
                        self.log_message(f"Countdown timer started for {parts[1]} {unit}")
                        self.broadcast("200:OK:Timer started")
                    except ValueError:
                        self.log_message("Invalid time format")
                        self.broadcast("400:Bad Request:Invalid time format")
                        continue
                elif len(parts) == 2:
                    try:
                        duration = int(parts[1])
                        self.log_message(f"Countdown timer started for {parts[1]} seconds")
                        self.broadcast("200:OK:Timer started")
                    except ValueError:
                        self.log_message("Invalid time format")
                        self.broadcast("400:Bad Request:Invalid time format")
                        continue

                if self.timer_thread is None or not self.timer_thread.is_alive():
                    self.timer_thread = threading.Thread(target=self.countdown_timer, args=(duration,))
                    self.timer_thread.start()

            elif data.startswith("timer"):
                try:
                    parts = data.split()[1]
                    hours, minutes, seconds = map(int, parts.split(':'))
                    duration = hours * 3600 + minutes * 60 + seconds
                    self.log_message(f"Countdown timer started for {duration} seconds")
                    self.broadcast("200:OK:Timer started")
                    if self.timer_thread is None or not self.timer_thread.is_alive():
                        self.timer_thread = threading.Thread(target=self.countdown_timer, args=(duration,))
                        self.timer_thread.start()
                except ValueError:
                    self.log_message("Invalid time format")
                    self.broadcast("400:Bad Request:Invalid time format")

            elif data == "exit":
                self.log_message(f"Closing connection with client {addr}")
                self.broadcast("100:Information:closing#")
                self.clients.remove(client_socket)
                break
        client_socket.close()
        self.log_message(f"Connection closed with {addr}")

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('localhost', 12345))
        self.server_socket.listen(5)
        self.log_message("Server is waiting for connections...")

        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.start()
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_server(self):
        for client_socket in self.clients:
            client_socket.close()
        self.clients = []
        
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        self.log_message("Server stopped")
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def accept_connections(self):
        while self.server_socket:
            try:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.start()
            except OSError:
                break

root = tk.Tk()
server_gui = ServerGUI(root)
root.mainloop()