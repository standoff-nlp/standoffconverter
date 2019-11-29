from lxml import etree


def is_child_of(a,b):
    if (
        (a.begin < b.begin and a.end > b.end)
        or (a.begin <= b.begin and a.end > b.end)
        or (a.begin < b.begin and a.end >= b.end)
        or (
            a.begin == b.begin and a.end == b.end 
            and a.depth < b.depth
        )
    ):
        return True
    return False


def create_el_from_so(c_so):
    el = etree.Element(c_so.tag)
    for k,v in c_so.attrib.items():
        el.set(k,v)
    return el
