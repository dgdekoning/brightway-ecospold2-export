# -*- coding: utf-8 -*-

"""
These are the dictionary templates used when putting together the XML documents.

Each XML document is built from one 'activity_dataset_template', 1 or more
'intermediate_exchange_template' objects and 0 or more 'elementary_exchange_template'
objects.
"""


activity_dataset_template = {
    "@xmlns:xml": "http://www.w3.org/XML/1998/namespace",
    "@xmlns": "http://www.EcoInvent.org/EcoSpold02",
    "@xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
    "activityDataset": {
        "activityDescription": {
            "activity": {
                "@id": "",
                "@activityNameId": "",
                "@type": 1,
                "@specialActivityType": 0,
                "@inheritanceDepth": 0,  # Not touched
                "@energyValues": 0,  # Not touched
                "activityName": {"@xml:lang": "en", "$": ""},
            },
            "geography": {
                "@geographyId": "",
                "shortname": {"@xml:lang": "en", "$": "GLO"},
            },
            "technology": {"@technologyLevel": 3},
            "timePeriod": {
                "@startDate": "",
                "@endDate": "",
                "@isDataValidForEntirePeriod": True,
            },
            "macroEconomicScenario": {
                "@macroEconomicScenarioId": "",
                "name": {"@xml:lang": "en", "$": "Business-as-Usual"},
            }
        },
        "flowData": [],
        "modellingAndValidation": {},
        "administrativeInformation": {
            "dataEntryBy": {
                "@personId": "",
                "@personName": "",
                "@personEmail": "",
                "@isActiveAuthor": False,  # Not touched
            },
            "dataGeneratorAndPublication": {
                "@personId": "",
                "@personName": "",
                "@personEmail": "",
                "@isCopyrightProtected": True,
                "@dataPublishedIn": 0,  # Not touched
                "@accessRestrictedTo": 0,  # Not touched
            },
            "fileAttributes": {
                "@majorRelease": 1,
                "@minorRelease": 0,
                "@majorRevision": 0,
                "@minorRevision": 0,
                "@defaultLanguage": "en",
                "contextName": {"@xml:lang": "en", "$": "brightway2 ecospold2 export"},
            },
        },
    },
}


intermediate_exchange_template = {
    "@id": "",
    "@unitId": "",
    "@amount": 1.0,
    "@intermediateExchangeId": "",
    "@isCalculatedAmount": False,  # Not touched
    "@activityLinkId": "",
    "name": {"@xml:lang": "en", "$": ""},
    "unitName": {"@xml:lang": "en", "$": ""},
    "comment": {"@xml:lang": "en", "$": ""},
}


elementary_exchange_template = {
    "@id": "",
    "@unitId": "",
    "@amount": 1.0,
    "@elementaryExchangeId": "",
    "@isCalculatedAmount": False,  # Not touched
    "name": {"@xml:lang": "en", "$": ""},
    "unitName": {"@xml:lang": "en", "$": ""},
    "comment": {"@xml:lang": "en", "$": ""},
    "compartment": {
        "@subcompartmentId": "",
        "compartment": {"@xml:lang": "en", "$": ""},
        "subcompartment": {"@xml:lang": "en", "$": ""}
    },
}
