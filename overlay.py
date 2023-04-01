import logging
import socket

from AutomatedTesting.Instruments.InstrumentConfig import (
    dmm,
    e4433b,
    psu2,
    psu3,
    sdg2122x,
)
from guizero import App, Box, Text

from instruments import DMMOverlay, PowerSupplyOverlay, SignalGeneratorOverlay

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
# dmm.only_software_control = False

app = App(title="hello world", width=1920, height=1080, bg="green")
bottom_box = Box(app, width="fill", align="bottom", height=180)


conn = addr = None


def clear_dmm_boxes():
    dmm_boxes = [x for x in boxes if x.startswith("dmm_")]
    for x in dmm_boxes:
        boxes[x].destroy()
        del boxes[x]


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
                    box_list = list(boxes.keys())
                    for x in box_list:
                        boxes[x].destroy()
                        del boxes[x]
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
                    elif data == "dmm_dcv":
                        clear_dmm_boxes()
                        boxes[data] = DMMOverlay(
                            dmm, dmm.configure_dc_voltage, "V", bottom_box
                        )
                    elif data == "dmm_dci":
                        clear_dmm_boxes()
                        boxes[data] = DMMOverlay(
                            dmm, dmm.configure_dc_current, "A", bottom_box
                        )
                    elif data == "dmm_res":
                        clear_dmm_boxes()

                        boxes[data] = DMMOverlay(
                            dmm, dmm.configure_resistance, "Ω", bottom_box
                        )
                    elif data == "dmm_diode":
                        clear_dmm_boxes()

                        boxes[data] = DMMOverlay(
                            dmm, dmm.configure_diode_voltage, "V", bottom_box
                        )
                    else:
                        raise NotImplementedError(data)

        except socket.timeout:
            pass


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    app.tk.attributes("-fullscreen", True)
    app.tk.attributes("-type", "dock")

    sock.bind(("", PORT))
    sock.listen()
    sock.settimeout(0.1)
    bottom_box.repeat(NETWORK_TIMEOUT * 1000, handle_connection)
    app.display()
