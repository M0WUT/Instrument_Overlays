from guizero import App, Text, Box

import socket
import logging
from instruments import SignalGeneratorOverlay, PowerSupplyOverlay
from AutomatedTesting.Instruments.InstrumentConfig import sdg2122x, e4433b, psu2, psu3



NUM_BOXES = 4

boxes = {}

# Network commms setup
PORT = 5973
NETWORK_TIMEOUT = 1

# Set instruments for interactive use
sdg2122x.only_software_control = False
e4433b.only_software_control = False
psu2.only_software_control = False
psu3.only_software_control = False


app = App(title="hello world", width=1920, height=1080, bg="green")
bottom_box = Box(app, width="fill", align="bottom", height=250)



conn = addr = None

def handle_connection():
    # If there's no connection, listen for incoming
    # otherwise listen for data

    # Needed as can't work out how to do static variables
    global conn
    global addr
    global bottom_box
    if not conn:
        try:
            conn, addr = sock.accept() 
            print(f"Incoming connection from {addr[0]}")
            conn.settimeout(0.5)
        except socket.timeout:
            pass
    else:
        # There's already a connection
        try:
            data = conn.recv(1024).decode("utf-8").strip()
            if not data:
                # Disconnected
                print(f"Disconnection from {addr[0]}")
                conn = addr = None
            else:
                if data in boxes:
                    # Already existing instrument so close connection
                    boxes[data].destroy()
                    del boxes[data]
                    print(f"Removed box for {data}")
                elif data == "clearall":
                    for x in boxes:
                        boxes[x].destroy()
                        del boxes[data]
                else:
                    # Open new connection to instruments
                    if data == "sdg2122x1":
                        boxes[data] = SignalGeneratorOverlay(sdg2122x, 1, bottom_box)
                    elif data == "sdg2122x2":
                        boxes[data] = SignalGeneratorOverlay(sdg2122x, 2, bottom_box)
                    elif data == "e4433b":
                        boxes[data] = SignalGeneratorOverlay(e4433b, 1, bottom_box)
                    elif data == "psu2":
                        boxes[data] = PowerSupplyOverlay(psu2, 1, bottom_box)
                    elif data == "psu3":
                        boxes[data] = PowerSupplyOverlay(psu3, 1, bottom_box)
                    else:
                        raise NotImplementedError
           
        except socket.timeout:
            pass
        
def update():
    for _, x in boxes.items():
        x.update()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("", PORT))
    sock.listen()
    sock.settimeout(0.25)
    bottom_box.repeat(NETWORK_TIMEOUT * 1000, handle_connection)
    #bottom_box.repeat(500, update)
    app.display()