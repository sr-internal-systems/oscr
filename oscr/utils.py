"""
oscr.utils
~~~~~~~~~~

This module implements utility methods for the API.
"""

import re
from logging import info, error

from oscr.bias import FUNCTION_BIAS, TITLE_BIAS
from oscr.clients import DiscoverOrgClient, SalesforceClient
from oscr.models import Account


def enrich(sfc: SalesforceClient, doc: DiscoverOrgClient, account: Account) -> None:
    """ Enriches a given account. """
    raw_info = doc.get_company_info(account)
    info_str = format_company_info(raw_info) if raw_info else None

    if info_str:
        sfc.upload_info(account, info)

    sf_contacts: list = [c for c in sfc.get_contacts(account)]
    do_contacts: list = [c for c in doc.get_contacts(account)]

    names: list = [c.name for c in sf_contacts]
    emails: list = [c.email for c in sf_contacts]
    domains: list = [
        re.findall(r"@(\w.+)", c.email)[0] for c in sf_contacts if c.email
    ] + re.findall(
        r"^(?:https?://)?(?:[^@/\n]+@)?(?:www\.)?([^:/?\n]+)", account.domain or ""
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

    sfc.complete_enrichment(account)


def _filter(contacts: list) -> list:
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

    contacts: list = sorted(contacts, key=lambda c: c.rating + c.priority)
    contacts: list = contacts[: int(len(contacts) / 3)] if len(
        contacts
    ) >= 45 else contacts
    contacts: list = contacts[:100] if len(contacts) > 50 else contacts

    return contacts


def format_company_info(info_dict):
    """ Produces a field-friendly string from a dictionary of company data. """
    overview: str = info_dict.get("overview")
    size: str = info_dict.get("numEmployees")
    revenue: str = info_dict.get("revenues")
    location: dict = info_dict.get("location")
    headquarters: str = ", ".join(
        [
            {location.get("city")},
            {location.get("stateProvinceRegion")},
            {location.get("countryName")},
        ]
    )

    info_str: str = "\n".join(
        [
            f"Overview: {overview}",
            f"Size: {size}",
            f"Revenue: {revenue}",
            f"Headquarters: {headquarters}",
        ]
    )

    return info_str
