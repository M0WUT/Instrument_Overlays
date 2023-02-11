import time
from dataclasses import dataclass
from threading import Thread

import pyvisa
from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGeneratorChannel,
)
from AutomatedTesting.UsefulFunctions import prefixify
from guizero import Box, Text
from pyvisa.errors import VisaIOError

TEXT_COLOUR = "blue"
BORDER_COLOUR = "blue"
BORDER_THICKNESS = 7
BACKGROUND_COLOUR = "gray"
TITLE_FONT = "Tahoma Bold"
TITLE_SIZE = 20
MAIN_FONT = "Tahoma Bold"
MAIN_SIZE = 24
SUB_FONT = "Tahoma Bold"
SUB_SIZE = 22


class Overlay:
    def __init__(self, instrument, parent_box: Box):
        if not instrument.is_connected():
            # Need to open connection to instrument
            instrument.initialise()
        self.instrument = instrument
        self.parent_box = parent_box
        self.main_box = Box(parent_box, align="left", width=480, height="fill")
        self.main_box.bg = BACKGROUND_COLOUR
        self.main_box.set_border(BORDER_THICKNESS, BORDER_COLOUR)
        self.stop_threads = False
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
        self.stop_threads = True
        self.get_info_thread.join()
        self.main_box.destroy()


class SignalGeneratorOverlay(Overlay):
    def __init__(
        self, instrument: BaseInstrument, channel_number: int, parent_box: Box
    ):
        """
        Takes an empty box, starts connection to instrument (if needed)
        and connects the callback function
        """
        self.event_name = f"<<{instrument.name}_{channel_number}>>"
        super().__init__(instrument, parent_box)
        self.channel = instrument.reserve_channel(channel_number, "Overlay")
        self.title = Text(
            self.main_box,
            text=f"{instrument.name} - Channel {channel_number}",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=TITLE_FONT,
            size=TITLE_SIZE,
        )
        self.frequency_field = Text(
            self.main_box,
            text="N/A",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=MAIN_FONT,
            size=MAIN_SIZE,
        )
        self.power_field = Text(
            self.main_box,
            text="N/A",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=MAIN_FONT,
            size=MAIN_SIZE,
        )
        self.enabled_field = Text(
            self.main_box,
            text="N/A",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=SUB_FONT,
            size=SUB_SIZE,
            height="fill",
        )
        print(f"Created box for {instrument.name} - Channel {channel_number}")
        self.parent_box.tk.bind(self.event_name, self.update_gui)
        self.get_info_thread.start()

    def get_info(self, parent_box):
        while True:

            self.frequency = prefixify(self.channel.get_freq(), "Hz")
            self.enabled = "ON" if self.channel.get_output_enabled_state() else "Off"

            load_impedance = self.channel.get_load_impedance()
            if load_impedance == 50:
                self.power = f"{self.channel.get_power():.2f}dBm"
            elif load_impedance == float("inf"):
                self.power = f"{self.channel.get_vpp():.3f}Vpp (Hi-Z)"
            if self.stop_threads:
                break
            parent_box.tk.event_generate(self.event_name)

    def update_gui(self, event):
        if self.frequency_field.value != self.frequency:
            self.frequency_field.value = self.frequency
        if self.power_field.value != self.power:
            self.power_field.value = self.power
        if self.enabled_field.value != self.enabled:
            self.enabled_field.value = self.enabled

    def destroy(self):
        super().destroy()
        self.channel.free()
        channel_status = [x.reserved for x in self.instrument.channels]
        if not any(channel_status):
            # All channels are unused
            self.instrument.cleanup()


class PowerSupplyOverlay(Overlay):
    def __init__(
        self, instrument: BaseInstrument, channel_number: int, parent_box: Box
    ):
        """
        Takes an empty box, starts connection to instrument (if needed)
        and connects the callback function
        """
        self.event_name = f"<<{instrument.name}_{channel_number}>>"
        super().__init__(instrument, parent_box)
        self.channel = instrument.reserve_channel(channel_number, "Overlay")
        self.title = Text(
            self.main_box,
            text=f"{instrument.name} - Channel {channel_number}",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=TITLE_FONT,
            size=TITLE_SIZE,
        )
        self.voltage_field = Text(
            self.main_box,
            text="N/A",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=MAIN_FONT,
            size=MAIN_SIZE,
        )
        self.current_field = Text(
            self.main_box,
            text="N/A",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=MAIN_FONT,
            size=MAIN_SIZE,
        )
        self.enabled_field = Text(
            self.main_box,
            text="N/A",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=SUB_FONT,
            size=SUB_SIZE,
        )
        print(f"Created box for {instrument.name} - Channel {channel_number}")
        self.parent_box.tk.bind(self.event_name, self.update_gui)
        self.get_info_thread.start()

    def get_info(self, parent_box):
        while True:
            try:
                enabled = self.channel.get_output_enabled_state()
                if enabled:
                    self.enabled = "ON"
                    self.voltage = f"{self.channel.measure_voltage():.3f}V"
                    self.current = f"{self.channel.measure_current():.3f}A"
                else:
                    self.enabled = "Off"
                    self.voltage = f"{self.channel.get_voltage():.3f}V"
                    self.current = f"{self.channel.get_current_limit():.3f}A"
                if self.stop_threads:
                    break
                parent_box.tk.event_generate(self.event_name)
            except VisaIOError:
                pass

    def update_gui(self, event):
        if self.voltage_field.value != self.voltage:
            self.voltage_field.value = self.voltage
        if self.current_field.value != self.current:
            self.current_field.value = self.current
        if self.enabled_field.value != self.enabled:
            self.enabled_field.value = self.enabled

    def destroy(self):
        super().destroy()
        self.channel.free()
        channel_status = [x.reserved for x in self.instrument.channels]
        if not any(channel_status):
            # All channels are unused
            self.instrument.cleanup()


class DMMOverlay(Overlay):
    def __init__(
        self,
        instrument: BaseInstrument,
        measurement_function,
        measurement_units: str,
        parent_box: Box,
    ):
        """
        Takes an empty box, starts connection to instrument (if needed)
        and connects the callback function
        """
        self.event_name = f"<<{instrument.name}>>"
        self.measurement_function = measurement_function
        self.measurement_units = measurement_units
        super().__init__(instrument, parent_box)
        self.instrument.set_remote_control()
        self.title = Text(
            self.main_box,
            text=f"{instrument.name}",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=TITLE_FONT,
            size=TITLE_SIZE,
        )
        self.measurement_field = Text(
            self.main_box,
            text="N/A",
            width="fill",
            align="top",
            color=TEXT_COLOUR,
            font=MAIN_FONT,
            size=48,
        )
        print(f"Created box for {instrument.name}")
        self.parent_box.tk.bind(self.event_name, self.update_gui)
        self.get_info_thread.start()

    def get_info(self, parent_box):
        while True:

            self.measurement = prefixify(
                self.measurement_function(),
                units=self.measurement_units,
                decimal_places=3,
            )
            if self.stop_threads:
                break


            parent_box.tk.event_generate(self.event_name)

    def update_gui(self, event):
        if self.measurement_field.value != self.measurement:
            self.measurement_field.value = self.measurement

    def destroy(self):
        super().destroy()
        self.instrument.cleanup()
