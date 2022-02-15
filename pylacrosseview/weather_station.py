import json
from datetime import datetime
from logging import getLogger
from typing import List, Dict

import jwt
import requests
from requests import Session

from .device import Device
from .field import Field, Value
from .location import Location

logger = getLogger(__name__)


class WeatherStation:
    def __init__(self):
        self.token = None
        self.locations = []
        self.session = Session()
        self.__devices_by_location = {}
        self.email = None
        self.password = None
        self.started = False

    def close(self):
        self.session.close()
        self.started = False

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
        self.token = self.get_token(email, password)
        self.email = email
        self.password = password
        self.init_locations()
        for location in self.locations:
            logger.info(f"Found location! {location.name} ({location.id})")
            self.init_location_devices(location)
            for device in location.devices:
                logger.info(f"Found device! {device.name} ({device.id})")
        self.started = True

    @property
    def token_expired(self):
        this_jwt = jwt.decode(self.token, options={"verify_signature": False})
        expiry_time = datetime.fromtimestamp(this_jwt['exp'])
        return expiry_time <= datetime.now()

    def refresh_token(self):
        if self.email is None or self.password is None:
            raise RuntimeError("Email and password must be set before refreshing token")
        elif self.token is None:
            raise RuntimeError("Token must be set before refreshing token")
        self.token = self.get_token(self.email, self.password)

    def get_token(self, email, password) -> str:
        logger.info("Logging in to La Crosse View...")
        url = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword"
        params: dict = {"key": "AIzaSyD-Uo0hkRIeDYJhyyIg-TvAv8HhExARIO4"}
        payload: dict = {
            "email": email,
            "returnSecureToken": True,
            "password": password
        }
        with requests.post(url, data=json.dumps(payload), params=params) as r:
            body = r.json()

            token = body.get('idToken')

            if token is None:
                raise Exception("Login Failed. Check credentials and try again")
            else:
                return token

    def init_locations(self):
        if self.token_expired:
            self.refresh_token()
        url = "https://lax-gateway.appspot.com/_ah/api/lacrosseClient/v1.1/active-user/locations"
        headers = {"Authorization": f"Bearer {self.token}"}
        with requests.get(url, headers=headers) as r:
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
        if self.token_expired:
            self.refresh_token()
        url = f"https://lax-gateway.appspot.com/_ah/api/lacrosseClient/v1.1/active-user/location/" \
              f"{location.id}/sensorAssociations"
        params = {"prettyPrint": "false"}
        headers = {"Authorization": f"Bearer {self.token}"}
        with requests.get(url, headers=headers) as r:
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
                    device_obj = Device(device_dict, self)
                    location.devices.append(device_obj)
            if not location.devices:
                logger.error(f"There are no devices for {location.name}")

    def get_device_state(self, device, start=None, end=None, time_zone="America/New_York") -> Dict[Field, List[Value]]:
        if self.token_expired:
            self.refresh_token()

        if not device.metric_names:
            return {}  # Save ourselves some time

        query_params: Dict[str, str] = {"fields": ",".join(device.metric_names), "tz": time_zone,
                                        "aggregates": "ai.ticks.1", "types": "spot"}

        if start is not None:
            query_params["from"] = start
        if end is not None:
            query_params["to"] = end

        url: str = f"https://ingv2.lacrossetechnology.com/api/v1.1/active-user/device-association/" \
                   f"ref.user-device.{device.id}/feed"

        with requests.get(url, headers={"Authorization": f"Bearer {self.token}"}, params=query_params) as r:
            if r.status_code < 200 or r.status_code >= 300:
                raise RuntimeError(f"Failed to get device state for {device.name}: {r.status_code} {r.text}")

            body = r.json()
            fields = body.get('ref.user-device.' + device.id).get('ai.ticks.1').get('fields')

            work: Dict[Field, List[Value]] = {}
            for name, data in fields.items():
                field: Field = Field(name, data["unit"], data["unit_enum"])
                values: List[Value] = []
                for value in data["values"]:
                    values.append(Value(value["s"], datetime.utcfromtimestamp(value["u"])))
                work[field] = sorted(values, key=lambda x: x.at.timestamp())
            return work


__all__ = [
    "WeatherStation"
]
