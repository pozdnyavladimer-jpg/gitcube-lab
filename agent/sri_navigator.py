def choose_mutation(pressure):

    if pressure["cycles"] > 0:
        return "break_cycle"

    if pressure["layers"] > 0:
        return "fix_layer"

    if pressure["density"] > 0.4:
        return "remove_edge"

    return "add_edge"
