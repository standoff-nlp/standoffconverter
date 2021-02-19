from lxml import etree
import numpy as np
import pandas as pd
import json
from contextlib import contextmanager

class Converter:
    """Contains a reference to the etree.Element object and the corresponding StandoffElement object to link the two representations.
    """
    def __init__(self, tei_tree):
        """Create a Converter from a tree element instance.
        
        arguments:
            tei_tree (etree.Element): the etree.Element instance.

        returns:
            (Converter): The created Converter instance.
        """
        self.tei_tree = tei_tree

        texts = self.tei_tree.findall(".//text")
        if len(texts) == 0:
            raise ValueError("No text attribute found.")
        elif len(texts)>1:
            raise ValueError("More than one text element is not supported.")
        else:
            self.text_el = texts[0]

        # Caches
        self.reset_cache()

    @contextmanager
    def cached_standoff(self):
        try:
            self.populate_cache()
            yield
        finally:
            self.reset_cache()

    def populate_cache(self):
        self.table, self.so2el, self.el2so = tree_to_standoff(self.text_el)
        self.plaintext = "".join(self.table.text)

    def reset_cache(self):
        self.el2so = None
        self.so2el = None
        self.table = None
        self.plaintext = None

    def ensure_cache(self):
        if self.table is None:
            self.populate_cache()
    
    @property
    def plain(self):
        """Plain text string of all text inside the <text> element of the TEI XML."""
        self.ensure_cache()
        return self.plaintext

    @property
    def standoffs(self):
        """List of standoff elements of the <text> element fo the TEI XML. Items are traversed in depth-first preorder."""

        self.ensure_cache()

        sos = list(set([so for sos in self.table.sos for so in sos]))
        
        sos = sorted(
            sorted(
                sorted(
                    sos,
                    key=lambda x: x.depth
                ),
                key=lambda x:  (x.begin - x.end)
            ),
            key=lambda x: x.begin
        )

        return sos

    @property
    def json(self):
        """JSON string of standoff elements of the <text> element fo the TEI XML. Items are traversed in depth-first preorder."""
        return json.dumps(list(map(lambda x: x.to_dict(), self.standoffs)))
        
    @property
    def collapsed_table(self):
        self.ensure_cache()
        return collapse_table(self.table)

    def get_parents(self, begin, end, depth=None):
        """Get all parent sos.
        
        arguments:
        begin (int)-- beginning character position within the XML
        end (int)-- ending character position within the XML
        depth (int)-- depth of current element

        returns:
            parents (list) -- list of parent elements ordered by depth (closest is last).
        """
        filtered_table = self.table.iloc[
            max(0,begin-1):min(len(self.table),end+1)
        ]

        mask = np.logical_and.reduce([
            filtered_table.sos.apply(lambda x: x[-1].begin<=begin),
            filtered_table.sos.apply(lambda x: x[-1].end>=end)
        ])

        filtered_table = filtered_table[mask]

        candidates = list(set([so for _,row in filtered_table.iterrows() for so in row.sos]))

        sos = [so for so in candidates if depth is None or so.depth < depth]

        sos = sorted(sos, key=lambda x: x.depth)

        return sos

    def get_children(self, begin, end, depth=None):
        """Get all children sos.
        
        arguments:
        begin (int)-- beginning character position within the XML
        end (int)-- ending character position within the XML
        depth (int)-- depth of current element

        returns:
            children (list) -- list of children elements ordered by depth (closest is first).
        """
        filtered_table = self.table.iloc[begin:end]

        mask = np.logical_and.reduce([
            filtered_table.sos.apply(lambda x: x[-1].begin>=begin),
            filtered_table.sos.apply(lambda x: x[-1].end<=end),
        ])

        filtered_table = filtered_table[mask]

        candidates = list(set([so for _,row in filtered_table.iterrows() for so in row.sos]))

        sos = [so for so in candidates if depth is None or so.depth >= depth]

        sos = sorted(sos, key=lambda x: x.depth)

        return sos
        
    def add_standoff(self, begin, end, tag, attrib):
        raise NotImplementedError()

    def __replace_el(self, old_el, new_el):

        old_so = self.el2so[old_el]

        second_parents = self.get_parents(
            old_so.begin,
            old_so.end,
            old_so.depth
        )

        # and replace the subtree
        if len(second_parents) == 0:
            new_el.tail = self.text_el.tail
            self.text_el = new_el
        else:
            second_parent = self.so2el[second_parents[-1]]
            new_el.tail = old_el.tail
            second_parent.replace(
                old_el,
                new_el
            )

    def __update_so2el_lookup(self, new_so2el):

        for new_so, new_el in new_so2el.items():

            if new_so in self.so2el:
                old_el = self.so2el[new_so]
                del self.el2so[old_el]

            self.so2el[new_so] = new_el
            self.el2so[new_el] = new_so


    def remove_inline(self, so_to_remove):
        """Remove a standoff element from the structure. 
        The standoff element will be removed from the caches and from the etree.
        
        arguments:
        so_to_remove (StandoffElement)-- the element that should be removed

        """
        parents = self.get_parents(
            so_to_remove.begin,
            so_to_remove.end,
            so_to_remove.depth
        )

        closest_parent = parents[-1]

        new_part = []
        
        for irow, row in self.table.iloc[closest_parent.begin:closest_parent.end].iterrows():
            for iso, so in enumerate(row.sos):
                if so.depth == closest_parent.depth:

                    new_part.append(
                        row.sos[iso:]
                    )

                if so_to_remove in row.sos:
                    row.sos.remove(so_to_remove)

        new_part = pd.DataFrame.from_dict({
            "sos": new_part,
            "text": self.table[closest_parent.begin:closest_parent.end].text
        })

        children = self.get_children(
            so_to_remove.begin,
            so_to_remove.end,
            so_to_remove.depth
        )
        
        for child in children:
            child.depth -= 1

        # now, recreate the subtree this element is in
        new_closest_parent_el, new_so2el = standoff_to_tree(
            new_part
        )

        self.__replace_el(
            self.so2el[closest_parent],
            new_closest_parent_el
        )
        
        del self.el2so[self.so2el[so_to_remove]]
        del self.so2el[so_to_remove]

        self.__update_so2el_lookup(new_so2el)
        

    def add_inline(self, **tag_dict):
        """Add a standoff element to the structure. 
        The standoff element will be added to the caches and to the etree.
        
        arguments:
        begin (int)-- beginning character position within the XML
        end (int)-- ending character position within the XML
        tag (str)-- tag name, for example 'text' for <text>.
        depth (int)-- depth where to add the element. If None, it will be added deepest
        attrib (dict)-- dictionary of items that go into the attrib of etree.Element. Ultimately, attributes within tags. for example {"resp":"machine"} will result in <SOMETAG resp="machine">.
        """

        self.ensure_cache()
        
        # First, stay in the standoff world
        new_so = StandoffElement(tag_dict)

        parents = self.get_parents(new_so.begin, new_so.end, new_so.depth)
        closest_parent = parents[-1]

        new_so.depth = closest_parent.depth + 1
        
        children = self.get_children(new_so.begin, new_so.end, new_so.depth)
        
        for child in children:
            child.depth += 1
        
        new_part = []
        
        for irow, row in self.table.iloc[closest_parent.begin:closest_parent.end].iterrows():
            for iso, so in enumerate(row.sos):
                if so.depth == closest_parent.depth:
                    if irow >= new_so.begin and irow < new_so.end:
                        row.sos.insert(iso+1, new_so)

                    new_part.append(
                        row.sos[iso:]
                    )
        new_part = pd.DataFrame.from_dict({
            "sos": new_part,
            "text": self.table[closest_parent.begin:closest_parent.end].text
        })

        # now, recreate the subtree this element is in
        new_closest_parent_el, new_so2el = standoff_to_tree(
            new_part
        )

        self.__replace_el(
            self.so2el[closest_parent],
            new_closest_parent_el
        )

        self.__update_so2el_lookup(new_so2el)


