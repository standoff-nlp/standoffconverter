from copy import deepcopy as dc
import numpy as np

from lxml import etree

class ReverseLookup:
    
    def __init__(self, table, export):
        self.lookup = []
        for irow, row in table.df.iterrows():
            ex_char = export[irow]
            if ex_char is not None:
                self.lookup.append({
                    "position": row.position,
                    "table_index": irow,
                })

    def get(self,i):
        return self.lookup[i]
    
    def get_table_index(self, i):
        return self.lookup[i]["table_index"]

    def get_pos(self, i):
        return self.lookup[i]["position"]


class View:

    def __init__(self, table):
        
        self.table = table
        self.export = dc(self.table.df.text.values)

    def exclude(self, tag_list):
        
        for tag in tag_list:
            self.__exclude_single(tag)
        return self

    def __exclude_single(self, tag):

        found_rows = self.table.df.loc[
            self.table.df.el.apply(lambda x:None if x is None else x.tag) == tag
        ]
        if len(found_rows) == 0:
            return self
        mask = np.ones(len(self.table.df), dtype=bool)

        open_stack = {}
        for irow, row in found_rows.iterrows():
            if row.row_type == "open":
                open_stack[row.el] = irow
            elif row.row_type == "close":
                if row.el in open_stack:
                    mask[open_stack[row.el]: irow] = False

        self.export[~mask] = None
        return self

    def insert_tag_text(self, map_):

        for irow, row in self.table.df.iterrows():
            if row.el is not None and row.el.tag in map_.keys():
                self.export[irow] = map_[row.el.tag]

        return self

    def replace_text(self, map_):

        for irow, row in self.table.df.iterrows():
            if row.text in map_.keys():
                self.export[irow] = map_[row.text]
        return self

    def shrink_whitespace(self, shrink_to=" ", custom_whitespaces=None):
        if custom_whitespaces is None:
            whitespaces = [" ", "\t", "\n"]
        else:
            whitespaces = custom_whitespaces

        begin = None 
        for i,it in enumerate(self.export):
            if it in whitespaces and begin is None:
                begin = i
            elif it not in whitespaces and begin is not None:
                self.export[begin] = shrink_to
                self.export[begin+1:i] = None
                begin = None
        return self

    def get_plain(self):
        lookup = ReverseLookup(self.table, self.export)
        plain = "".join(it for it in self.export if it is not None)
        return plain, lookup