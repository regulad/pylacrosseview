from datetime import datetime


class Value:
    __slots__ = ("value", "at")

    def __init__(self, value: float, at: datetime):
        self.value: float = value
        self.at: datetime = at

    def __hash__(self):
        return hash((self.value, self.at))

    def __float__(self):
        return self.value


class Field:
    __slots__ = ("unit_enum", "name", "unit")

    def __init__(self, name: str, unit: str, unit_enum: int):
        self.name: str = name
        self.unit: str = unit
        self.unit_enum: int = unit_enum

    def __eq__(self, other):
        return self.name == other.name and self.unit == other.unit and self.unit_enum == other.unit_enum

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name


__all__ = ["Field", "Value"]
