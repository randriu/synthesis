import re


def parse_am_labels(hole):
    options = []
    for option in hole.options:
        assert re.match(
            r"{.*}\+\d", hole.option_labels[option]), "Hole option label {} doesn't match".format(hole.option_labels[option])
        opt = re.findall(r"{.*}\+(\d)", hole.option_labels[option])[0]
        options.append(int(opt))

    max = None if not options else sorted(list(set(options)))[-1]

    return (options, max)


def get_current_memory(name):
    return int(re.findall(r"[AM]{1,2}\(\[.*\],(\d)\)", name)[0])


def parse_hole(hole) -> object:
    assert re.match(r"[AM]{1,2}\(\[.*\],\d\)",
                    hole.name), "Cannot use restrict function, hole name doesn't match"
    parsed = {}
    parsed["memory"] = get_current_memory(hole.name)
    parsed["next"] = list(hole.options)

    observation = re.findall(r"[AM]{1,2}\(\[(.*)],\d\)", hole.name)

    if len(observation):
        parsed["observation"] = observation[0] if observation[0] else "-"
    else:
        parsed["observation"] = "-"

    if hole.name[0] == "M":
        parsed["type"] = "Memory"
    elif hole.name[0] == "A" and hole.name[1] == "M":
        parsed["type"] = "Mix"
        options, _ = parse_am_labels(hole)
        parsed["next"] = list(set(options))
    else:
        parsed["type"] = "Assignment"

    return parsed
