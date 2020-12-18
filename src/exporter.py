# -*- coding: utf-8 -*-
import copy
import datetime
import json
from pathlib import Path
from typing import NamedTuple, List
import uuid
from xml.etree.ElementTree import ElementTree
import xmlschema

import brightway2 as bw
from bw2data.backends.peewee import Activity, Exchange
from bw2io.extractors.ecospold2 import ACTIVITY_TYPES
from bw2io.utils import activity_hash

from .dictionary_templates import *
from .strategies import alter_uuids_template, match_flows_uuids
from .utils import seeded_uuid


class ExchangeTemplate(NamedTuple):
    exchange: Exchange
    flow_id: str

    @property
    def id_is_equal(self) -> bool:
        return self.exchange.get("flow") == self.flow_id

    @property
    def type(self) -> str:
        return self.exchange.get("type", "technosphere")

    @classmethod
    def from_exchange(cls, exchange: Exchange) -> 'ExchangeTemplate':
        return cls(
            exchange,
            seeded_uuid("".join(["flow", activity_hash(exchange.input)]))
        )


class ActivityTemplate(NamedTuple):
    activity: Activity
    activity_id: str
    exchanges: List[ExchangeTemplate]

    @property
    def id_is_equal(self) -> bool:
        return self.activity.get("activity") == self.activity_id

    @property
    def key(self) -> tuple:
        return self.activity.key

    @property
    def production_flow_id(self) -> str:
        exc = next(e for e in self.exchanges if e.type == "production")
        return exc.flow_id

    @classmethod
    def from_activity(cls, activity: Activity) -> 'ActivityTemplate':
        exchanges = [
            ExchangeTemplate.from_exchange(exc)
            for exc in activity.exchanges()
        ]
        return cls(
            activity,
            seeded_uuid(activity_hash(activity)),
            exchanges,
        )


ACTIVITY_TYPES_REV = {v: k for k, v in ACTIVITY_TYPES.items()}
TYPES = {
    "process": 1,
    "system terminated": 2,
}


def ecospold2_dict_from_activity(activity: ActivityTemplate) -> dict:
    """Construct activityDataset dictionary from the given Activity object."""
    data = copy.deepcopy(activity_dataset_template)
    act = activity.activity
    name = act.get("name", "")
    location = act.get("location", "GLO")
    economic_scenario = act.get("macro economic scenario", "Business-as-Usual")
    if "authors" in act:
        entry = act.get("authors", {}).get("data entry", {})
        generator = act.get("authors", {}).get("data generator", {})
    else:
        entry = {"name": "John Doe", "email": "john.doe@unknown.com"}
        generator = {"name": "John Doe", "email": "john.doe@unknown.com"}

    # Now extract all the data from the given activity.
    # - Activity description
    description = data["activityDataset"]["activityDescription"]
    # If we can't find the actual uuid, use the random one.
    description["activity"]["@id"] = act.get("activity", seeded_uuid(activity_hash(act)))
    description["activity"]["@activityNameId"] = seeded_uuid(name)
    description["activity"]["@type"] = TYPES[act.get("type", "process")]
    description["activity"]["@specialActivityType"] = ACTIVITY_TYPES_REV[act.get("activity type", "ordinary transforming activity")]
    description["activity"]["activityName"]["$"] = name
    description["geography"]["@geographyId"] = seeded_uuid(location)
    description["geography"]["shortname"]["$"] = location
    description["technology"]["@technologyLevel"] = act.get("technology level", 3)
    description["timePeriod"]["@startDate"] = act.get("start date", str(datetime.date(2010, 1, 1)))
    description["timePeriod"]["@endDate"] = act.get("end date", str(datetime.date(2020, 12, 31)))
    description["timePeriod"]["@isDataValidForEntirePeriod"] = act.get("data validity", True)
    description["macroEconomicScenario"]["@macroEconomicScenarioId"] = seeded_uuid(economic_scenario)
    description["macroEconomicScenario"]["name"]["$"] = economic_scenario

    # - Flow data
    data["activityDataset"]["flowData"] = build_flows_from_exchanges(activity)

    # - Administrative information
    administrative = data["activityDataset"]["administrativeInformation"]
    administrative["dataEntryBy"]["@personId"] = seeded_uuid(entry.get("name"))
    administrative["dataEntryBy"]["@personName"] = entry.get("name")
    administrative["dataEntryBy"]["@personEmail"] = entry.get("email")
    administrative["dataGeneratorAndPublication"]["@personId"] = seeded_uuid(generator.get("name"))
    administrative["dataGeneratorAndPublication"]["@personName"] = generator.get("name")
    administrative["dataGeneratorAndPublication"]["@personEmail"] = generator.get("email")
    administrative["dataGeneratorAndPublication"]["@isCopyrightProtected"] = True

    return data


