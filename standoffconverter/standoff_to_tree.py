from lxml import etree

def create_el(c_so):
    el = etree.Element(c_so["tag"])
    for k,v in c_so["attrib"].items():
        el.set(k,v)
    return el

class ItemPair:

    def __init__(self, so, el):
        self.so = so
        self.el = el

    @classmethod
    def from_so(cls, so):
        el = create_el(so)
        return cls(so, el)


def get_order_for_traversal(so):
    return sorted(
        sorted(
            sorted(
                so.standoffs,
                key=lambda x: x["depth"]
            ),
            key=lambda x:  (x["begin"] - x["end"])
        ),
        key=lambda x: x["begin"]
    )


def standoff_to_tree(so):
    
    order = get_order_for_traversal(so)

    pos_to_so = [[] for _ in range(len(so.plain))]

    for c_so in order:
        p = ItemPair.from_so(c_so)
        for pos in range(p.so["begin"], p.so["end"]):
            pos_to_so[pos].append(p)
    
    for i in range(len(so.plain)):
        c_parents = pos_to_so[i]
        for i_parent in range(len(c_parents)-1):
            c_parent = c_parents[i_parent].el
            c_child = c_parents[i_parent+1].el
            if c_child not in c_parent:
                c_parent.append(c_child)
        if len(c_parents[-1].el) == 0:
            if c_parents[-1].el.text is None:
                c_parents[-1].el.text = ""

            c_parents[-1].el.text += so.plain[i]
        else:
            if c_parents[-1].el[-1].tail is None:
                c_parents[-1].el[-1].tail = ""
            c_parents[-1].el[-1].tail += so.plain[i]

    root = pos_to_so[0][0].el.getroottree().getroot()
    return root