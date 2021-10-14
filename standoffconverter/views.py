from copy import deepcopy as dc
import pandas as pd
import numpy as np

from lxml import etree
from tqdm import tqdm


class View:
    """Prepare the plain text of a Standoff table for processing with NLP libraries without
    losing the information of where the characters came from within the Standoff table. Typical use cases are removal of <notes> or insertion of newlines for encoded newlines (`<lb>`).
    """
    def __init__(self, so):

        self.table = so.table.df
        self.view = self.__create_view()
        self.begins = self.table.row_type=='open'
        self.ends = self.table.row_type=='close'


    def __create_view(self):

        result = []

        for irow, row in tqdm(self.table.iterrows(), desc="create view", total=len(self.table)):
            if row.text is not None:
                for ichar, char in enumerate(row.text):
                    result.append({
                        "table_index": irow,
                        "table_position": row.position+ichar,
                        "el": row.el,
                        "row_type": row.row_type,
                        "char": char,
                        "char_immutable": char,
                    })    
            else:
                result.append({
                    "table_index": irow,
                    "table_position": row.position,
                    "el": row.el,
                    "row_type": row.row_type,
                    "char": "",
                    "char_immutable": "",
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

    def iter_indices_inside(self, tag_or_callable=None):

        if callable(tag_or_callable):
            element_mask = self.table.el.apply(tag_or_callable)
        else:
            element_mask = self.table.el.apply(lambda x: x.tag == tag_or_callable if isinstance(x, etree._Element) else False)
            
        begins = self.table[np.logical_and(
            element_mask,
            self.begins
        )]

        ends = self.table[np.logical_and(
            element_mask,
            self.ends
        )]

        for begin, end in tqdm(zip(begins.index, ends.index), total=len(begins)):
            yield begin, end
               
    def exclude_outside(self, tag):
        """exclude all text outside the tag.
        
        arguments:
        tag -- for example `'note'` or `"{http://www.tei-c.org/ns/1.0}abbr"`

        returns:
            self (standoffconverter.View) for chainability.
        """
        mask = np.ones(len(self.view), dtype=bool)
        for begin, end in self.iter_indices_inside(tag):
            mask[self.view.table_index.isin(np.arange(begin,end))] = False
        self.view.loc[mask, 'char'] = ""
        return self

    def exclude_inside(self, tag):
        """exclude all text within the tag.
        
        arguments:
        tag -- for example `'note'` or `"{http://www.tei-c.org/ns/1.0}abbr"`

        returns:
            self (standoffconverter.View) for chainability.
        """
        mask = np.zeros(len(self.view), dtype=bool)
        for begin, end in self.iter_indices_inside(tag):
            mask[self.view.table_index.isin(np.arange(begin,end))] = True
        self.view.loc[mask, 'char'] = ""
        return self

    def include_inside(self, tag):
        """include all text within the tag. It will basically reset all modifications inside the given tag. This means that for example, altered characters or shrunken whitespaces will also be reset. It does not affect any characters outside the given tags (for example, it does not exclude anything outside explicitly). Therefore, it can combined nicely with `exclude_outside`, for example view.exclude_outside("a").include_iside_("b") which will exclude everything except what is inside `<a>`s and `<b>`s.
        
        arguments:
        tag -- for example `'note'` or `"{http://www.tei-c.org/ns/1.0}abbr"`

        returns:
            self (standoffconverter.View) for chainability.
        """
        for begin, end in self.iter_indices_inside(tag):
            self.view.loc[
                np.logical_and(
                    self.view.table_index.isin(np.arange(begin,end)),
                    self.view.row_type=='text'
                ),
                "char"
            ] = self.view.loc[
                np.logical_and(
                    self.view.table_index.isin(np.arange(begin,end)),
                    self.view.row_type=='text'
                ),
                "char_immutable"
            ]
           
        return self

    def insert_tag_text(self, tag, text):
        """insert a custom character to the plain text for all occurrences of the tag.
        
        arguments:
        tag -- the el tag that should be replaced, for example `"{http://www.tei-c.org/ns/1.0}lb"`
        text -- the text that the el should be replaced with.

        returns:
            self (standoffconverter.View) for chainability.
        """
        
        for _, row in tqdm(self.view.iterrows(), desc='insert tag text', total=len(self.view)):
            if row.el is not None and row.el.tag == tag:
                self.view.loc[row.name, 'char'] = text
        
        return self

    def shrink_whitespace(self, shrink_to=" ", custom_whitespaces=None):
        """Reduce consecutive white spaces to a single white space.
        
        arguments:
        shrink_to (str)-- the character that multiple whitespaces are replaced with (shrunken to).
        custom_whitespaces (list)-- alternative list of characters that are considered as white spaces.

        returns:
            self (standoffconverter.View) for chainability.
        """

        assert len(shrink_to) == 1, "only single character strings allowed."
        if custom_whitespaces is None:
            whitespaces = [" ", "\t", "\n"]
        else:
            whitespaces = custom_whitespaces
        
        begin = None 
        for i,row in tqdm(self.view.iterrows(), desc="shrink whitespace", total=len(self.view)):
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

    def remove_comments(self):
        """Remove comments (something like "<!-- ... -->") from plain text view.
        
        returns:
            self (standoffconverter.View) for chainability.
        """
        for begin, end in self.iter_indices_inside(
            lambda x: isinstance(x, etree._Comment)
        ):

            self.view.loc[
                np.logical_and(
                    self.view.table_index.isin(np.arange(begin,end)),
                    self.view.row_type=='text'
                ),
                "char"
            ] = ""
        
        return self