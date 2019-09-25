
def tree_to_standoff(tree):
    stand_off_props = {}
    plain = []

    def __traverse_and_parse(el, plain, stand_off_props, depth=0):
        stand_off_props[el] = {
            "begin": len(plain),
            "tag": el.tag,
            "attrib": el.attrib,
            "depth": depth
        }

        if el.text is not None:
            plain += [char for char in el.text]

        for gen in el:
            __traverse_and_parse(gen, plain, stand_off_props, depth=depth+1)

        depth -= 1
        stand_off_props[el]["end"] = len(plain)

        if el.tail is not None:
            plain += [char for char in el.tail]

    __traverse_and_parse(tree, plain, stand_off_props)
    return "".join(plain), [v for k,v in stand_off_props.items()]


class Standoff:
    
    def __init__(self, standoffs=None, plain=None):
        self.standoffs = [] if standoffs is None else standoffs
        self.plain = plain
 
    @classmethod
    def from_lxml_tree(cls, tree):
        """create a standoff representation from an lxml tree.

        arguments:
        tree -- the lxml object
        """
        plain, standoffs = tree_to_standoff(tree)
        return cls(standoffs, plain)

    def to_xml(self):
        """create a standoff representation from an lxml tree.

        returns:
        string -- the string containing the xml
        """
        assert self.plain is not None, "tree not yet initialized."

        standoff_begin_lookup = [[] for _ in range(len(self.plain)+1)]
        standoff_end_lookup = [[] for _ in range(len(self.plain)+1)]
        
        for v in self.standoffs:
            standoff_begin_lookup[v["begin"]] += [v]
            standoff_end_lookup[v["end"]] += [v]

        out_xml = ""

        offset = 0

        for ic in range(len(self.plain)+1):
            try:
                c = self.plain[ic]
            except IndexError:
                c = ""
            
            # add_closing tags
            new_str = ""
            sorted_end = sorted(
                sorted(standoff_end_lookup[ic], key=lambda x: -x["depth"]),
                key=lambda x: -(x["end"] - x["begin"])
            )

            for v in sorted_end:
                tag_str = "</{}>".format(v["tag"])
                new_str += tag_str

            out_xml += new_str
            offset += len(new_str)

            # add opening tags
            new_str = ""
            
            sorted_begin = sorted(
                sorted(standoff_begin_lookup[ic], key=lambda x: x["depth"]),
                key=lambda x: -(x["end"] - x["begin"])
            )

            for v in sorted_begin:

                attrib_str = " " + " ".join(
                    "{}='{}'".format(k_, v_) for k_, v_ in v["attrib"].items()
                )
                tag_str = "<{}{}>".format(
                    v["tag"],
                    attrib_str if len(attrib_str) > 1 else ""
                )
                new_str += tag_str

            out_xml += new_str
            offset += len(new_str)

            out_xml += c

        return out_xml

    def add_annotation(self, begin, end, tag, depth, attribute, unique=True):
        """add a standoff annotation.

        arguments:
        begin (int) -- the beginning character index
        end (int) -- the ending character index
        tag (str) -- the name of the xml tag
        depth (int) -- tree depth of the attribute. for the same begin and end, 
                 a lower depth annotation includes a higher depth annotation
        attribute (dict) -- attrib of the lxml

        keyword arguments:
        unique (bool) -- whether to allow for duplicate annotations
        """
        if not unique or not self.is_duplicate_annotation(begin, end, tag, attribute):
            self.standoffs.append({
                "begin": begin,
                "end": end,
                "tag": tag,
                "attrib": attribute,
                "depth": depth if depth is not None else 0
            })

    def is_duplicate_annotation(self, begin, end, tag, attribute):
        """check whether this annotation already in self.standoffs
        
        arguments:
        begin (int) -- the beginning character index
        end (int) -- the ending character index
        tag (str) -- the name of the xml tag
        attribute (dict) -- attrib of the lxml

        returns:
        bool -- True if annotation already exists
        """

        def attrs_equal(attr_a, attr_b):
            shared_items = {}
            for k in attr_a:
                if k in attr_b and attr_a[k] == attr_b[k]:
                    shared_items[k] = attr_a[k]

            return len(attr_a) == len(attr_b) == len(shared_items)

        for standoff in self.standoffs:
            if (standoff["begin"] == begin
                and standoff["end"] == end
                and standoff["tag"] == tag
                and attrs_equal(attribute, standoff["attrib"])):
                return True
        return False
            
    def add_spacy_annotations(self, doc, inds, labels, attributes, depths=None, unique=True):
        """add a standoff annotations from a spacy document.

        In order to add annotations from a spacy document, the annotations need to be 
        converted from token-level annotations to character-level annotations

        arguments:
        doc (spacy.tokens.Doc) -- A Document that was created from self.plain
        inds (list) -- the list of *token* indices
        labels (list) -- the list of labels to be used as XML tags
        attributes (list) -- the list of attributes (dicts) to be used as XML attributes

        keyword arguments:
        depths (list) -- list of depths for each attribute. The depth specifies the order 
                         of XML tags that have the same beginning and ending index.
                         for the same begin and end, a lower depth annotation includes 
                         a higher depth annotation.
        unique (bool) -- whether to allow for duplicate annotations
        """

        if depths is None:
            depths =  [None]*len(inds)
        
        assert (doc.text == self.plain), "spacy document does not fit the self.plain text."

        assert len(inds) == len(labels) == len(attributes) == len(depths), "new standoff\
         params have to have all same lengths."

        tokeni2idx = {t.i:(t.idx,t.idx+tchar) for t in doc for tchar in range(len(t.text)+1)} 

        for ind, label, attribute, depth in zip(inds, labels, attributes, depths):
            begin, end = tokeni2idx[ind]
            self.add_annotation(begin, end, label, depth, attribute, unique)