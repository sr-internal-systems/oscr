"""
oscr.clients.discoverorg
~~~~~~~~~~~~~~~~~~~~~~~~

This module contains a high-level DiscoverOrg API client class.
"""

import json
import os
import time
from logging import info, warning

from oscr.models import Account, Contact

import requests as rq


class DiscoverOrgClient:
    """ Implement the `DiscoverOrgClient` class.

    This class contains a high-level controlled interface for interacting with the
    DiscoverOrg API within the context of the OSCR system.

    It requires the presence of a username, password, and partner key in order to
    start a session with the API. Those values must be stored in environment variables
    `DO_USERNAME`, `DO_PASSWORD`, and `DO_KEY`, respectively.
    """

    def __init__(self):
        self.base: str = "https://papi.discoverydb.com/papi"

        self.username: str = os.getenv("DO_USERNAME")
        self.password: str = os.getenv("DO_PASSWORD")
        self.key: str = os.getenv("DO_KEY")

        self.session: str = self._get_session()

    def _get_session(self) -> str:
        """ Get a session key.

        :return: A `str` session key.
        """
        url: str = "".join([self.base, "/login"])
        headers: dict = {"Content-Type": "application/json"}
        data: dict = {
            "username": self.username,
            "password": self.password,
            "partnerKey": self.key,
        }

        response: rq.Response = rq.post(url, headers=headers, data=json.dumps(data))

        session: str = response.headers.get("X-AUTH-TOKEN")

        return session

    def get_company_info(self, account: Account) -> str:
        """ Get company information for a given account. 
        
        This method retrieves the following fields:

            Overview
            Headquarters
            Company Size
            Revenue
        
        These values are formatted into a Salesforce field-friendly string
        by a separate utility method.
        
        :param account: An `Account` object.
        """
        url: str = "".join([self.base, "/v1/search/companies"])
        headers: dict = {
            "X-PARTNER-KEY": self.key,
            "X-AUTH-TOKEN": self.session,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        data: str = json.dumps(
            {
                "companyCriteria": {
                    "queryString": account.name,
                    "queryStringApplication": ["NAME"],
                    "websiteUrls": [account.domain],
                }
            }
        )

        response: rq.Response = rq.post(url, headers=headers, data=data)

        breakpoint

        if response.status_code == 200:
            data: dict = json.loads(response.text)
            records: list = data.get("content", [])
        elif response.status_code == 429:
            wait = int(response.headers.get("X-Rate-Limit-Reset")) - time.time()
            time.sleep(int(wait))
            self.get_company_info(account)
        else:
            warning(f"Couldn't retrieve company info records for {account.name}.")
            records: list = []

        if len(records) > 0:
            return records[0]
        else:
            return None

    def get_contacts(self, account: Account) -> Contact:
        """ Yield a generator of available contacts for a given account.

        This method contains a regular expression to stop the yielding of contacts
        whose email addresses aren't on the exact domain of the account, but might
        be substrings of that domain.

        :param account: An `Account` object.
        """
        base: str = "".join([self.base, "/v1/search/persons"])
        headers: dict = {
            "X-PARTNER-KEY": self.key,
            "X-AUTH-TOKEN": self.session,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        body: str = json.dumps({"companyCriteria": {"websiteUrls": [account.domain]}})
        page = 0

        records: list = []
        while True:
            url: str = f"{base}?pageNumber={page}"
            response: rq.Response = rq.post(url=url, headers=headers, data=body)

            if response.status_code == 200:
                data: dict = json.loads(response.text)
                records.extend(data.get("content", []))

                if data["last"] is False:
                    page += 1
                    continue
                else:
                    break
            elif response.status_code == 429:
                wait = int(response.headers.get("X-Rate-Limit-Reset")) - time.time()
                time.sleep(int(wait))
                continue
            else:
                warning(f"Couldn't retrieve contact records for {account.name}.")
                break

        while records:
            record: dict = records.pop(0)

            yield Contact(
                account=account.salesforce_id,
                salesforce_id="",
                name=record.get("fullName", ""),
                title=record.get("title", ""),
                office=account.phone,
                direct=record.get("officeTelNumber", ""),
                mobile=record.get("mobileTelNumber", ""),
                email=record.get("email", ""),
                rating=10,
                priority=10,
                status="new",
            )
