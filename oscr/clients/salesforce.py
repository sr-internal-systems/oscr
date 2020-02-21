"""
oscr.clients.salesforce
~~~~~~~~~~~~~~~~~~~~~~~

This module contains a high-level Salesforce API client class.
"""

import os
from logging import info, error
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
        info("Account records retrieved.")

        while records:
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

    def complete_enrichment(self, account: Account) -> None:
        """ Write 'Enrichment_Complete__c' on a given account. 
        
        :param account: An `Account` object.
        """
        self.api.Account.update(account.salesforce_id, {"Enrichment_Complete__c": True})
        info(f"Enrichment completed for {account.name}.")

    def upload_notes(self, account: Account, company_info: str, summary: str) -> None:
        """ Write a company info string to a given account. 
        
        :param account: An `Account` object.
        :param company_info: A `str` of company info generated by 
                             the `format_company_info` utility function.
        :param summary: An `str` enrichment summary generated by the
                        `format_enrichment_summary` utility function.
        """
        notes: str = "<br><br>".join([company_info, summary])

        self.api.Account.update(account.salesforce_id, {"Notes__c": notes})
        info(f"Company info uploaded for {account.name}.")

    def upload_contacts(self, account: Account, contacts: list) -> None:
        """ Write given contacts to a given account. 
        
        :param account: An `Account` object.
        :param contacts: A `list` of `Contact` objects.
        """
        data: list = []
        for contact in contacts:
            name: list = contact.name.split()
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
            error(f"Contact write failure for {account.name}. {e.message}")
        else:
            info(f"Contacts uploaded for {account.name}.")
            self.complete_enrichment(account)

