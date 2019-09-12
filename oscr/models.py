"""
oscr.models
~~~~~~~~~~~

This module implements data models.
"""


class Account:
    def __init__(
        self, sfid=None, doid=None, prep=None, name=None, domain=None, phone=None
    ):
        self.sfid: str = sfid
        self.doid: str = doid
        self.prep: str = prep

        self.name: str = name
        self.domain: str = domain
        self.phone: str = phone


class Contact:
    def __init__(
        self,
        account=None,
        sfid=None,
        name=None,
        title=None,
        office=None,
        direct=None,
        mobile=None,
        email=None,
        rating=None,
        priority=None,
        status=None,
    ):
        self.account: str = account
        self.sfid: str = sfid

        self.name: str = name
        self.title: str = title

        self.office: str = office
        self.direct: str = direct
        self.mobile: str = mobile
        self.email: str = email

        self.rating: int = rating
        self.priority: int = priority

        self.status: str = status
