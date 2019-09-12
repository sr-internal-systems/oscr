"""
oscr.clients
~~~~~~~~~~~~

This module contains the `SalesforceClient` and `DiscoverOrgClient` classes.
"""

import datetime
import json
import os
import uuid

import requests as rq
import simple_salesforce as ss

from oscr.models import Account, Contact


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
                sfid=record.get("Id", ""),
                doid=record.get("DSCORGPKG__DiscoverOrg_ID__c", ""),
                prep=record.get("Enrichment_Requested_By__c", "0050V000006j7Jj"),
                name=record.get("Name", ""),
                domain=record.get("Website", ""),
                phone=record.get("Phone", ""),
            )

    def get_contacts(self, account: Account):
        """ Yields a generator of contacts for a given account. """
        sql: str = f"""
            SELECT
                Id, Name, Title,
                Phone, MobilePhone, Email,
                Contact_Status__c
            FROM
                Contact
            WHERE
                AccountId = '{account.sfid}'
        """
        records: list = self.api.query_all(sql)["records"]

        while records:
            record: dict = records.pop(0)

            yield Contact(
                account=account.sfid,
                sfid=record.get("Id", ""),
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
        self.api.Account.update(account.sfid, {"Enrichment_Complete__c": True})

    def upload_contacts(self, account: Account, contacts: list):
        """ Writes given contacts to a given account in Salesforce. """
        for contact in contacts:
            for f in contact.get_fields():
                if getattr(contact, f.name) is None:
                    setattr(contact, f.name, "")

        data = []
        for contact in contacts:
            name = contact.name.split()
            data.append(
                {
                    "AccountId": account.sfid,
                    "OwnerId": account.prep,
                    "FirstName": name[0],
                    "LastName": name[1] if len(name) > 1 else "",
                    "Title": contact.title,
                    "Phone": contact.direct,
                    "MobilePhone": contact.mobile,
                    "Email": contact.email,
                }
            )

        with open(f"~/oscr_dumps/{account.sfid}.json", "w+") as f:
            raw = json.dumps(data)
            f.write(raw)

        try:
            self.api.bulk.Contact.insert(data)
        except ss.SalesforceError as e:
            log: str = (
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                " - CONTACT WRITE FAILURE\n"
                "* * * * * * * * * *\n"
                f"Salesforce Error: {e.message}\n"
                "* * * * * * * * * *\n"
                f"CONTACT DUMP\n"
            ) + json.dumps(data or [])

            with open(f"~/oscr_logs/{uuid.uuid4()}", "w+") as f:
                f.write(log)
        else:
            self.complete_enrichment(account)


class DiscoverOrgClient:
    """ Implements the `DiscoverOrgClient` class.

    This class contains a high-level controlled interface for interacting with the
    DiscoverOrg API within the context of the OSCR system.
    """

    def __init__(self):
        self.base: str = "https://papi.discoverydb.com/papi"

        self.username: str = os.getenv("DO_KEY")
        self.password: str = os.getenv("DO_PASSWORD")
        self.key: str = os.getenv("DO_USERNAME")

        self.session: str = self._get_session()

    def _get_session(self):
        """ Gets a session key.

        :return `session`: A `str` session key.
        """
        url: str = "".join([self.base, "/login"])
        headers: dict = {"Content-Type": "application/json"}
        data: dict = {
            "username": self.username,
            "password": self.password,
            "partnerKey": self.key,
        }

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
                account=account.sfid,
                sfid="",
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
