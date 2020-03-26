"""
oscr.clients.salesforce
~~~~~~~~~~~~~~~~~~~~~~~

This module contains a high-level Salesforce API client class.
"""

import os
from logging import error
from typing import Generator

from oscr.models import Account, Contact

import simple_salesforce as ss


class SalesforceClient:
    """ Implement the `SalesforceClient` class.

    This class contains a high-level controlled interface for interacting with the
    Salesforce API within the context of the OSCR system.

    It requires the presence of a username, password, token, and organization ID
    in order to authenticate properly with the API. Those values must be stored in 
    environment variables `SF_USERNAME`, `SF_PASSWORD`, `SF_TOKEN`, and `SF_ORG_ID`
    respectively.
    """

    def __init__(self):
        self.api: ss.Salesforce = ss.Salesforce(
            username=os.getenv("SF_USERNAME"),
            password=os.getenv("SF_PASSWORD"),
            security_token=os.getenv("SF_TOKEN"),
            organizationId=os.getenv("SF_ORG_ID"),
            domain="test",
        )

    def get_accounts(self) -> Generator[Account, None, None]:
        """ Yield a generator of all accounts where enrichment is requested. 
        
        This method, if no `Enrichment_Requested_By__c` value is present,
        requires the presence of a default user value to fulfill the contact
        ownership field in the environment variable `SF_DEFAULT_USER`.
        """
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

        count = 0
        while records and count <= 100:
            record: dict = records.pop(0)

            yield Account(
                salesforce_id=record.get("Id", ""),
                discoverorg_id=record.get("DSCORGPKG__DiscoverOrg_ID__c", ""),
                prep=record.get(
                    "Enrichment_Requested_By__c", os.getenv("SF_DEFAULT_USER")
                ),
                name=record.get("Name", ""),
                domain=record.get("Website", ""),
                phone=record.get("Phone", ""),
            )

            count += 1

    def get_contacts(self, account: Account) -> Generator[Contact, None, None]:
        """ Yield a generator of contacts for a given account.

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

    def upload_contacts(self, data: list):
        """ Write all new contacts to Salesforce.
        
        :param: A `list` of formatted contact data `dict` objects.
        """
        try:
            self.api.bulk.Contact.insert(data)
        except ss.SalesforceError as e:
            error(f"Contact write failure. {e.message}")

    def complete_enrichment(self, accounts: list) -> None:
        """ Write `Notes__c` and  `Enrichment_Complete__c` on given accounts. 
        
        :param account: A `list` of `Account` objects.
        """
        data = []
        for account in accounts:
            data.append(
                {
                    "Id": str(account.salesforce_id),
                    "Notes__c": account.notes,
                    "Enrichment_Complete__c": True,
                }
            )

        try:
            self.api.bulk.Account.update(data)
        except ss.SalesforceError as e:
            error(f"Account write failure. {e.message}")
