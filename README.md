# OSCR
## (The Opinionated System for Contact Retrieval)

OSCR is a Python program that automatically enriches accounts in Salesforce upon which `Enrichment_Requested__c` is `True`. It uses an algorithm to filter potential new contacts before they are loaded into Salesforce. This program uses the DiscoverOrg API to source its contact data.

### The Algorithm

This algorithm produces high-value contacts based on a twofold qualification bias (source in `oscr/bias.py`) and a quantity filter. The implementation for this algorithm can be found in `oscr.utils._filter`.

The first step is giving each contact a rating and priority, based on title and job function, respectively.

The second step is sorting the contacts based on the sum of these criteria, then doing one of two things: if the number of contacts is above 45, the top 15 are returned, but if the number of contacts is below 45, all are returned.

### Usage

To run OSCR, simply call it from the command line:

    python -m oscr

This will launch the process via the `__main__.py` module.