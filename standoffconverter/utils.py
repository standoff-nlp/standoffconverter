from lxml import etree

def strip_ns(tag):
    return (
        tag[tag.index("}")+1:] if "}" in tag else tag
    )


def is_empty_el(el):
    return len(el) == 0 and el.text is None


def create_el_from_so(tag, attrib):
    el = etree.Element(tag)
    for k,v in attrib.items():
        el.set(k,v)
    return el


def get_order_for_traversal(so):
    return sorted(
        sorted(
            sorted(
                so,
                key=lambda x: x["depth"]
            ),
            key=lambda x:  (x["begin"] - x["end"])
        ),
        key=lambda x: x["begin"]
    )