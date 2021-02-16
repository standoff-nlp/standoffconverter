from lxml import etree
import numpy as np
import pandas as pd
import json
from contextlib import contextmanager

class Converter:
    """TODO: Contains a reference to the etree.Element object and the corresponding StandoffElement object to link the two representations.
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

    def reset_cache(self):
        self.el2so = None
        self.so2el = None
        self.table = None

    def ensure_cache(self):
        if self.table is None:
            self.populate_cache()
    
    @property
    def plain(self):
        return "".join(self.table.text)

    @property
    def json(self):
        raise NotImplementedError()

    @property
    def collapsed_table(self):
        raise NotImplementedError()

    def get_parents(self, begin, end, depth=None):
        
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
        
        filtered_table = self.table.iloc[begin:end]

        mask = np.logical_and.reduce([
            filtered_table.sos.apply(lambda x: x[-1].begin>=begin),
            filtered_table.sos.apply(lambda x: x[-1].end<=end),
        ])

        filtered_table = filtered_table[mask]

        candidates = list(set([so for _,row in filtered_table.iterrows() for so in row.sos]))

        sos = [so for so in candidates if depth is None or so.depth > depth]

        sos = sorted(sos, key=lambda x: x.depth)

        return sos
        

    def add_standoff(self, begin, end, tag, attrib):
        raise NotImplementedError()

    def add_inline(self, **tag_dict):
        self.ensure_cache()
        
        # First, stay in the standoff world
        new_el = StandoffElement(tag_dict)
        
        

        parents = self.get_parents(new_el.begin, new_el.end)
        closest_parent = parents[-1]

        new_el.depth = closest_parent.depth + 1

        children = self.get_children(new_el.begin, new_el.end)
        for child in children:
            child.depth += 1
        
        new_part = []
        
        for irow, row in self.table.iloc[closest_parent.begin:closest_parent.end].iterrows():
            for iso, so in enumerate(row.sos):
                if so.depth == closest_parent.depth:

                    if irow >= new_el.begin and irow < new_el.end:
                        row.sos.insert(iso+1, new_el)

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

        second_parents = self.get_parents(
            closest_parent.begin,
            closest_parent.end,
            closest_parent.depth
        )

        # and replace the subtree
        if len(second_parents) == 0:
            self.text_el = new_closest_parent_el
        else:
            second_parent = second_parents[-1]

            self.so2el[second_parent].replace(
                self.so2el[closest_parent],
                new_closest_parent_el
            )

        # update lookups
        for new_so, new_el in new_so2el.items():

            if new_so in self.so2el:
                old_el = self.so2el[new_so]
                del self.el2so[old_el]

            self.so2el[new_so] = new_el
            self.el2so[new_el] = new_so


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
    for _,row in table.iterrows():
        
        c_parents = []
        for it in row.sos:
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

    root = so2el[table.iloc[0].sos[0]].getroottree().getroot()

    return root, so2el



# class AnnotationPair:
#     """Contains a reference to the etree.Element object (self.el) and the corresponding StandoffElement object (self.so) to link the two representations.
#     """
#     def __init__(self, so, el, converter):
#         """Create an AnnotationPair from a StandoffElement instance.
        
#         arguments:
#             so (StandoffElement): the StandoffElement instance.
#             el (etree.Element): the etree.Element instance.
#             converter (Converter): the Converter instance in which so is located.

#         returns:
#             (AnnotationPair): The created AnnotationPair instance.
#         """
#         self.so = so
#         self.el = el
#         self.converter = converter

#     @classmethod
#     def from_so(cls, so, converter):
#         """Create an AnnotationPair from a StandoffElement instance.
        
#         arguments:
#             so (StandoffElement): the StandoffElement instance.
#             converter (Converter): the Converter instance in which so is located.

#         returns:
#             (AnnotationPair): The created AnnotationPair instance.
#         """
#         el = create_el_from_so(so)
#         so.etree_el = el
#         return cls(so, el, converter)

#     def xpath(self, *args, **kwargs):
#         """Wrapper for `xpath` of the el

#         returns
#             (list): List of AnnotationPairs
#         """
#         found_els = self.el.xpath(*args, **kwargs)
#         return [self.converter.el2pair[el] for el in found_els]

#     def find(self, *args, **kwargs):
#         """Wrapper for `find` of the el

#         returns
#             (AnnotationPairs): The found annotation pair
#         """
#         found_el = self.el.find(*args, **kwargs)
#         return self.converter.el2pair[found_el]

#     def get_text(self):
#         """Get the text inside the annotation

#         returns:
#             (str): text within the annotation
#         """
#         return self.converter.plain[self.get_begin():self.get_end()]

#     def get_so(self):
#         """Get the so of the AnnotationPair

#         returns:
#             (StandoffElement): The created dictionary of standoff properties
#         """
#         return self.so

#     def get_el(self):
#         """Get the el of the AnnotationPair

#         returns:
#             (etree.Element): The created dictionary of standoff properties
#         """
#         return self.el

#     def get_tag(self):
#         """Get the tag of the StandoffElement

#         returns:
#             (str): The created dictionary of standoff properties
#         """
#         return self.so.tag

#     def get_depth(self):
#         """Get the depth of the StandoffElement

#         returns:
#             (int): The created dictionary of standoff properties
#         """
#         return self.so.depth

#     def get_attrib(self):
#         """Get the attrib of the StandoffElement

#         returns:
#             (dict): The created dictionary of standoff properties
#         """
#         return self.so.attrib

#     def get_begin(self):
#         """Get the begin of the StandoffElement

#         returns:
#             (int): The created dictionary of standoff properties
#         """
#         return self.so.begin

#     def get_end(self):
#         """Get the end of the StandoffElement

#         returns:
#             (int): The created dictionary of standoff properties
#         """
#         return self.so.end

