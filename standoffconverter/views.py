class View:

    def __init__(self, so, mask, replaces={"lb": "\n"}):
        
        # 1. apply argument mask
        self.filtered_table = dc(so.table[mask])


        # 2. strip all multiple whitespace and reduce it to one `" "`
        strip_mask = pd.Series(
            np.ones(len(self.filtered_table)),
            index=self.filtered_table.index,
            dtype=bool
        )

        grouper = (
            np.logical_and(
                self.filtered_table.text.shift(fill_value=" ").isin([' ', '\t', '\n']), 
                self.filtered_table.text.isin([' ', '\t', '\n'])
            )
        )

        for group_, subdf in self.filtered_table.groupby(grouper):
            if group_:
                group__ = grouper[grouper==group_].index
                strip_mask[group__[1:]] = False
                self.filtered_table[group__[0], "text"] = " "

        self.filtered_table.text = self.filtered_table.text.apply(lambda x: x.replace("\n", " "))
        self.filtered_table = self.filtered_table[strip_mask]

        # apply all argument replaces
        for from_,to in replaces.items():

            inds = self.filtered_table[
                self.filtered_table.context.apply(
                    lambda ctx: any([ctit.strip_ns() == from_ for ctit in ctx])
                )
            ].index

            self.filtered_table.loc[inds, "text"] = to

        self.viewinds2soinds = []
        for index, row in self.filtered_table.iterrows():
            for char in row.text:
                self.viewinds2soinds.append(
                    index[0]
                )
        self.plain = "".join(self.filtered_table.text)

    def standoff_char_pos(self, ind):
        return self.viewinds2soinds[ind]