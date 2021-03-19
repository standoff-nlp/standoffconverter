import numpy as np
import pandas as pd

from .utils import strip_ns, is_empty_el

class Context(list):
    """list of etree.Elements that define the context of a position."""
    def __str__(self):
        return ">".join(map(lambda x: x.tag, self))

    def strip_ns(self):
        return ">".join(map(lambda ctx: strip_ns(ctx.tag), self))

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
        return "".join(self.df[~self.df.text.isnull()].text)

    def set_el(self, el, map_):        
        for k,v in map_.items():
            assert k in ['el', 'position', 'row_type', 'depth', 'text']
            indices = self.df.loc[self.df.el == el, k].index
            for index in indices:
                self.df.at[index, k] = v

    def insert_open(self, pos, el, new_depth):
        row_type = "open"
        slice_ = self.df[self.df.position == pos]
        after_pos = np.ravel(np.argwhere(~(slice_.depth<new_depth).values))[0]
        index = slice_.iloc[after_pos].name-.5
        self.df.loc[index] = (pos, row_type, el, new_depth, None)
        self.df = self.df.sort_index().reset_index(drop=True)

    def insert_close(self, pos, el, new_depth):
        row_type = "close"
        slice_ = self.df[self.df.position == pos]
        after_pos = np.ravel(np.argwhere(~(slice_.depth>new_depth).values))[0]
        index = slice_.iloc[after_pos].name-.5
        self.df.loc[index] = (pos, row_type, el, new_depth, None)
        self.df = self.df.sort_index().reset_index(drop=True)

    def insert_empty(self, pos, el, new_depth, tail_text="open"):
        row_type = "empty"
        slice_ = self.df[self.df.position == pos]
        
        if tail_text == "text":
            chosen_ind = np.ravel(np.argwhere(~(slice_.depth<new_depth).values))[0]
        else:
            chosen_ind = np.ravel(np.argwhere(~(slice_.depth>new_depth).values))[0]
        
        index = slice_.iloc[chosen_ind].name-.5
        self.df.loc[index] = (pos, row_type, el, new_depth, None)
        self.df = self.df.sort_index().reset_index(drop=True)

    def remove_el(self, el):
        index = self.df[self.df.el == el].index
        self.df.drop(index, inplace=True)
        self.df = self.df.reset_index(drop=True)

    def get_context_at_pos(self, pos):
        slice_ = self.df[np.logical_and(
            self.df.position == pos,
            self.df.row_type == "text"
        )].iloc[0]
        
        parent = self.df[np.logical_or(
            self.df.row_type=="open",
            self.df.row_type=="close",
        )].loc[:slice_.name][::-1]
        cache = set()
        for irow, row in parent.iterrows():
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
            
    def collapse(self, include_empty_els=True):

        collapsed_table = []

        text_buffer = ""
        c_context = None
        
        for pos, new_context, txt in self.iter_positions(include_empty_els):
            
            # Deal with starting context
            if c_context is None and txt is not None:
                # first text item
                c_context = new_context

            if new_context != c_context and txt is not None:

                collapsed_table.append({
                    "context": c_context.strip_ns(),
                    "text": text_buffer
                })
                text_buffer = ""

                c_context = new_context
            
            # include empty elements
            if len(new_context) == 0:
                import pdb; pdb.set_trace()
            el = new_context[-1]
            if is_empty_el(el):
                if len(text_buffer)>0:
                    collapsed_table.append({
                        "context": c_context.strip_ns(),
                        "text": text_buffer
                    })
                    text_buffer = ""

                collapsed_table.append({
                    "context": new_context.strip_ns(),
                    "text": ""
                })

            text_buffer += txt if txt is not None else ""
        
        # include trailing text
        if text_buffer != "":
            collapsed_table.append({
                "context": c_context.strip_ns(),
                "text": text_buffer
            })
        
        return pd.DataFrame(collapsed_table)