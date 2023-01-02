from AutomatedTesting.UsefulFunctions import readable_freq
from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import SignalGeneratorChannel

from guizero import Box, Text
from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from dataclasses import dataclass
import pyvisa
import time
from threading import Thread


TEXT_COLOUR = "black"
TITLE_FONT = "Helvetica"
TITLE_SIZE = 24
MAIN_FONT = "Helvetica"
MAIN_SIZE = 36
SUB_FONT = "Helvetica"
SUB_SIZE = 24


class Overlay:
    def __init__(self, instrument, parent_box: Box):
        if not instrument.is_connected():
            # Need to open connection to instrument
            instrument.initialise()
        self.parent_box = parent_box
        self.main_box = Box(parent_box, align="left",
                            border=5, width=480, height="fill")
        self.get_info_thread = Thread(
            target=self.get_info, args=[parent_box], daemon=True
        )
        

    def get_info(self):
        """
        Retrieves all the information needed to update the GUI as this might take a long time
        """
        raise NotImplementedError


    def update(self):
        raise NotImplementedError

    def destroy(self):
        self.main_box.destroy()


class SignalGeneratorOverlay(Overlay):
    def __init__(self, instrument: BaseInstrument, channel_number: int, parent_box: Box):
        """
        Takes an empty box, starts connection to instrument (if needed)
        and connects the callback function
        """
        self.event_name = f"<<{instrument.name}_{channel_number}>>"

        super().__init__(instrument, parent_box)
        self.channel = instrument.reserve_channel(channel_number, "Overlay")
        self.title = Text(self.main_box, text=f"{instrument.name} - Channel {channel_number}",
                          width="fill", align="top", color=TEXT_COLOUR, font=TITLE_FONT, size=TITLE_SIZE)
        self.frequency_field = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=MAIN_FONT, size=MAIN_SIZE)
        self.power_field = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=MAIN_FONT, size=MAIN_SIZE)
        self.enabled_field = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=SUB_FONT, size=SUB_SIZE)
        print(f"Created box for {instrument.name} - Channel {channel_number}")
        self.parent_box.tk.bind(self.event_name, self.update_gui)
        self.get_info_thread.start()

    def get_info(self, parent_box):
        while True:
            self.frequency = f"{readable_freq(self.channel.get_freq())}"
            self.power = f"{self.channel.get_power():.2f}dBm"
            self.enabled = "ON" if self.channel.get_output_enabled_state() else "Off"
            parent_box.tk.event_generate(self.event_name)
            time.sleep(0.25)
            
    def update_gui(self, event):
        self.frequency_field.value = self.frequency
        self.power_field.value = self.power
        self.enabled_field.value = self.enabled


    def destroy(self):
        self.channel.free()
        super().destroy()

class PowerSupplyOverlay(Overlay):
    def __init__(self, instrument: BaseInstrument, channel_number: int, parent_box: Box):
        """
        Takes an empty box, starts connection to instrument (if needed)
        and connects the callback function
        """
        self.event_name = f"<<{instrument.name}_{channel_number}>>"
        super().__init__(instrument, parent_box)
        self.channel = instrument.reserve_channel(channel_number, "Overlay")
        self.title = Text(self.main_box, text=f"{instrument.name} - Channel {channel_number}",
                          width="fill", align="top", color=TEXT_COLOUR, font=TITLE_FONT, size=TITLE_SIZE)
        self.voltage_field = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=MAIN_FONT, size=MAIN_SIZE)
        self.current_field = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=MAIN_FONT, size=MAIN_SIZE)
        self.enabled_field = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=SUB_FONT, size=SUB_SIZE)
        print(f"Created box for {instrument.name} - Channel {channel_number}")
        self.parent_box.tk.bind(self.event_name, self.update_gui)
        self.get_info_thread.start()

    def get_info(self, parent_box):
        while True:
            enabled = self.channel.get_output_enabled_state()
            if enabled:
                self.enabled = "ON"
                self.voltage = f"{self.channel.measure_voltage():.3f}V"
                self.current = f"{self.channel.measure_current():.3f}A"
            else:
                self.enabled = "Off"
                self.voltage = f"{self.channel.get_voltage():.3f}V"
                self.current = f"{self.channel.get_current_limit():.3f}A"
            
            parent_box.tk.event_generate(self.event_name)
            time.sleep(0.25)
            
    def update_gui(self, event):
        self.voltage_field.value = self.voltage
        self.current_field.value = self.current
        self.enabled_field.value = self.enabled


    def destroy(self):
        self.channel.free()
        super().destroy()
