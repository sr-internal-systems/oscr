"""
oscr.models
~~~~~~~~~~~

This module implements dataclass models for the system.
"""

from dataclasses import asdict, dataclass, fields


@dataclass
class Account:
    sfid: str
    doid: str
    prep: str

    name: str
    domain: str
    phone: str

    def get_dict(self):
        return asdict(self)

    def get_fields(self):
        return fields(self)


@dataclass
class Contact:
    account: str
    sfid: str

    name: str
    title: str

    office: str
    direct: str
    mobile: str
    email: str

    rating: int
    priority: int

    status: str

    def get_dict(self):
        return asdict(self)

    def get_fields(self):
        return fields(self)