class StandoffElement:
    """Wrapper class for the basic standoff properties."""
    def __init__(self, dict_):
        self.tag = dict_["tag"] if "tag" in dict_ else None
        self.attrib = dict(dict_["attrib"]) if "attrib" in dict_ else None
        self.begin = dict_["begin"] if "begin" in dict_ else None
        self.end = dict_["end"] if "end" in dict_ else None
        self.depth = dict_["depth"] if "depth" in dict_ else None

    def __str__(self):
        return self.tag

    def __repr__(self):
        return f"{self.tag}-{hex(id(self))}"

    def to_dict(self):
        return {
            "tag": self.tag,
            "attrib": self.attrib,
            "begin": self.begin,
            "end": self.end,
            "depth": self.depth
        }

def collapse_table(table):
        """Pandas Dataframe with standoff elements and texts aligned. text within the same element is grouped"""
        context = table.sos.apply(tuple)
        grouper = (context != context.shift()).cumsum()
        collapsed = []
        for group, subdf in table.groupby(grouper):
            collapsed.append({
                "context": subdf.iloc[0].sos,
                "text": "".join(subdf.text)
            })

        return pd.DataFrame(collapsed)


def create_el_from_so(c_so):
    el = etree.Element(c_so.tag)
    for k,v in c_so.attrib.items():
        el.set(k,v)
    return el

