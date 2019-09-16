"""
oscr.utils
~~~~~~~~~~

This module implements utility methods for the API.
"""

import re

from oscr.bias import TITLE_BIAS, FUNCTION_BIAS
from oscr.clients import DiscoverOrgClient, SalesforceClient
from oscr.models import Account


def enrich(sfc: SalesforceClient, doc: DiscoverOrgClient, account: Account):
    """ Enriches a given account. """
    sf_contacts: list = [c for c in sfc.get_contacts(account)]
    do_contacts: list = [c for c in doc.get_contacts(account)]

    names: list = [c.name for c in sf_contacts]
    emails: list = [c.email for c in sf_contacts]
    domains: list = [
        re.findall(r"@(\w.+)", c.email)[0] for c in sf_contacts
    ] + re.findall(
        r"^(?:https?://)?(?:[^@/\n]+@)?(?:www\.)?([^:/?\n]+)", account.domain
    )

    contacts: list = _filter(
        [
            contact
            for contact in do_contacts
            if (
                contact.email
                and contact.email != ""
                and contact.name not in names
                and contact.email not in emails
                and re.findall(r"@(\w.+)", contact.email)[0] not in domains
            )
        ]
    )

    if contacts:
        sfc.upload_contacts(account, contacts)


def _filter(contacts: list):
    """ Filters a given list of contacts for writing to Salesforce.

    This method uses the 'Scarce' selection algorithm. Documentation of
    this algorithm can be found in the `docs` section of the main OSCR repository.
    """
    for contact in contacts:
        for i, group in enumerate(TITLE_BIAS):
            for title in group:
                if title in contact.title.upper():
                    contact.rating = i
                    break

        for i, function in enumerate(FUNCTION_BIAS):
            if function in contact.title.upper():
                contact.priority = i
                break

    contacts = sorted(contacts, key=lambda c: c.rating + c.priority)
    contacts = contacts[: int(len(contacts) / 3)] if len(contacts) >= 45 else contacts
    contacts = contacts[:100] if len(contacts) > 50 else contacts

    return contacts
