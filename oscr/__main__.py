"""
oscr.main
~~~~~~~~~

This module implements the the system's main script.
"""

from logging import getLogger, info, INFO, warning, error
from typing import Generator

from oscr.clients import DiscoverOrgClient, SalesforceClient
from oscr.utils import enrich


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
        while accounts:
            enrich(sfc, doc, next(accounts))
    except StopIteration:
        info("Account generator exhausted.")
        pass
    finally:
        del accounts


if __name__ == "__main__":
    getLogger().setLevel(INFO)

    run()
