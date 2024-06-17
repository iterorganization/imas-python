from enum import Enum
from typing import Iterable, List, Type
from xml.etree.ElementTree import fromstring

from imaspy import dd_zip


class IDSIdentifier(Enum):
    def __new__(self, value: int, description: str):
        obj = object.__new__(self)
        obj._value_ = value
        return obj

    def __init__(self, value: int, description: str) -> None:
        self.index = value
        """Unique index for this identifier value."""
        self.description = description
        """Description for this identifier value."""

    @classmethod
    def from_xml(cls, identifier_name, xml) -> Type["IDSIdentifier"]:
        element = fromstring(xml)
        enum_values = {}
        for int_element in element.iterfind("int"):
            name = int_element.get("name")
            value = int_element.text
            description = int_element.get("description")
            enum_values[name] = (int(value), description)
        # Create the enumeration
        enum = cls(
            identifier_name,
            enum_values,
            module=__name__,
            qualname=f"{__name__}.{identifier_name}",
        )
        enum.__doc__ = element.find("header").text
        return enum


class IDSIdentifiers:

    def __getattr__(self, name) -> Type[IDSIdentifier]:
        if name not in self.identifiers:
            raise AttributeError(f"Unknown identifier name: {name}")
        xml = dd_zip.get_identifier_xml(name)
        identifier = IDSIdentifier.from_xml(name, xml)
        setattr(self, name, identifier)
        return identifier

    def __getitem__(self, name) -> Type[IDSIdentifier]:
        if name not in self.identifiers:
            raise KeyError(f"Unknown identifier name: {name}")
        return getattr(self, name)

    def __dir__(self) -> Iterable[str]:
        return sorted(set(object.__dir__(self)).union(self.identifiers))

    @property
    def identifiers(self) -> List[str]:
        return dd_zip.dd_identifiers()


identifiers = IDSIdentifiers()
