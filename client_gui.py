import tkinter as tk
from tkinter import scrolledtext
import socket
import threading

# 6510450291 Chutipong Triyasith
class ClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Client GUI")

        self.timer_label = tk.Label(root, text="00:00:00", font=("Helvetica", 48), fg="blue")
        self.timer_label.pack(pady=20)

        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        self.command_entry = tk.Entry(button_frame)
        self.command_entry.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)

        self.send_button = tk.Button(button_frame, text="Send Command", command=self.send_command, bg="lightblue")
        self.send_button.pack(side=tk.LEFT, padx=10)

        self.connect_button = tk.Button(button_frame, text="Connect to Server", command=self.connect_to_server, bg="lightgreen")
        self.connect_button.pack(side=tk.LEFT, padx=10)

        self.disconnect_button = tk.Button(button_frame, text="Disconnect", command=self.disconnect_from_server, bg="blue", state=tk.DISABLED)
        self.disconnect_button.pack(side=tk.LEFT, padx=10)

        self.log = scrolledtext.ScrolledText(root, state='disabled', height=10)
        self.log.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.client_socket = None
        self.buffer = ""

    def log_message(self, message):
        self.log.config(state='normal')
        self.log.insert(tk.END, message + '\n')
        self.log.yview(tk.END)
        self.log.config(state='disabled')

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(('localhost', 12345))
        self.log_message("Connected to the server")
        self.log_message("Enter command (Start <time> <sec or min or hour>/ Timer <hour:min:sec> /EXIT) ")

        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.start()
        
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)

    def disconnect_from_server(self):
        if self.client_socket:
            self.client_socket.send("exit".encode())
            self.client_socket.close()
            self.client_socket = None
            self.log_message("Disconnected from the server")
        
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)

    def send_command(self):
        command = self.command_entry.get().strip().lower()
        if command:
            self.client_socket.send(command.encode())
            self.command_entry.delete(0, tk.END)

    def receive_messages(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode().lower()
                self.buffer += data
                while '#' in self.buffer:
                    message, self.buffer = self.buffer.split('#', 1)
                    status_code, status_phrase, content = message.split(':', 2)
                    if status_code == "100":
                        if content.startswith("time_left"):
                            time_left = int(content.split()[1])
                            hours, remainder = divmod(time_left, 3600)
                            minutes, seconds = divmod(remainder, 60)
                            self.timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
                        elif content == "time_up":
                            self.timer_label.config(text="00:00:00")
                            self.log_message("Time is up!")
                        elif content == "timer_started":
                            self.log_message("Timer started")
                        elif content == "closing":
                            self.log_message("Server closed the connection")
                            self.client_socket.close()
                            self.client_socket = None
                            return
                    else:
                        self.log_message(f"Received [ status code: {status_code} , status phrases: {status_phrase} ]: {content}")
            except ConnectionResetError:
                self.log_message("Server connection lost")
                break

root = tk.Tk()
client_gui = ClientGUI(root)
root.mainloop()