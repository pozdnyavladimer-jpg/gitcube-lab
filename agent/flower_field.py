def compute_pressure(graph, report):
    pressure = {}

    pressure["cycles"] = report["metrics"]["strict_cycle_nodes"]
    pressure["layers"] = report["metrics"]["layer_viol"]
    pressure["density"] = report["metrics"]["density"]

    return pressure
