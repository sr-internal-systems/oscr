# OSCR
## (The Opinionated System for Contact Retrieval)

OSCR is a Python program that automatically enriches accounts in Salesforce upon which `Enrichment_Requested__c` is `True`. It uses an algorithm to filter potential new contacts before they are loaded into Salesforce. This program uses the DiscoverOrg API to source its contact data.

### Prerequisites

In order for OSCR to run on a Salesforce instance, it must have some custom fields built in.
The following table outlines those requirements.

| Object  | Field Name                | Field API Name               | Data Type | Requirements                                              |
|---------|---------------------------|------------------------------|-----------|-----------------------------------------------------------|
| Account | Enrichment Requested      | Enrichment_Requested__c      | Checkbox  |                                                           |
| Account | Enrichment Requested By   | Enrichment_Requested_By__c   | Text(55)  | Must capture the user ID of whoever requested enrichment. |
| Account | Enrichment Requested Date | Enrichment_Requested_Date__c | Date/Time |                                                           |
| Account | Enrichment Completed      | Enrichment_Completed__c      | Checkbox  |                                                           |
| Account | Enrichment Completed By   | Enrichment_Completed_By__c   | Text(55)  | Must capture the user ID of the user of the API.          |
| Account | Enrichment Completed Date | Enrichment_Completed_Date__c | Date/Time |                                                           |

### Program Usage

To run OSCR, simply call it from the command line:

    python -m oscr

This will launch the process via the `__main__.py` module.

### The Algorithm

This algorithm produces high-value contacts based on a twofold qualification bias (source in `oscr/bias.py`) and a quantity filter. The implementation for this algorithm can be found in `oscr.utils._filter`.

The first step is giving each contact a rating and priority, based on title and job function, respectively.

The second step is sorting the contacts based on the sum of these criteria, then doing one of two things: if the number of contacts is above 45, the top 15 are returned, but if the number of contacts is below 45, all are returned.