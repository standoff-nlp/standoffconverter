

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
    return "".join(plain), [v for k,v in stand_off_props.items()]


def standoff_to_xml(plain, standoff):

    standoff_begin_lookup = [[] for _ in range(len(plain)+1)]
    standoff_end_lookup = [[] for _ in range(len(plain)+1)]
    
    for v in standoff:
        standoff_begin_lookup[v["begin"]] += [v]
        standoff_end_lookup[v["end"]] += [v]

    out_xml = ""

    offset = 0

    for ic in range(len(plain)+1):
        try:
            c = plain[ic]
        except IndexError:
            c = ""
        
        # add_closing tags
        new_str = ""
        
        for v in sorted(standoff_end_lookup[ic], key=lambda x: -x["depth"]):
            tag_str = "</{}>".format(v["tag"])
            new_str += tag_str

        out_xml += new_str
        offset += len(new_str)

        # add opening tags
        new_str = ""
        
        for v in sorted(standoff_begin_lookup[ic], key=lambda x: x["depth"]):

            attrib_str = " " + " ".join(
                "{}='{}'".format(k_, v_) for k_, v_ in v["attrib"].items()
            )
            tag_str = "<{}{}>".format(
                v["tag"],
                attrib_str if len(attrib_str) > 1 else ""
            )
            new_str += tag_str

        out_xml += new_str
        offset += len(new_str)

        out_xml += c

    return out_xml