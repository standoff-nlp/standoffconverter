from copy import deepcopy as dc
import numpy as np

from lxml import etree

class ReverseLookup:
    """Contains a lookup from the characters of the plain text of a `View` back to the position/table index of the `PositionTable` of the `Standoff` object.
    """    
    def __init__(self, table, export):
        """Create a ReverseLookup from a table and a View export.
        
        arguments:
            table (PositionTable): the position table of the view.
            export (np.array): the export of the view.

        returns:
            (ReverseLookup): The created ReverseLookup instance.
        """
        self.lookup = []
        for irow, row in table.df.iterrows():
            ex_char = export[irow]
            if ex_char is not None:
                self.lookup.append({
                    "position": row.position,
                    "table_index": irow,
                })
        # add element at the end to be able to wrap last char
        self.lookup.append({
            "position": row.position+1,
            "table_index": irow+1
        }) 
    def get(self,i):
        """the position/table_index information for a given character position.
        
        arguments:
        i (int)-- character position in the plain text output of the view

        returns:
            positional information (dict) -- dictionary of with `position` and `table_index` keys and respective values.
        """
        return self.lookup[i]
    
    def get_table_index(self, i):
        """the table_index value for a given character position.
        
        arguments:
        i (int)-- character position in the plain text output of the view

        returns:
            table index (int).
        """
        return self.lookup[i]["table_index"]

    def get_pos(self, i):
        """the position value within Standoff Table for a given character position. This position can differ from the one in the plain text due to added or removed characters in the plain text (such as multiple whitespace removal or addition of whitespaces at encoded whitespace positions (`<lb/>`)).
        
        arguments:
        i (int)-- character position in the plain text output of the view

        returns:
            table_index (int).
        """
        return self.lookup[i]["position"]


class View:
    """Prepare the plain text of a Standoff table for processing with NLP libraries without losing the information of where the characters came from within the Standoff table. Typical use cases are removal of <notes> or insertion of newlines for encoded newlines (`<lb>`).
    """ 
    def __init__(self, table):
        
        self.table = table
        self.export = dc(self.table.df.text.values)
        

    def exclude_outside(self, tag_list):
        """exclude all text outside any of the tags in a list of tags.
        
        arguments:
        tag_list (list)-- for example `['note']` or `["{http://www.tei-c.org/ns/1.0}note", "{http://www.tei-c.org/ns/1.0}abbr"]`

        returns:
            self (int) for chainability.
        """
        for tag in tag_list:
            mask = np.zeros(len(self.table.df), dtype=bool)
            return self.__exclude_generic(tag, mask, True)
            
        return self

    def exclude_inside(self, tag_list):
        """exclude all text within any of the tags in a list of tags.
        
        arguments:
        tag_list (list)-- for example `['note']` or `["{http://www.tei-c.org/ns/1.0}note", "{http://www.tei-c.org/ns/1.0}abbr"]`

        returns:
            self (int) for chainability.
        """
        for tag in tag_list:
            mask = np.ones(len(self.table.df), dtype=bool)
            return self.__exclude_generic(tag, mask, False)
            
        return self

    def __exclude_generic(self, tag, mask, application):
        found_rows = self.table.df.loc[
            self.table.df.el.apply(lambda x:None if x is None else x.tag) == tag
        ]
        if len(found_rows) == 0:
            return self

        open_stack = {}
        for irow, row in found_rows.iterrows():
            if row.row_type == "open":
                open_stack[row.el] = irow
            elif row.row_type == "close":
                if row.el in open_stack:
                    mask[open_stack[row.el]: irow] = application

        self.export[~mask] = None
        return self


    def insert_tag_text(self, tag, text, row_type="any"):
        """insert a custom character to the plain text for all occurrences of the tag.
        
        arguments:
        map_ (dict)-- for example `{"{http://www.tei-c.org/ns/1.0}lb": "\n"}` add the newline character to the plain text for all line breaks.

        returns:
            self (int) for chainability.
        """
        for irow, row in self.table.df.iterrows():
            
            # if row.el is not None and row.el.tag == tag:
            #     import pdb; pdb.set_trace()
            if (
                row.el is not None 
                and row.el.tag == tag
                and (
                    row_type == "any"
                    or row_type == row.row_type
                )
            ):
                assert len(text) == 1, "only allowed to insert single character strings."
                self.export[irow] = text

        return self


    def shrink_whitespace(self, shrink_to=" ", custom_whitespaces=None):
        """Reduce consecutive white spaces to a single white space.
        
        arguments:
        shrink_to (str)-- the character that multiple whitespaces are replaced with (shrunken to).
        custom_whitespaces (list)-- alternative list of characters that are considered as white spaces.

        returns:
            self (int) for chainability.
        """

        assert len(shrink_to) == 1, "only single character strings allowed."
        if custom_whitespaces is None:
            whitespaces = [" ", "\t", "\n"]
        else:
            whitespaces = custom_whitespaces
        
        begin = None 
        for i,it in enumerate(self.export):
            if it in whitespaces and begin is None:
                begin = i
            elif (
                it not in whitespaces + [None]
                and begin is not None
            ):
                if sum(~self.table.df[begin:i].text.isnull()) > 1: # only replace if it actually was multiple whitespaces
                    self.export[begin] = shrink_to

                self.export[begin+1:i] = None
                begin = None
        return self

    def get_plain(self):
        """Plain text of the current status of the view alongside a ReverseLookup table. The plain text output by this function is meant to be inserted into an NLP pipeline. The results of the NLP pipeline will be made on the character level of this sequence. In order to create an annotation within the original TEI, the positions within the TEI that corresponds to the character positions in this plain text sequence can be looked up like this:
        `lookup.get_table_index(pos)`. So if there is, for example an 'A' in your document, the following assertion would be true: `so.table.df.iloc[lookup.get_table_index(plain.index("A"))].text == "A"`

        returns:
            plain (str)-- the plain text str with all modifications applied.
            lookup (ReverseLookup)-- the matching lookup object. 
        """
        lookup = ReverseLookup(self.table, self.export)
        plain = "".join(it for it in self.export if it is not None)
        return plain, lookup