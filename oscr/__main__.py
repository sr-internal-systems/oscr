"""
oscr.main
~~~~~~~~~

This module implements the the system's main script.
"""

from logging import getLogger, info, INFO
from typing import Generator

from oscr.utils import enrich
from oscr.clients.discoverorg import DiscoverOrgClient
from oscr.clients.salesforce import SalesforceClient


def run():
    """ Collects and enriches accounts.

    This method contains a mechanism to remove any duplicate contacts
    from DiscoverOrg that may already exist in Salesforce. It also calls on the
    method that sorts/cleans the contact list before it is written to Salesforce.
    """
    info("Initiating clients.")
    sfc: SalesforceClient = SalesforceClient()
    doc: DiscoverOrgClient = DiscoverOrgClient()

    info("Collecting accounts.")
    accounts: Generator = sfc.get_accounts()

    try:
        info("Enriching accounts.")
        completed_contacts = []
        completed_accounts = []
        while accounts:
            account = next(accounts)
            contacts, company_info, summary = enrich(sfc, doc, account)

            completed_contacts.extend(contacts)

            account.notes: str = "<br><br>".join([company_info, summary])
            completed_accounts.append(account)

    except StopIteration:
        info("Uploading contacts.")
        sfc.upload_contacts(completed_contacts)
        sfc.complete_enrichment(completed_accounts)
        pass
    finally:
        del accounts


if __name__ == "__main__":
    getLogger().setLevel(INFO)

    run()
