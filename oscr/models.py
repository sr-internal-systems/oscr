"""
oscr.models
~~~~~~~~~~~

This module implements data models.
"""


class Account:
    def __init__(self, salesforce_id=None, discoverorg_id=None, prep=None, name=None, domain=None, phone=None):
        self.salesforce_id: str = salesforce_id
        self.discoverorg_id: str = discoverorg_id
        self.prep: str = prep

        self.name: str = name
        self.domain: str = domain
        self.phone: str = phone


class Contact:
    def __init__(
        self,
        account=None,
        salesforce_id=None,
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
        self.salesforce_id: str = salesforce_id

        self.name: str = name
        self.title: str = title

        self.office: str = office
        self.direct: str = direct
        self.mobile: str = mobile
        self.email: str = email

        self.rating: int = rating
        self.priority: int = priority

        self.status: str = status
