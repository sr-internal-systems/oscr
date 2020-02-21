"""
oscr.models
~~~~~~~~~~~

This module implements data models.
"""

from dataclasses import dataclass


@dataclass
class Account:
    """ Model an `Account` object that parallels some Salesforce fields. """

    salesforce_id: str
    discoverorg_id: str
    prep: str
    name: str
    domain: str
    phone: str


@dataclass
class Contact:
    """ Model a `Contact` object that parallels some Salesforce fields. """

    account: str
    salesforce_id: str

    name: str
    title: str

    office: str
    direct: str
    mobile: str
    email: str

    rating: int
    priority: int

    status: str
