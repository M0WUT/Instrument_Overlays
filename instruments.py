from AutomatedTesting.UsefulFunctions import readable_freq
from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import SignalGeneratorChannel

from guizero import Box, Text
from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from dataclasses import dataclass
import pyvisa
import time


TEXT_COLOUR = "black"
TITLE_FONT = "Helvetica"
TITLE_SIZE = 24
MAIN_FONT = "Helvetica"
MAIN_SIZE = 36
SUB_FONT = "Helvetica"
SUB_SIZE = 24


class Overlay:
    def __init__(self, parent_box: Box):
        self.main_box = Box(parent_box, align="left",
                            border=5, width=480, height="fill")

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
        if not instrument.is_connected():
            # Need to open connection to instrument
            instrument.initialise()
        super().__init__(parent_box)
        self.channel = instrument.reserve_channel(channel_number, "Overlay")
        self.title = Text(self.main_box, text=f"{instrument.name} - Channel {channel_number}",
                          width="fill", align="top", color=TEXT_COLOUR, font=TITLE_FONT, size=TITLE_SIZE)
        self.frequency = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=MAIN_FONT, size=MAIN_SIZE)
        self.power = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=MAIN_FONT, size=MAIN_SIZE)
        self.enabled = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=SUB_FONT, size=SUB_SIZE)
        print(f"Created box for {instrument.name} - Channel {channel_number}")

    def update(self):
        self.frequency.value = f"{readable_freq(self.channel.get_freq())}"
        self.power.value = f"{self.channel.get_power():.2f}dBm"
        self.enabled.value = "Enabled" if self.channel.get_output_enabled_state() else "Disabled"


    def destroy(self):
        self.channel.free()
        super().destroy()

class PowerSupplyOverlay(Overlay):
    def __init__(self, instrument: BaseInstrument, channel_number: int, parent_box: Box):
        """
        Takes an empty box, starts connection to instrument (if needed)
        and connects the callback function
        """
        if not instrument.is_connected():
            # Need to open connection to instrument
            instrument.initialise()
        super().__init__(parent_box)
        self.channel = instrument.reserve_channel(channel_number, "Overlay")
        self.title = Text(self.main_box, text=f"{instrument.name} #{channel_number}",
                          width="fill", align="top", color=TEXT_COLOUR, font=TITLE_FONT, size=TITLE_SIZE)
        self.voltage = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=MAIN_FONT, size=MAIN_SIZE)
        self.current = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=MAIN_FONT, size=MAIN_SIZE)
        self.enabled = Text(self.main_box, text="N/A",
                              width="fill", align="top", color=TEXT_COLOUR, font=SUB_FONT, size=SUB_SIZE)
        self.main_box.repeat(5000, self.update)
        print(f"Created box for {instrument.name} #{channel_number}")

    def update(self):
        enabled = self.channel.get_output_enabled_state()
        if enabled:
            self.enabled.value = "ON"
            self.voltage.value = f"{self.channel.measure_voltage():0.3f}V"
            self.current.value = f"{self.channel.measure_current():0.3f}A"
        else:
            self.enabled.value = "Off"
            self.voltage.value = f"{self.channel.get_voltage():0.3f}V"
            self.current.value = f"{self.channel.get_current_limit():0.3f}A"
        



    def destroy(self):
        self.channel.free()
        super().destroy()
