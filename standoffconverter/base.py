import numpy as np
import pandas as pd
from copy import copy as sc

from .utils import strip_ns, is_empty_el

class Context(list):
    """list of etree.Elements that define the context of a position."""
    def __str__(self):
        return ">".join(map(lambda ctx: strip_ns(ctx.tag), self))
        # return ">".join(map(lambda x: x.tag, self))

    # def strip_ns(self):

    def __eq__(self, other):
        if len(self) != len(other):
            return False

        for a,b in zip(self,other):
            if a != b:
                return False

        return True

class PositionTable:
    """Base representation that connects the tree and the standoff world."""
    def __init__(self, df):
        self.df = df
        self.plain = "".join(self.df[~self.df.text.isnull()].text)

    def __iter__(self):
        for irow, row in self.df.iterrows():
            yield (
                row.position,
                row.row_type,
                row.el,
                row.depth,
                row.text,
            )
    
    def iter_positions(self, include_empty_els=True):

        current_context = Context()
        for irow, row in self.df.iterrows():
            if row.row_type == "open":
                current_context.append(row.el)
            if row.row_type == "close":
                current_context = Context(current_context[:-1])
            if row.row_type == "empty" and include_empty_els:
                yield row.position, Context(current_context + [row.el]), None
            if row.row_type == "text":
                yield row.position, current_context, row.text

    def get_text(self):
        return self.plain

    def set_el(self, el, map_):        
        for k,v in map_.items():
            assert k in ['el', 'position', 'row_type', 'depth', 'text']
            indices = self.df.loc[self.df.el == el, k].index
            for index in indices:
                self.df.at[index, k] = v

    def __split_string(self, pos):

        slice_ = self.df[np.logical_and(
            self.df.position < pos,
            self.df.row_type == "text"
        )]

        old_row = slice_.iloc[-1]
        base_position = old_row.position
        split_index = pos - base_position

        new_text1 = old_row.text[:split_index]
        new_text2 = old_row.text[split_index:]

        new_row1 = (base_position, "text", None, old_row.depth, new_text1)
        new_row2 = (pos, "text", None, old_row.depth, new_text2)

        index = old_row.name
        self.df.loc[index] = new_row1
        self.df.loc[index+.5] = new_row2
        self.df = self.df.sort_index().reset_index(drop=True)

    def insert_open(self, pos, el, new_depth):
        row_type = "open"
        if not (self.df.position==pos).any():
            # pos not in self.df.position
            self.__split_string(pos)
        slice_ = self.df[self.df.position == pos]
        after_pos = np.ravel(np.argwhere(~(slice_.depth<new_depth).values))[0]
        index = slice_.iloc[after_pos].name-.5
        self.df.loc[index] = (pos, row_type, el, new_depth, None)
        self.df = self.df.sort_index().reset_index(drop=True)

    def insert_close(self, pos, el, new_depth):
        row_type = "close"
        if not (self.df.position==pos).any():
            # pos not in self.df.position
            self.__split_string(pos)
        slice_ = self.df[self.df.position == pos]
        after_pos = np.ravel(np.argwhere(~(slice_.depth>new_depth).values))[0]
        index = slice_.iloc[after_pos].name-.5
        self.df.loc[index] = (pos, row_type, el, new_depth, None)
        self.df = self.df.sort_index().reset_index(drop=True)

    def insert_empty(self, pos, el, new_depth, insert_index_at_pos=0):


        row_type = "empty"

        if not (self.df.position==pos).any():
            # pos not in self.df.position
            self.__split_string(pos)

        slice_ = self.df[self.df.position == pos]
        
        ind_candidates = []

        for _,row in slice_.iterrows():
            if row.row_type == 'close' and row.depth+1 == new_depth:
                ind_candidates.append(row.name-.5)
            elif row.row_type == 'open' and row.depth+1 == new_depth:
                ind_candidates.append(row.name+.5)
            elif row.row_type == 'empty' and row.depth == new_depth:
                ind_candidates.append(row.name+.5)
            elif row.row_type == 'text':
                ind_candidates.append(row.name-.5)


        ind_candidates = sorted(list(set(ind_candidates)))
        # import pdb; pdb.set_trace()
        index = ind_candidates[insert_index_at_pos]
    
        self.df.loc[index] = (pos, row_type, el, new_depth, None)
        self.df = self.df.sort_index().reset_index(drop=True)

    def remove_el(self, el):
    
        index = self.df[self.df.el == el].index
        self.df.drop(index, inplace=True)
    
        for idx_entry in index:
            
            old_row1 = self.df.loc[idx_entry-1]
            old_row2 = self.df.loc[idx_entry+1]

            if (old_row1.row_type=='text'
                and old_row2.row_type=='text'):
                # join string rows
                new_row = (
                    old_row1.position,
                    "text",
                    None,
                    old_row1.depth,
                    old_row1.text + old_row2.text
                )
                self.df.drop(idx_entry+1, inplace=True)
                self.df.loc[idx_entry-1] = new_row

                self.df = self.df.reset_index(drop=True)

        self.df = self.df.reset_index(drop=True)

    def get_context_at_pos(self, pos):

        if not (self.df.position==pos).any():
            # pos not in self.df.position
            slice_ = self.df[np.logical_and(
                self.df.position < pos,
                self.df.row_type == "text"
            )]

            slice_ = slice_.iloc[-1]

        else:
            slice_ = self.df[np.logical_and(
                self.df.position == pos,
                self.df.row_type == "text"
            )].iloc[0]
        
        index = slice_.name

        cache = set()
        for irow in range(index, -1, -1):
            row = self.df.loc[irow]
            if row.row_type == "close":
                cache.add(row.el)
            if row.row_type == "open" and row.el not in cache:
                break
        parent = row.el

        context = [parent]
        while strip_ns(context[-1].getparent().tag) != "text":
            context.append(context[-1].getparent())
        context.append(context[-1].getparent())

        return Context(context[::-1])

        # slice_ = self.df[np.logical_and(
        #     self.df.position == pos,
        #     self.df.row_type == "text"
        # )].iloc[0]
        
        # parent = self.df[np.logical_or(
        #     self.df.row_type=="open",
        #     self.df.row_type=="close",
        # )].loc[:slice_.name][::-1]
        # cache = set()
        # for irow, row in parent.iterrows():
        #     if row.row_type == "close":
        #         cache.add(row.el)
        #     if row.row_type == "open" and row.el not in cache:
        #         break
        # parent = row.el

        # context = [parent]
        # while strip_ns(context[-1].getparent().tag) != "text":
        #     context.append(context[-1].getparent())
        # context.append(context[-1].getparent())

        # return Context(context[::-1])
            
    def collapse(self, include_empty_els=True):

        collapsed_table = []

        text_buffer = ""
        c_context = None
        
        for pos, new_context, txt in self.iter_positions(include_empty_els):
            
            # Deal with starting context
            if c_context is None and txt is not None:
                # first text item
                c_context = sc(new_context)

            if new_context != c_context and txt is not None:
                collapsed_table.append({
                    "context": c_context,
                    "text": text_buffer
                })
                text_buffer = ""

                c_context = sc(new_context)
            
            # include empty elements
            el = new_context[-1]
            if is_empty_el(el):
                if len(text_buffer)>0:
                    collapsed_table.append({
                        "context": c_context,
                        "text": text_buffer
                    })
                    text_buffer = ""

                collapsed_table.append({
                    "context": new_context,
                    "text": ""
                })

            text_buffer += txt if txt is not None else ""
        
        # include trailing text
        if text_buffer != "":
            collapsed_table.append({
                "context": c_context,
                "text": text_buffer
            })
        
        return pd.DataFrame(collapsed_table)