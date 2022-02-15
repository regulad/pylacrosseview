from typing import List, Dict

from .field import Field, Value


class Device:
    def __init__(self, device_dict, weather_station):
        self.name = device_dict.get('device_name')
        self.id = device_dict.get('device_id')
        self.sensor_type = device_dict.get('sensor_type_name')
        self.sensor_id = device_dict.get('sensor_id')
        self.metric_names = device_dict.get('sensor_field_names')
        self.weather_station = weather_station

    def __str__(self):
        return self.name

    def states(self, start=None, end=None, time_zone="America/New_York") -> Dict[Field, List[Value]]:
        return self.weather_station.get_device_state(self, start, end, time_zone)
