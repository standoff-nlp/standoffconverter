def tree_to_standoff(tree):
    stand_off_props = {}
    plain = []

    def __traverse_and_parse(el, plain, stand_off_props, depth=0):
        stand_off_props[el] = {
            "begin": len(plain),
            "tag": el.tag,
            "attrib": el.attrib,
            "depth": depth
        }

        if el.text is not None:
            plain += [char for char in el.text]

        for gen in el:
            __traverse_and_parse(gen, plain, stand_off_props, depth=depth+1)

        depth -= 1
        stand_off_props[el]["end"] = len(plain)

        if el.tail is not None:
            plain += [char for char in el.tail]

    __traverse_and_parse(tree, plain, stand_off_props)
    return "".join(plain), [v for k,v in stand_off_props.items()], stand_off_props