def get_table_from_pair_collection(plain, pair_collection):
    order = __get_order_for_traversal(pair_collection)

    pos2so = [[] for _ in range(len(plain))]
    so2el = {}
    el2so = {}

    for c_so,c_el in order:

        so2el[c_so] = c_el
        el2so[c_el] = c_so

        for pos in range(c_so.begin, c_so.end):
            pos2so[pos].append(c_so)

    table = pd.DataFrame()

    table['sos'] = pos2so
    table['text'] = [c for c in plain]

    return table, so2el, el2so
    

def tree_to_standoff(tree):
    """traverse the tree and create a standoff representation.

    arguments:
        tree -- the root element of an lxml etree

    returns:
        plain (str) -- the plain text of the tree
        collection (list) -- the list of standoff annotations
    """
    stand_off_props = {}
    plain = []

    def __traverse_and_parse(el, plain, stand_off_props, depth=0):
        
        so = {
            "begin": len(plain),
            "tag": el.tag,
            "attrib": el.attrib,
            "depth": depth
        }
        
        so = StandoffElement(so)

        stand_off_props[el] = (so, el)

        if el.text is not None:
            plain += [char for char in el.text]

        for gen in el:
            __traverse_and_parse(gen, plain, stand_off_props, depth=depth+1)

        depth -= 1
        stand_off_props[el][0].end = len(plain)

        if el.tail is not None and depth>0: # (depth>0) shouldn't add tail for root
            plain += [char for char in el.tail]

    __traverse_and_parse(tree, plain, stand_off_props)

    plain, pair_collection = "".join(plain), [v for k,v in stand_off_props.items()]
    
    table, so2el, el2so = get_table_from_pair_collection(plain, pair_collection)

    return table, so2el, el2so


def __get_order_for_traversal(so):
    return sorted(
        sorted(
            sorted(
                so,
                key=lambda x: x[0].depth
            ),
            key=lambda x:  (x[0].begin - x[0].end)
        ),
        key=lambda x: x[0].begin
    )


def standoff_to_tree(table):
    """convert the standoff representation to a etree representation

    arguments:
        table -- standoff object

    returns:
        tree (str) -- the root element of the resulting tree
    """
    so2el = {}
    collapsed_table = collapse_table(table)
    for _,row in collapsed_table.iterrows():
        
        c_parents = []
        for it in row.context:
            if it not in so2el:
                new_el = create_el_from_so(it)
                so2el[it] = new_el

            c_parents.append(so2el[it])
                
        for i_parent in range(len(c_parents)-1):
            c_parent = c_parents[i_parent]
            c_child = c_parents[i_parent+1]
            if c_child not in c_parent:
                c_parent.append(c_child)
        if len(c_parents[-1]) == 0:
            if c_parents[-1].text is None:
                c_parents[-1].text = ""

            c_parents[-1].text += row.text
        else:
            if c_parents[-1][-1].tail is None:
                c_parents[-1][-1].tail = ""
            c_parents[-1][-1].tail += row.text

    root = so2el[collapsed_table.iloc[0].context[0]].getroottree().getroot()

    return root, so2el
