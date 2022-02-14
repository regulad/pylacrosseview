from logging import INFO, basicConfig
from os import environ

from pylacrosseview import *

if __name__ == "__main__":
    basicConfig(level=INFO)
    ws: WeatherStation = WeatherStation()
    ws.start(environ["LACROSSE_EMAIL"], environ["LACROSSE_PASSWORD"])
    for device in ws.devices:
        for field, values in device.states().items():
            print(f"Value of {field} on {device} is {values[-1].value} {field.unit}")
