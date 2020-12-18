# -*- coding: utf-8 -*-

def alter_uuids_template(data: list) -> list:
    """Add activity and flow uuid's to the Activity and Exchange objects
    within the data.
    """
    for ds in data:
        if "activity" not in ds.activity:
            ds.activity["activity"] = ds.activity_id
        for exc in ds.exchanges:
            if "flow" not in exc.exchange:
                if exc.type == "biosphere":  # Specific for 'biosphere3' dataset.
                    flow = exc.exchange.input
                    exc.exchange["flow"] = flow.get("code")
                else:
                    exc.exchange["flow"] = exc.flow_id
            elif exc.exchange.get("type") in {"production", "technosphere", "substitution"}:
                # Replace the flow id for technosphere exchanges that have an old one.
                exc.exchange["flow"] = exc.flow_id
    return data


def match_flows_uuids(data: list) -> list:
    """Ensure that technosphere inputs of an activity are correctly matched to
    the other activities in the dataset.
    """
    matchers = {
        ds.key: ds.production_flow_id for ds in data
    }
    for ds in data:
        technosphere = (
            e for e in ds.exchanges if e.type in {"technosphere", "substitution"}
        )
        for exc in technosphere:
            exc.exchange["flow"] = matchers[exc.exchange.input.key]
    return data
