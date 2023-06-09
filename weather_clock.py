#!/usr/bin/env python

# basically a simple copy from silly_clock.py https://github.com/rm-hull/luma.led_matrix/tree/master/examples, 
# with some modifications made to have it more oop and more extendable then we can add more data later on.

import time
from datetime import datetime

from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT

import json
import urllib.request

import weather_settings as ws

# =============================================================================
class Weather:
    ''' Get the API and build the string.
    '''
    def __init__(self) -> None:
        self.settings = ws.Settings()
        self.weather = self.weather_description = self.feels_like = self.temperature = self.humidity = self.name = ""
        self.addr = 'https://api.openweathermap.org/data/2.5/weather?lat=' + self.settings.lat + '&lon=' + self.settings.long + '&appid=' + self.settings.api_key
        self.y = None

    def get_weather(self) -> None:
        with urllib.request.urlopen(self.addr) as url:
            self.y = json.load(url)
        
    def interpret_weather(self) -> None:
        self.weather = self.y['weather'][0]['main']
        self.weather_description = self.y['weather'][0]['description']
        self.feels_like = f"feels like: {self.y['main']['feels_like'] - 273.15:.2f} C"
        self.temperature = f"temperature: {self.y['main']['temp'] - 273.15:.2f} C"
        self.humidity = f"humidity: {self.y['main']['humidity']} %"
        self.name = f"{self.y['name']}"

# =============================================================================
class Stringifier:
    ''' Convert the weather to a string
    '''
    def __init__(self) -> None:
        self.weather = Weather()

    def build_string(self) -> str:
        self.weather.get_weather()
        self.weather.interpret_weather()
        return f"{self.weather.name} = {self.weather.weather}: {self.weather.weather_description}, {self.weather.feels_like}, {self.weather.temperature}, {self.weather.humidity}"

# =============================================================================
class Displayer:
    ''' Display the hours minutes seconds on the MAX7219.
    Provide simple animation also.
    '''
    def __init__(self, device) -> None:
        self.idx_h = 0
        self.idx_col1 = 16
        self.idx_m = 18
        self.idx_col2 = 34
        self.idx_s = 36
        self.device = device

    def static_show(self, hours, minutes, seconds, toggle):
        self.draw(hours, minutes, seconds, toggle, 1)

    def draw(self, hours, minutes, seconds, toggle, y_index):
        with canvas(self.device) as draw:
            text(draw, (0, y_index), hours, fill="white", font=proportional(CP437_FONT))
            text(draw, (16, y_index), ":" if toggle else " ", fill="white", font=proportional(TINY_FONT))
            text(draw, (18, y_index), minutes, fill="white", font=proportional(CP437_FONT))
            text(draw, (34, y_index), ":" if toggle else " ", fill="white", font=proportional(TINY_FONT))
            text(draw, (36, y_index), seconds, fill="white", font=proportional(CP437_FONT))

    def animate(self, hours, minutes, seconds, from_y, to_y):
        current_y = from_y
        while current_y != to_y:
            self.draw(hours, minutes, seconds, toggle=True, y_index=current_y)
            time.sleep(0.1)
            current_y += 1 if to_y > from_y else -1

    def animate_up(self, hours, minutes, seconds):
        self.animate(hours, minutes, seconds, from_y=8, to_y=1)

    def animate_down(self, hours, minutes, seconds):
        self.animate(hours, minutes, seconds, from_y=1, to_y=8)

    def minute_change(self, hours, minutes, seconds):
        '''When we reach a minute change, animate it.'''
        seconds = "00"

        def helper(current_y):
            with canvas(self.device) as draw:
                text(draw, (0, 1), hours, fill="white", font=proportional(CP437_FONT))
                text(draw, (16, 1), ":", fill="white", font=proportional(TINY_FONT))
                text(draw, (18, current_y), minutes, fill="white", font=proportional(CP437_FONT))
                text(draw, (34, 1), ":", fill="white", font=proportional(TINY_FONT))
                text(draw, (36, 1), seconds, fill="white", font=proportional(CP437_FONT))
            time.sleep(0.1)
        for current_y in range(1, 9):
            helper(current_y)
        minutes = datetime.now().strftime('%M')
        for current_y in range(9, 1, -1):
            helper(current_y)

        if minutes == "00":
            self.hour_change(hours, minutes, seconds)

    def hour_change(self, hours, minutes, seconds):
        '''When we reach an hour change, animate it.'''
        minutes = "00"
        seconds = "00"

        def helper(current_y):
            with canvas(self.device) as draw:
                text(draw, (0, current_y), hours, fill="white", font=proportional(CP437_FONT))
                text(draw, (16, 1), ":", fill="white", font=proportional(TINY_FONT))
                text(draw, (18, 1), minutes, fill="white", font=proportional(CP437_FONT))
                text(draw, (34, 1), ":", fill="white", font=proportional(TINY_FONT))
                text(draw, (36, 1), seconds, fill="white", font=proportional(CP437_FONT))
            time.sleep(0.1)
        for current_y in range(1, 9):
            helper(current_y)
        hours = datetime.now().strftime('%H')
        for current_y in range(9, 1, -1):
            helper(current_y)

# =============================================================================
class Timekeeper:
    ''' Timekeeping class, simply getting data from datetime.
    '''
    def __init__(self) -> None:
        self.hours = self.minutes = self.seconds = 0
        self.update_time()

    def update_time(self) -> None:
        self.hours = datetime.now().strftime('%H')
        self.minutes = datetime.now().strftime('%M')
        self.seconds = datetime.now().strftime('%S')

# =============================================================================
def main():
    ''' Main function of the weather clock.
    '''
    serial = spi(port=0, device=0, gpio=noop())
    device = max7219(serial, width=64, height=8, block_orientation=-90)
    device.contrast(50)

    tk = Timekeeper()
    dd = Displayer(device)
    a = Stringifier()

    dd.animate(tk.hours, tk.minutes, tk.seconds, -8, 1)

    counter = 0
    weather_to_show = a.build_string() + " > " + str(counter) 

    toggle = False  # Toggle the second indicator every second
    while True:
        toggle = not toggle
        sec = datetime.now().second
        if sec == 59:
            # When we change minutes, animate the minute change
            dd.minute_change(tk.hours, tk.minutes, tk.seconds)
        elif sec == 10:
            full_msg = time.ctime()
            show_message(device, full_msg, fill="white", font=proportional(CP437_FONT))
        elif sec == 30:
            # Half-way through each minute, display the complete date/time,
            # animating the time display into and out of the abyss.
            dd.animate(tk.hours, tk.minutes, tk.seconds, 1, 8)
            show_message(device, weather_to_show, fill="white", font=proportional(CP437_FONT))
            dd.animate(tk.hours, tk.minutes, tk.seconds, 8, 1)
        else:
            tk.update_time()
            dd.static_show(tk.hours, tk.minutes, tk.seconds, toggle)
            time.sleep(0.5)

        # every 5 mins.
        if int(tk.minutes) % 5 == 0 and int(tk.seconds) == 5:
            counter += 1
            weather_to_show = a.build_string() + " > " + str(counter) 


# =============================================================================
if __name__ == "__main__":
    main()
