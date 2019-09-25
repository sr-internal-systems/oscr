"""
oscr.main
~~~~~~~~~

This module implements the the system's main script.
"""

from typing import Iterator

from oscr.clients import DiscoverOrgClient, SalesforceClient
from oscr.utils import enrich


def run():
    """ Collects and enriches accounts.

    This method contains a mechanism to remove any duplicate contacts
    from DiscoverOrg that may already exist in Salesforce. It also calls on the
    method that sorts/cleans the contact list before it is written to Salesforce.
    """
    sfc: SalesforceClient = SalesforceClient()
    doc: DiscoverOrgClient = DiscoverOrgClient()

    accounts: Iterator = sfc.get_accounts()

    try:
        while accounts:
            enrich(sfc, doc, next(accounts))
    except StopIteration:
        pass
    finally:
        del accounts


if __name__ == "__main__":
    run()
