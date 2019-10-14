import numpy as np
from lxml import etree

def load(fname):
    with open(fname, "r") as fin:
        tree = etree.fromstring(fin.read())
    return Standoff.from_lxml_tree(tree)


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



def standoff_to_tree(so):

    order = sorted(
        sorted(
            sorted(
                so.standoffs,
                key=lambda x: x["depth"]
            ),
            key=lambda x:  (x["begin"] - x["end"])
        ),
        key=lambda x: -x["begin"]
    )

    def __traverse_and_write(parent, ll):

        if len(ll) > 0:
            c_so = ll[0]

            new_el = etree.Element(c_so["tag"])
            for k,v in c_so["attrib"].items():
                new_el.set(k,v)

            if parent is None:
                parent = new_el
            else:
                parent.append(new_el)
            

            if len(ll[1:]) > 0:
                next_so = ll[1]

                new_el.text = so.plain[c_so["begin"]:next_so["begin"]]
                if (
                    (c_so["begin"] < next_so["begin"] and c_so["end"] > next_so["end"])
                    or (c_so["begin"] <= next_so["begin"] and c_so["end"] > next_so["end"])
                    or (c_so["begin"] < next_so["begin"] and c_so["end"] >= next_so["end"])
                    or (c_so["begin"] == next_so["begin"] and c_so["end"] == next_so["end"] and c_so["depth"] < next_so["depth"])
                ):                
                    child = __traverse_and_write(new_el, ll[1:])
                    child.tail = so.plain[next_so["end"]: c_so["end"]]
                else:
                    new_el.tail = so.plain[c_so["end"]: next_so["begin"]]
                    sibling = __traverse_and_write(parent, ll[1:])
                    sibling.tail = so.plain[next_so["end"]: c_so["end"]]

            else:
                new_el.text = so.plain[c_so["begin"]:c_so["end"]]
            
            return new_el

    root = __traverse_and_write(None, order)

    return root


class Filter:

    def __init__(self, so, namespace=""):
        self.so = so
        self.find_state = [so.tree]
        self.exclude_map = np.zeros(len(so.plain))
        self.namespace = namespace

    def find(self, tag):
        new_find_state = []

        for it in self.find_state:
            new_find_state += [jt for jt in it.iterfind(".//{}{}".format(self.namespace, tag))]

        self.find_state = new_find_state
        return self

    def first(self):
        for plain, standoff in self.__iter__():
            return plain, standoff

    def exclude(self, tag):
        for it in self.find_state:
            for jt in it.iterfind(".//{}{}".format(self.namespace, tag)):
                standoff = self.so.tree_standoff_link[jt]
                self.exclude_map[standoff["begin"]:standoff["end"]] = 1

        return self

    def __iter__(self):
        for el in self.find_state:
            standoff = self.so.tree_standoff_link[el]
            filtered_string = (
                "".join(
                    char for ichar, char in enumerate(self.so.plain[standoff["begin"]:standoff["end"]])
                                                if self.exclude_map[ichar + standoff["begin"]] == 0
                )
            )
            yield filtered_string, standoff


    def copy(self):
        '''
        create a copy of the filter set by retaining the original standoff and namespace
        also retaining
        '''
        new_obj = Filter(self.so, self.namespace)    
        new_obj.exclude_map = np.copy(self.exclude_map)
        new_obj.find_state = [el for el in self.find_state]
        return new_obj

class Standoff:
    
    def __init__(self, standoffs=None, plain=None, tree=None, tree_standoff_link=None):
        self.standoffs = [] if standoffs is None else standoffs
        self.plain = plain
        self.tree = tree
        self.tree_standoff_link = tree_standoff_link

    @classmethod
    def from_lxml_tree(cls, tree):
        """create a standoff representation from an lxml tree.

        arguments:
        tree -- the lxml object
        """
        plain, standoffs, link = tree_to_standoff(tree)
        return cls(standoffs, plain, tree, link)

    def __iter__(self):
        for attr in self.standoffs:
            yield attr, self.plain[attr["begin"]:attr["end"]]

    def synchronize_representations(self, reference):

        if reference == "standoff":
            self.tree = standoff_to_tree(self)
        elif reference == "tree":
            self.plain, self.standoffs = tree_to_standoff(self.tree)
        else:
            raise ValueError("reference unknown.")

    def add_annotation(self, begin=None, end=None, tag=None, depth=None, attribute=None, unique=True):
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
        self.synchronize_representations(reference="standoff")

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
     
    def save(self, fname):
        with open(fname, "w") as fout:
            fout.write(etree.tostring(self.tree, encoding=str))

    
        