def build_flows_from_exchanges(activity: ActivityTemplate) -> dict:
    """ Prepare flowType dictionary based on exchanges present."""
    flows = {
        "intermediateExchange": [
            ecospold2_dict_from_exchange(exc.exchange)
            for exc in activity.exchanges
            if exc.type in {"production", "technosphere", "substitution"}
        ]
    }

    if len(activity.activity.biosphere()) > 0:
        flows["elementaryExchange"] = [
            ecospold2_dict_from_exchange(exc.exchange)
            for exc in activity.exchanges if exc.type == "biosphere"
        ]

    # Now also parse possible parameters
    # if "parameters" in activity:
    #     flows["parameter"] = {}

    return flows


def ecospold2_dict_from_exchange(exchange: Exchange) -> dict:
    """Construct a 'flowType' object from the given exchange object."""
    exc_type = exchange.get("type", "technosphere")
    random_id = str(uuid.uuid4())
    input_flow = exchange.input
    unit = input_flow.get("unit", "unit")
    if "reference product" in input_flow:
        name = input_flow.get("reference product")
    elif "name" in exchange:
        name = exchange.get("name")
    else:
        name = input_flow.get("name")

    if exc_type == "biosphere":
        flow = copy.deepcopy(elementary_exchange_template)
    else:
        flow = copy.deepcopy(intermediate_exchange_template)

    flow["@id"] = random_id
    flow["@unitId"] = seeded_uuid(unit)
    flow["@amount"] = float(exchange.get("amount", 0))
    flow["name"]["$"] = name
    flow["unitName"]["$"] = unit
    flow["comment"]["$"] = exchange.get("comment", "")

    if exc_type == "biosphere":
        return finish_elementary_exchange(exchange, flow)
    return finish_intermediate_exchange(exchange, flow)


def finish_elementary_exchange(exc: Exchange, flow: dict) -> dict:
    """Finalize the elementary exchange by adding specific fields."""
    flow_id = exc.get("flow", str(uuid.uuid4()))
    in_flow = exc.input
    categories = in_flow.get("categories", ("", ""))
    flow_type = in_flow.get("type")

    flow["@elementaryExchangeId"] = flow_id
    flow["compartment"]["@subcompartmentId"] = in_flow.get("code")
    flow["compartment"]["compartment"]["$"] = categories[0]
    flow["compartment"]["subcompartment"]["$"] = categories[1] if len(categories) > 1 else "unspecified"
    direction = "inputGroup" if flow_type == "natural resource" else "outputGroup"
    flow[direction] = 4
    return flow


def finish_intermediate_exchange(exc: Exchange, flow: dict) -> dict:
    """Finalize the intermediate exchange by adding specific fields."""
    flow_id = exc.get("flow")
    in_flow = exc.input

    flow["@intermediateExchangeId"] = flow_id
    flow["@activityLinkId"] = in_flow.get("activity", seeded_uuid(activity_hash(in_flow)))
    if exc.get("type") == "production":
        flow["outputGroup"] = 0
    else:
        flow["inputGroup"] = 5
    return flow


class Ecospold2Manager(object):
    DEFAULT_NAMESPACES = {
        'xml': 'http://www.w3.org/XML/1998/namespace',
        '': 'http://www.EcoInvent.org/EcoSpold02',
        'xsd': 'http://www.w3.org/2001/XMLSchema',
    }

    def __init__(self, schema_dir: Path) -> None:
        # Read in the EcoSpold2 schema files using the base_dir method
        top_schema = schema_dir / "EcoSpold02.xsd"
        assert top_schema.exists(), "Cannot find ecospold2 schema files."
        with top_schema.open(encoding="utf-8") as infile:
            self.schemas = xmlschema.XMLSchema(infile, base_url=str(schema_dir))

        self.data: List[ActivityTemplate] = []

    @classmethod
    def initialize(cls, schema_path: Path, db_name: str) -> 'Ecospold2Manager':
        """Construct the manager with prepared schema files and convert the
        database into set of valid XML template objects.
        """
        obj = cls(schema_path)
        assert db_name in bw.databases, "Given db_name must exist as database"
        obj.data = cls.process_database(db_name)
        return obj

    @staticmethod
    def process_database(db_name) -> List[ActivityTemplate]:
        """Build the dataset list and apply specific 'export' strategies
        to ensure that both the XML is valid and brightway can import
        the data again.
        """
        data = [
            ActivityTemplate.from_activity(ds)
            for ds in bw.Database(db_name)
        ]
        #
        data = alter_uuids_template(data)
        # Now correct activity match the flows with their inputs.
        data = match_flows_uuids(data)
        return data

    def export_data_as_xml(self, directory: Path) -> None:
        """Export all of the collected template objects as XML files to the
        given directory.

        NOTE: Will overwrite files if given the chance.
        """
        if not directory.exists():
            directory.mkdir()

        for i, act in enumerate(self.data):
            chunk = ecospold2_dict_from_activity(act)
            xml = xmlschema.from_json(json.dumps(chunk), schema=self.schemas)
            pth = directory / f"activity_{i}.spold"
            ElementTree(xml).write(str(pth))