#     def get_dict(self):
#         """Creates a new dictionary instance with the basic properties of the so element

#         returns:
#             (dict): The created dictionary of standoff properties
#         """
#         return {
#             "begin": self.so.begin,
#             "end": self.so.end,
#             "attrib": self.so.attrib,
#             "depth": self.so.depth,
#             "tag": self.so.tag,
#         }





# class Converter_:
#     """Home class that manages the representations of the document. 
#     """
#     def __init__(self, collection=None, plain=None, tree=None, so2pair=None, el2pair=None):
#         """
#         arguments:
#             collection (list): annotations in list format.
#             tree (etree.Element): root element of all annotations in tree format.
#             plain (str): plain text without annotations.
#             so2pair (dict): a dictionary to lookup self.collection items given a StandoffElement
#             el2pair (dict): a dictionary to lookup self.collection items given a etree.Element

#         returns:
#             (AnnotationPair): The created AnnotationPair instance.
#         """
        
#         if collection is None:
#             self.collection = []
#         else:
#             self.collection = collection

#         self.plain = plain
#         self.tree = tree
#         if so2pair is None or el2pair is None:
#             self.so2pair, self.el2pair = self.__get_lookups()
        
#         if self.tree is not None:
#             self.root_ap = self.el2pair[self.tree]

#     @classmethod
#     def from_tree(cls, tree):
#         """create a standoff representation from an lxml tree.

#         arguments:
#             tree: the lxml object
#         """
#         self = cls()
#         plain, collection = tree_to_standoff(tree, self)
#         self.tree = tree
#         self.plain = plain
#         self.collection = collection
#         self.so2pair, self.el2pair = self.__get_lookups()
#         self.root_ap = self.el2pair[self.tree]

#         return self

#     def to_tree(self):
#         """
#         returns:
#             (etree.Element): Root element of the tree representation.
#         """
#         return self.tree

#     def to_json(self):
#         """
#         returns:
#             (str): JSON representation.
#         """
#         return json.dumps(
#             [it.get_dict() for it in self.collection]
#         )

#     def __iter__(self):
#         for attr in self.collection:
#             yield attr, self.plain[attr.begin:attr.end]

#     def __len__(self):
#         return len(self.collection)

#     def __synchronize_representations(self, reference):

#         if reference == "standoff":
#             self.tree = standoff_to_tree(self)
#         elif reference == "tree":
#             self.plain, self.collection = tree_to_standoff(self.tree, self)
#         else:
#             raise ValueError("reference unknown.")

#         self.so2pair, self.el2pair = self.__get_lookups()

#     def __get_lookups(self):
        
#         so2pair = {}
#         el2pair = {}
        
#         for it_pair in self.collection:
#             so, el = it_pair.get_so(), it_pair.get_el()
#             so2pair[so] = it_pair
#             el2pair[el] = it_pair

#         return so2pair, el2pair

#     def add_annotation(self, begin=None, end=None, tag=None, depth=None, attribute=None, unique=True, synchronize=True):
#         """add a standoff annotation.

#         arguments:
#             begin (int): the beginning character index
#             end (int): the ending character index
#             tag (str): the name of the xml tag
#             depth (int): tree depth of the attribute. for the same begin and end, a lower depth annotation includes a higher depth annotation
#             attribute (dict): attrib of the lxml
#             unique (bool): whether to allow for duplicate annotations
#             synchronize (bool): Whether to synchronize other representations (self.tree, the lookups) when self.collection is updated.
#         """
#         if not unique or not self.__is_duplicate_annotation(begin, end, tag, attribute):
#             dict_ = {
#                 "begin": begin,
#                 "end": end,
#                 "tag": tag,
#                 "attrib": attribute,
#                 "depth": depth if depth is not None else 0
#             }
            
#             so = StandoffElement(dict_)
#             pair = AnnotationPair.from_so(so, self)
#             self.collection.append(pair)
#         if synchronize:
#             self.__synchronize_representations(reference="standoff")

#     def remove_annotation(self, so, synchronize=True):
#         '''remove a standoff annotation

#         arguments:
#             so (StandoffElement): that is to be removed.
#             synchronize (bool): Whether to synchronize other representations (self.tree, the lookups) when self.collection is updated.
#         '''

#         if so not in self.collection:
#             raise ValueError("Annotation not in collection")
#         self.collection.remove(so)
        
#         if synchronize:
#             self.__synchronize_representations(reference="standoff")
    
#     @contextmanager
#     def transaction(self, reference):
#         '''delay the synchronization until all modifications to either the "standoff" or the "tree" as been finished to save unwanted compute for each individual modification. You should not modify both representations in one transaction.

#         arguments:
#             reference (str): name of the representation that holds the updated information (either "standoff" or "tree").
#         '''
#         try:
#             yield
#         finally:
#             self.__synchronize_representations(reference)


#     def __is_duplicate_annotation(self, begin, end, tag, attribute):
#         """check whether this annotation already in self.collection
        
#         arguments:
#             begin (int): the beginning character index
#             end (int): the ending character index
#             tag (str): the name of the xml tag
#             attribute (dict): attrib of the lxml

#         returns:
#             bool: True if annotation already exists
#         """

#         def attrs_equal(attr_a, attr_b):
#             shared_items = {}
#             for k in attr_a:
#                 if k in attr_b and attr_a[k] == attr_b[k]:
#                     shared_items[k] = attr_a[k]

#             return len(attr_a) == len(attr_b) == len(shared_items)

#         for item_pair in self.collection:
#             if (item_pair.get_begin() == begin
#                 and item_pair.get_end() == end
#                 and item_pair.get_tag() == tag
#                 and attrs_equal(attribute, item_pair.get_attrib())):
#                 return True
#         return False
