from datetime import datetime
from typing import List, Dict

import requests

from .field import Field, Value


class Device:
    def __init__(self, device_dict, feed_token):
        self.name = device_dict.get('device_name')
        self.id = device_dict.get('device_id')
        self.sensor_type = device_dict.get('sensor_type_name')
        self.sensor_id = device_dict.get('sensor_id')
        self.metric_names = device_dict.get('sensor_field_names')
        self.token = feed_token

    def __str__(self):
        return self.name

    def states(self, start=None, end=None, time_zone="America/New_York") -> Dict[Field, List[Value]]:
        if not self.metric_names:
            return {}  # Save ourselves some time

        query_params: Dict[str, str] = {"fields": ",".join(self.metric_names), "tz": time_zone,
                                        "aggregates": "ai.ticks.1", "types": "spot"}

        if start is not None:
            query_params["from"] = start
        if end is not None:
            query_params["to"] = end

        url: str = f"https://ingv2.lacrossetechnology.com/api/v1.1/active-user/device-association/" \
                   f"ref.user-device.{self.id}/feed"

        with requests.get(url, headers={"Authorization": f"Bearer {self.token}"}, params=query_params) as r:
            if r.status_code < 200 or r.status_code >= 300:
                raise RuntimeError("HTTP Issue")

            body = r.json()
            fields = body.get('ref.user-device.' + self.id).get('ai.ticks.1').get('fields')

            work: Dict[Field, List[Value]] = {}
            for name, data in fields.items():
                field: Field = Field(name, data["unit"], data["unit_enum"])
                values: List[Value] = []
                for value in data["values"]:
                    values.append(Value(value["s"], datetime.utcfromtimestamp(value["u"])))
                work[field] = sorted(values, key=lambda x: x.at.timestamp())
            return work
