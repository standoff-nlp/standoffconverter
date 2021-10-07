from copy import deepcopy as dc
import pandas as pd
import numpy as np

from lxml import etree


class View:
    """Prepare the plain text of a Standoff table for processing with NLP libraries without
    losing the information of where the characters came from within the Standoff table. Typical use cases are removal of <notes> or insertion of newlines for encoded newlines (`<lb>`).
    """
    def __init__(self, so):

        self.table = so.table.df
        self.view = self.__create_view()

    def __create_view(self):

        result = []

        for irow, row in self.table.iterrows():
            if row.text is not None:
                for ichar, char in enumerate(row.text):
                    result.append({
                        "table_index": irow,
                        "table_position": row.position+ichar,
                        "el": row.el,
                        "row_type": row.row_type,
                        "char": char
                    })    
            else:
                result.append({
                    "table_index": irow,
                    "table_position": row.position,
                    "el": row.el,
                    "row_type": row.row_type,
                    "char": ""
                })

        return pd.DataFrame(result)

    def get_plain(self):
        """Plain text of the current status of the view. The plain text output by this function is meant to be inserted into an NLP pipeline. The results of the NLP pipeline will be made on the character level of this sequence. In order to create an annotation within the original TEI, the positions within the TEI that corresponds to the character positions in this plain text sequence can be looked up like this:
        `view.get_table_pos(plain_text_pos)`.

        returns:
            plain (str)-- the plain text str with all modifications applied.
        """
        return "".join(self.view.char)

    def get_table_pos(self, plain_text_index):
        """the position value within Standoff Table for a given character position. This position can differ from the one in the plain text due to added or removed characters in the plain text (such as multiple whitespace removal or addition of whitespaces at encoded whitespace positions (`<lb/>`)).
        
        arguments:
        plain_text_index (int)-- character position in the plain text output of the view

        returns:
            table_position (int).
        """
        index = (self.view.char.apply(len).cumsum()-1==plain_text_index).argmax()
        return self.view.iloc[index].table_position

    def get_table_index(self, plain_text_index):
        """the table_index value for a given character position.
        
        arguments:
        plain_text_index (int)-- character position in the plain text output of the view

        returns:
            table index (int).
        """
        index = (self.view.char.apply(len).cumsum()-1==plain_text_index).argmax()
        return self.view.iloc[index].table_index

    def iter_exclude(self, tag):
        open_stack = set()
        for irow, row in self.view.iterrows():
            if (row.el is not None 
                and row.el.tag == tag
                and row.row_type == "open"):
                open_stack.add(row.el)
            elif (row.el is not None 
                and row.el.tag == tag
                and row.row_type == "close"):
                open_stack.remove(row.el)

            inside = len(open_stack) > 0
            yield inside, irow, row
               
    def exclude_outside(self, tag):
        """exclude all text outside any of the tags in a list of tags.
        
        arguments:
        tag -- for example `'note'` or `"{http://www.tei-c.org/ns/1.0}abbr"`

        returns:
            self (int) for chainability.
        """
        mask = np.zeros(len(self.view), dtype=bool)
        for inside, irow, _ in self.iter_exclude(tag):
            if not inside:
                mask[irow] = True
        self.view.loc[mask, 'char'] = ""
        return self

    def exclude_inside(self, tag):
        """exclude all text within any of the tags in a list of tags.
        
        arguments:
        tag -- for example `'note'` or `"{http://www.tei-c.org/ns/1.0}abbr"`

        returns:
            self (int) for chainability.
        """
        mask = np.zeros(len(self.view), dtype=bool)
        for inside, irow, _ in self.iter_exclude(tag):
            if inside:
                mask[irow] = True
        self.view.loc[mask, 'char'] = ""
        return self

    def insert_tag_text(self, tag, text):
        """insert a custom character to the plain text for all occurrences of the tag.
        
        arguments:
        tag -- the el tag that should be replaced, for example `"{http://www.tei-c.org/ns/1.0}lb"`
        text -- the text that the el should be replaced with.

        returns:
            self (int) for chainability.
        """
        
        for _, row in self.view.iterrows():
            if row.el is not None and row.el.tag == tag:
                self.view.loc[row.name, 'char'] = text
        
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
        for i,row in self.view.iterrows():
            if row.char in whitespaces and begin is None:
                begin = i
            elif (
                row.char not in whitespaces + [""]
                and begin is not None
            ):
                if len("".join(self.view[begin:i].char)) > 1: # only replace if it actually was multiple whitespaces
                    self.view.loc[begin, 'char'] = shrink_to
                    self.view.loc[begin+1:i-1, 'char'] = ""
                begin = None

        return self
