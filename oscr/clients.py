"""
oscr.clients
~~~~~~~~~~~~

This module contains the `SalesforceClient` and `DiscoverOrgClient` classes.
"""

import datetime
import json
import os

import requests as rq
import simple_salesforce as ss
from selenium import webdriver

from .models import Account, Contact


class SalesforceClient:
    """ Implements the `SalesforceClient` class.

    This class contains a high-level controlled interface for interacting with the
    Salesforce API within the context of the OSCR system.
    """

    def __init__(self):
        self.api: ss.Salesforce = ss.Salesforce(
            username=os.getenv("SF_USERNAME"),
            password=os.getenv("SF_PASSWORD"),
            security_token=os.getenv("SF_TOKEN"),
            organizationId=os.getenv("SF_ORG_ID"),
        )

    def get_accounts(self):
        """ Yields a generator of all accounts where enrichment is requested. """
        sql = """
            SELECT
                Id, DSCORGPKG__DiscoverOrg_ID__c, Name, Phone, Website,
                Enrichment_Requested_By__c, Enrichment_Requested_Date__c
            FROM
                Account
            WHERE
                Enrichment_Requested__c = True
            AND
                Enrichment_Complete__c = False
        """
        records: list = self.api.query_all(sql)["records"]

        while records:
            record: dict = records.pop(0)

            yield Account(
                salesforce_id=record.get("Id", ""),
                discoverorg_id=record.get("DSCORGPKG__DiscoverOrg_ID__c", ""),
                prep=record.get("Enrichment_Requested_By__c", "0050V000006j7Jj"),
                name=record.get("Name", ""),
                domain=record.get("Website", ""),
                phone=record.get("Phone", ""),
            )

    def get_contacts(self, account: Account):
        """ Yields a generator of contacts for a given account.

        :param account: An `Account` object.
        """
        sql: str = f"""
            SELECT
                Id, Name, Title,
                Phone, MobilePhone, Email,
                Contact_Status__c
            FROM
                Contact
            WHERE
                AccountId = '{account.salesforce_id}'
        """
        records: list = self.api.query_all(sql)["records"]

        while records:
            record: dict = records.pop(0)

            yield Contact(
                account=account.salesforce_id,
                salesforce_id=record.get("Id", ""),
                name=record.get("Name", ""),
                title=record.get("Title", ""),
                office=account.phone,
                direct=record.get("Phone", ""),
                mobile=record.get("MobilePhone", ""),
                email=record.get("Email", ""),
                rating=10,
                priority=10,
                status="old",
            )

    def complete_enrichment(self, account: Account):
        """ Writes 'Enrichment_Complete__c' on a given account. """
        self.api.Account.update(account.salesforce_id, {"Enrichment_Complete__c": True})

    def upload_contacts(self, account: Account, contacts: list):
        """ Writes given contacts to a given account in Salesforce. """
        data = []
        for contact in contacts:
            name = contact.name.split()
            data.append(
                {
                    "AccountId": account.salesforce_id,
                    "OwnerId": account.prep,
                    "FirstName": name[0],
                    "LastName": name[1] if len(name) > 1 else "",
                    "Title": contact.title or "",
                    "Phone": contact.direct or "",
                    "MobilePhone": contact.mobile or "",
                    "Email": contact.email or "",
                }
            )

        try:
            self.api.bulk.Contact.insert(data)
        except ss.SalesforceError as e:
            print(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                " - CONTACT WRITE FAILURE\n"
                "* * * * * * * * * *\n"
                f"Salesforce Error: {e.message}\n"
                "* * * * * * * * * *\n"
                f"CONTACT DUMP\n"
            ) + json.dumps(data or [])
        else:
            self.complete_enrichment(account)


class DiscoverOrgClient:
    """ Implements the `DiscoverOrgClient` class.

    This class contains a high-level controlled interface for interacting with the
    DiscoverOrg API within the context of the OSCR system.
    """

    def __init__(self):
        self.base: str = "https://papi.discoverydb.com/papi"

        self.username: str = os.getenv("DO_USERNAME")
        self.password: str = os.getenv("DO_PASSWORD")
        self.key: str = os.getenv("DO_KEY")

        self.session: str = self._get_session()

    def _get_session(self):
        """ Gets a session key.

        :return session: A `str` session key.
        """
        url: str = "".join([self.base, "/login"])
        headers: dict = {"Content-Type": "application/json"}
        data: dict = {"username": self.username, "password": self.password, "partnerKey": self.key}

        response: rq.Response = rq.post(url, headers=headers, data=json.dumps(data))
        session = response.headers.get("X-AUTH-TOKEN")

        return session

    def get_contacts(self, account: Account):
        """ Yields a generator of available contacts for a given account.

        This method contains a regular expression to stop the yielding of contacts
        whose email addresses aren't on the exact domain of the account, but might
        be substrings of that domain.
        """
        response: rq.Response = rq.post(
            url="".join([self.base, "/v1/search/persons"]),
            headers={
                "X-PARTNER-KEY": self.key,
                "X-AUTH-TOKEN": self.session,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            data=json.dumps({"companyCriteria": {"websiteUrls": [account.domain]}}),
        )

        if response.status_code == 200:
            data = json.loads(response.text)
            records = data.get("content", [])
        else:
            records = []

        while records:
            record = records.pop(0)

            yield Contact(
                account=account.salesforce_id,
                salesforce_id="",
                name=record.get("fullName"),
                title=record.get("title"),
                office=account.phone,
                direct=record.get("officeTelNumber"),
                mobile=record.get("mobileTelNumber"),
                email=record.get("email"),
                rating=10,
                priority=10,
                status="new",
            )


class LinkedInClient:
    """ Implements the `LinkedInClient` class.

    This class provides a high-level interface for collecting data
    via a system of web scrapers/drivers.
    """

    def __init__(self, username: str = None, password: str = None):
        self.driver: webdriver = webdriver.Chrome()

        username: str = username or os.getenv("LI_USERNAME")
        password: str = password or os.getenv("LI_PASSWORD")
        self._login(username, password)

    def _login(self, username: str, password: str):
        """ Logs into LinkedIn via a Selenium ChromeDriver.

        :param username: A valid `str` LinkedIn username.
        :param password: A valid `str` LinkedIn password.
        """
        self.driver.get("https://www.linkedin.com/login")

        username_input = self.driver.find_element_by_id("username")
        password_input = self.driver.find_element_by_id("password")

        username_input.send_keys(username)
        password_input.send_keys(password)

        password_input.submit()
