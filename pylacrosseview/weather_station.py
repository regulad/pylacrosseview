import json
from logging import getLogger
from typing import List

import requests

from .device import Device
from .location import Location

logger = getLogger(__name__)


class WeatherStation:
    def __init__(self):
        self.token = None
        self.locations = []
        self.__type_names = []
        self.__devices_by_location = {}

    @property
    def type_names(self):
        return self.__type_names

    @type_names.setter
    def type_names(self, type_names):
        self.__type_names = type_names

    @property
    def devices_by_location(self):
        return self.__devices_by_location

    @devices_by_location.setter
    def devices_by_location(self, devices_by_location):
        self.__devices_by_location = devices_by_location

    @property
    def devices(self) -> List[Device]:
        devices = []
        for location in self.locations:
            devices.extend(location.devices)
        return devices

    def start(self, email, password):
        self.login(email, password)
        self.init_locations()
        for location in self.locations:
            logger.info(f"Found location! {location.name} ({location.id})")
            self.init_location_devices(location)
            for device in location.devices:
                logger.info(f"Found device! {device.name} ({device.id})")

    def login(self, email, password):
        logger.info("Logging in to LacrosseView...")
        url = "https://www.googleapis.com/" \
              "identitytoolkit/v3/relyingparty/verifyPassword?" \
              "key=AIzaSyD-Uo0hkRIeDYJhyyIg-TvAv8HhExARIO4"
        payload = {
            "email": email,
            "returnSecureToken": True,
            "password": password
        }
        r = requests.post(url, data=json.dumps(payload))
        body = r.json()
        self.token = body.get('idToken')

        if self.token is None:
            raise Exception("Login Failed. Check credentials and try again")

    def init_locations(self):
        url = "https://lax-gateway.appspot.com/" \
              "_ah/api/lacrosseClient/v1.1/active-user/locations"
        headers = {"Authorization": "Bearer " + self.token}
        r = requests.get(url, headers=headers)
        if r.status_code < 200 or r.status_code >= 300:
            raise ConnectionError("failed to get locations ()".
                                  format(r.status_code))
        body = r.json()
        for loc in body.get('items'):
            self.locations.append(Location(loc))
        if not self.locations:
            raise Exception("Unable to get account locations")
        return True

    def init_location_devices(self, location):
        url = "https://lax-gateway.appspot.com/" \
              "_ah/api/lacrosseClient/v1.1/active-user/location/" \
              + location.id \
              + "/sensorAssociations?prettyPrint=false"
        headers = {"Authorization": "Bearer " + self.token}
        r = requests.get(url, headers=headers)
        body = r.json()
        if body:
            devices = body.get('items')
            for device in devices:
                sensor = device.get('sensor')
                device_name = device.get('name').lower().replace(' ', '_')
                device_dict = {
                    "device_name": device_name,
                    "device_id": device.get('id'),
                    "sensor_type_name": sensor.get('type').get('name'),
                    "sensor_id": sensor.get('id'),
                    "sensor_field_names": [x for x in sensor.get('fields')
                                           if x != "NotSupported"],
                    "last_timestamp_written": None,
                    "location": location}
                device_obj = Device(device_dict, self.token)
                location.devices.append(device_obj)
        if not location.devices:
            logger.error(f"There are no devices for {location.name}")


__all__ = [
    "WeatherStation"
]
