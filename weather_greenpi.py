import json
import urllib.request


# build the string
class Weather:
    def __init__(self) -> None:
        self.weather = self.weather_description = self.feels_like = self.temperature = self.humidity = self.name = ""
        self.addr = 'https://api.openweathermap.org/data/2.5/weather?lat=' + lat + '&lon=' + lon + '&appid=' + api_key
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

# convert the weather to a string
class Stringifier:
    def __init__(self) -> None:
        self.weather = Weather()

    def build_string(self) -> str:
        self.weather.get_weather()
        self.weather.interpret_weather()
        return f"{self.weather.name} = {self.weather.weather}: {self.weather.weather_description}, {self.weather.feels_like}, {self.weather.temperature}, {self.weather.humidity}"

a = Stringifier()
print(a.build_string())
