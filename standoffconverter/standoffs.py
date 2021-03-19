from lxml import etree
import numpy as np
import pandas as pd
import json
from contextlib import contextmanager
from copy import deepcopy as dc
from .converters import flat_tree2position_table, flatten_tree, standoff2tree
from .utils import is_empty_el, strip_ns, get_order_for_traversal, create_el_from_so
        
        
class Standoff:
    """Contains a reference to the etree.Element object and the corresponding ContextItem object to link the two representations.
    """
    def __init__(self, tei_tree, namespaces={}):
        """Create a Converter from a tree element instance.
        
        arguments:
            tei_tree (etree.Element): the etree.Element instance.

        returns:
            (Standoff): The created Standoff instance.
        """

        if "tei" not in namespaces:
            namespaces = {"tei": ""}

        self.tei_tree = tei_tree

        texts = self.tei_tree.findall(".//tei:text", namespaces=namespaces)
        if len(texts) == 0:
            raise ValueError("No text attribute found.")
        elif len(texts)>1:
            raise ValueError("More than one text element is not supported.")
        else:
            self.text_el = texts[0]
        
        self.text_el.tail = None # remove trailing whitespace of text element

        flat_tree = flatten_tree(self.text_el)
        self.table_ = flat_tree2position_table(flat_tree)

    @property
    def table(self):
        """Table with each character and context of the <text> element of the tei tree. Index  is character position inside <text> element of te TEI XML."""
        return self.table_
    
    @property
    def tree(self):
        """tree of the TEI XML."""
        return self.tei_tree

    @property
    def plain(self):
        """Plain text string of all text inside the <text> element of the TEI XML."""
        return self.table.get_text()

    @property
    def standoffs(self):
        """List of standoff elements of the <text> element fo the TEI XML. Items are traversed in depth-first preorder."""
        elements = {}
        for position, row_type, el, depth, text in self.table:

            if row_type in ["open", "empty"]:
                elements[el] = {
                    "el": el,
                    "begin": position,
                    "end": None,
                    "depth": depth
                }
            if row_type in ["close", "empty"]:
                elements[el]["end"] = position
            
        return get_order_for_traversal(list(elements.values()))

    @property
    def json(self):
        """JSON string of standoff elements of the <text> element fo the TEI XML. Items are traversed in depth-first preorder."""
        so_as_json = []
        for standoff in self.standoffs:
            so_as_json.append({
                "tag": standoff["el"].tag,
                "attrib": dict(standoff["el"].attrib),
                "begin": int(standoff["begin"]),
                "end": int(standoff["end"]),
                "depth": int(standoff["depth"]),
            })
        
        return json.dumps(so_as_json)
        
    @property
    def collapsed_table(self):
        """Table with text and context of the <text> element of the tei tree. All leaf/tail text with the same context is joined."""
        return self.table.collapse()

    def get_parents(self, begin, end, depth=None):
        """Get all parent context.
        
        arguments:
        begin (int)-- beginning character position within the XML
        end (int)-- ending character position within the XML
        depth (int)-- depth of current element

        returns:
            parents (list) -- list of parent elements ordered by depth (closest is last).
        """

        begin_ctx = self.table.get_context_at_pos(begin)
        if depth is not None:
            begin_parents = begin_ctx[:int(depth)]
        else:
            begin_parents = begin_ctx

        end_ctx = self.table.get_context_at_pos(max(begin, end-1))
        if depth is not None:
            end_parents = end_ctx[:int(depth)]
        else:
            end_parents = end_ctx

        if len(begin_parents) > len(end_parents):
            parents = end_parents
        elif len(begin_parents) < len(end_parents):
            parents = begin_parents
        else:
            parents = begin_parents

        if begin_parents != end_parents:
            raise ValueError("no unique context found")

        return parents

    def get_children(self, begin, end, depth):
        """Get all children context.
        
        arguments:
        begin (int)-- beginning character position within the XML
        end (int)-- ending character position within the XML
        depth (int)-- depth of current element

        returns:
            children (list) -- list of children elements ordered by depth (closest is first).
        """

        begin_ctx = self.table.get_context_at_pos(begin)
        
        if depth is None:
            depth = len(begin_ctx)

        children = set(begin_ctx[int(depth):])
        for pos in range(begin+1, end+1):
            ctx = self.table.get_context_at_pos(begin)
            children.union(set(ctx[int(depth):]))
    
        return list(children)
        
    def add_standoff(self, begin, end, tag, attrib):
        raise NotImplementedError()

    def __replace_el(self, old_el, new_el):

        second_parent = old_el.getparent()

        # and replace the subtree
        if second_parent is None:
            new_el.tail = self.text_el.tail
            self.text_el = new_el
        else:
            new_el.tail = old_el.tail
            second_parent.replace(
                old_el,
                new_el
            )

    def add_inline(self, begin, end, tag, depth=None, attrib=None):
        """Add a standoff element to the structure. 
        The standoff element will be added to the caches and to the etree.
        
        arguments:
        begin (int)-- beginning character position within the XML
        end (int)-- ending character position within the XML
        tag (str)-- tag name, for example 'text' for <text>.
        depth (int)-- depth where to add the element. If None, it will be added deepest
        attrib (dict)-- dictionary of items that go into the attrib of etree.Element. Ultimately, attributes within tags. for example {"resp":"machine"} will result in <SOMETAG resp="machine">.
        """

        attrib = attrib if attrib is not None else {}
        
        # First, create a new element and get parents and children
        new_el = create_el_from_so(tag, attrib)
        parents = self.get_parents(begin, end, depth)

        parent = parents[-1]

        # DEPTH handling 
        # set own depth and increase children's depth by one
        new_depth = depth if depth is not None else len(parents)
        
        children = self.get_children(begin, end, new_depth)
  
        for child in children:
            child_depth = self.table.df[self.table.df.el==child].iloc[0].depth
            self.table.set_el(child, {"depth":child_depth+1} )

        if begin == end:
            self.table.insert_empty(begin, new_el, new_depth)
        else:
            self.table.insert_open(begin, new_el, new_depth)
            self.table.insert_close(end, new_el, new_depth)
        # extract part of the standoff table that needs to be recreated
        # as etree
        parent_begin, parent_end = self.table.df.loc[self.table.df.el == parent].index
        to_update = self.table.df.iloc[parent_begin:parent_end]

        # now, recreate the subtree this element is in
        new_parent_el, old_els2new_els = standoff2tree(to_update)
        
        for old_el, new_el in old_els2new_els.items():
            self.table.set_el(old_el, {"el": new_el})
        self.__replace_el(
            parent,
            new_parent_el
        )

    def remove_inline(self, del_el):
        """Remove a standoff element from the structure. 
        The standoff element will be removed from the caches and from the etree.
        
        arguments:
        del_el (etree.Element)-- the element that should be removed

        """
        el_open_row = self.table.df[np.logical_and(
            self.table.df.el == del_el,
            self.table.df.row_type.isin(["open", "empty"])
        )].iloc[0]

        el_close_row = self.table.df[np.logical_and(
            self.table.df.el == del_el,
            self.table.df.row_type.isin(["close", "empty"])
        )].iloc[0]

        begin = el_open_row.position
        end = el_close_row.position
        depth = el_open_row.depth

        parents = self.get_parents(begin, end, depth)

        parent = parents[-1]

        children = self.get_children(begin, end, depth)
        
        # DEPTH handling 
        # decrease children's depth by one
        for child in children:
            child_depth = self.table.df[self.table.df.el==child].iloc[0].depth
            self.table.set_el(child, {"depth":child_depth-1} )

        self.table.remove_el(del_el)

        # extract part of the standoff table that needs to be recreated
        # as etree
        parent_begin, parent_end = self.table.df.loc[self.table.df.el == parent].index
        to_update = self.table.df.iloc[parent_begin:parent_end]

        # now, recreate the subtree this element is in
        new_parent_el, old_els2new_els = standoff2tree(to_update)

        for old_el, new_el in old_els2new_els.items():
            self.table.set_el(old_el, {"el": new_el})
            
        self.__replace_el(
            parent,
            new_parent_el
        )
        

    def add_span(self, id_, **tag_dict):
        """Add a span element to the structure. 
        arguments:
        begin (int)-- beginning character position within the XML
        end (int)-- ending character position within the XML
        tag (str)-- tag name, for example 'text' for <text>.
        depth (int)-- depth where to add the element. If None, it will be added deepest
        """
        
        #add span start
        attrib = {"spanTo":id_}
        if "attrib" in tag_dict:
            attrib.update(tag_dict["attrib"])
        self.add_inline(
            begin=tag_dict["begin"],
            end=tag_dict["begin"],
            tag=tag_dict["tag"]+"Span",
            depth=tag_dict["depth"],
            attrib=attrib
            )
        
        #add anchor
        self.add_inline(
            begin=tag_dict["end"],
            end=tag_dict["end"],
            tag="anchor",
            depth=tag_dict["depth"],
            attrib={"id":id_}
            )
