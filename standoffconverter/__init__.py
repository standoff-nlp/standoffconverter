import numpy as np


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


class FilterSet:

    def __init__(self, so):
        self.so = so
        self.find_map = np.zeros(len(so.plain))
        self.exclude_map = np.zeros(len(so.plain))

    def find(self, query):
        for attr in self.so.standoffs:
            if attr["tag"] == query:
                self.find_map[attr["begin"]:attr["end"]] = 1
        return self

    def exclude(self, query):
        for attr in self.so.standoffs:
            if attr["tag"] == query:
                self.exclude_map[attr["begin"]:attr["end"]] = 1
        return self

    def __iter__(self, flat=True):

        filtered_standoffs = []
        for attr in self.so.standoffs:
            if self.find_map[attr["begin"]:attr["end"]].sum() == attr["end"] - attr["begin"]:
                if self.exclude_map[attr["begin"]:attr["end"]].sum() < attr["end"] - attr["begin"]:
                    filtered_standoffs.append(attr)

        if flat:
            if len(self.so.standoffs) == 0:
                return
            min_depth = min(self.so.standoffs, key=lambda x: x["depth"])

        for attr in self.so.standoffs:
            if not flat or attr["depth"] == min_depth:
                yield attr, "".join(
                    c for ic, c in enumerate(self.so.plain[attr["begin"]:attr["end"]]) if (
                        self.exclude_map == 0 and self.find_map == 1
                    )
                )

class Standoff:
    
    def __init__(self, standoffs=None, plain=None):
        self.standoffs = [] if standoffs is None else standoffs
        self.plain = plain
 
    @classmethod
    def from_lxml_tree(cls, tree):
        """create a standoff representation from an lxml tree.

        arguments:
        tree -- the lxml object
        """
        plain, standoffs = tree_to_standoff(tree)
        return cls(standoffs, plain)


    def __iter__(self):
        for attr in self.standoffs:
            yield attr, self.plain[attr["begin"]:attr["end"]]

    def to_xml(self):
        """create a standoff representation from an lxml tree.

        returns:
        string -- the string containing the xml
        """
        assert self.plain is not None, "tree not yet initialized."

        standoff_begin_lookup = [[] for _ in range(len(self.plain)+1)]
        standoff_end_lookup = [[] for _ in range(len(self.plain)+1)]
        
        for v in self.standoffs:
            standoff_begin_lookup[v["begin"]] += [v]
            standoff_end_lookup[v["end"]] += [v]

        out_xml = ""

        offset = 0

        for ic in range(len(self.plain)+1):
            try:
                c = self.plain[ic]
            except IndexError:
                c = ""
            
            # add_closing tags
            new_str = ""
            sorted_end = sorted(
                sorted(standoff_end_lookup[ic], key=lambda x: -x["depth"]),
                key=lambda x: -(x["end"] - x["begin"])
            )

            for v in sorted_end:
                tag_str = "</{}>".format(v["tag"])
                new_str += tag_str

            out_xml += new_str
            offset += len(new_str)

            # add opening tags
            new_str = ""
            
            sorted_begin = sorted(
                sorted(standoff_begin_lookup[ic], key=lambda x: x["depth"]),
                key=lambda x: -(x["end"] - x["begin"])
            )

            for v in sorted_begin:

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

    def add_annotation(self, begin, end, tag, depth, attribute, unique=True):
        """add a standoff annotation.

        arguments:
        begin (int) -- the beginning character index
        end (int) -- the ending character index
        tag (str) -- the name of the xml tag
        depth (int) -- tree depth of the attribute. for the same begin and end, 
                 a lower depth annotation includes a higher depth annotation
        attribute (dict) -- attrib of the lxml

        keyword arguments:
        unique (bool) -- whether to allow for duplicate annotations
        """
        if not unique or not self.is_duplicate_annotation(begin, end, tag, attribute):
            self.standoffs.append({
                "begin": begin,
                "end": end,
                "tag": tag,
                "attrib": attribute,
                "depth": depth if depth is not None else 0
            })

    def is_duplicate_annotation(self, begin, end, tag, attribute):
        """check whether this annotation already in self.standoffs
        
        arguments:
        begin (int) -- the beginning character index
        end (int) -- the ending character index
        tag (str) -- the name of the xml tag
        attribute (dict) -- attrib of the lxml

        returns:
        bool -- True if annotation already exists
        """

        def attrs_equal(attr_a, attr_b):
            shared_items = {}
            for k in attr_a:
                if k in attr_b and attr_a[k] == attr_b[k]:
                    shared_items[k] = attr_a[k]

            return len(attr_a) == len(attr_b) == len(shared_items)

        for standoff in self.standoffs:
            if (standoff["begin"] == begin
                and standoff["end"] == end
                and standoff["tag"] == tag
                and attrs_equal(attribute, standoff["attrib"])):
                return True
        return False
        