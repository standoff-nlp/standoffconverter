import streamlit as st
from lxml import etree
from standoffconverter import Standoff, View


st.set_page_config(layout="wide")

st.write("# Interactive demo of the standoff converter")

st.write('''
This demo shows the steps involved to get from TEI XML to plain text, identify sentences and put the found sentences as `<s>` into the TEI. It illustrates how you can use standard NLP tools on your TEI documents. You can modify the input document to see how things change!

[The code for this demo is available in our Github Repository](https://github.com/standoff-nlp/standoffconverter/blob/master/examples/wysiwyg.py)  

''')

st.write("## TEI to plain text")



col1, col2, col3 = st.beta_columns(3)


input_xml = col1.text_area(
    'input_xml:',
    value="""<TEI>
<teiHeader> </teiHeader>
<text>
    <body>
        <p>1 2 3 4. 5 6<lb/> 7 9 10.</p>
        <p> 11 12 13 14</p>
    </body>
</text>
</TEI>
""",
    height=400,
    max_chars=300,
)



col2.write("1. Standoff representation")

col2.code(
    """# 1. create standoff 
tree = etree.fromstring(input_xml)
so = Standoff(tree)
print(so.collapsed_table)"""
)
tree = etree.fromstring(input_xml)
so = Standoff(tree)

col2.write(so.collapsed_table)
col3.write("2. Plain text view")

view = (
    View(so)
        .insert_tag_text(
            "lb",
            "\n"
        )
        .exclude_outside("p")
)

plain = view.get_plain()


col3.code(
    """# 2. create view
view = (
    View(so)
        .insert_tag_text(
            "lb",
            "\\n"
        )
        .exclude_outside("p")
)

plain = view.get_plain()
print(plain)"""
)
col3.text(plain)


st.write("## Apply spacy sentencizer and add `<s>`-tags")


col1, col2, col3 = st.beta_columns(3)
col1.write('3. Apply spacy sentencizer')
col1.code(
    """# 3. annotate with NLP 
# to split sentences 
from spacy.lang.en import English
nlp = English()
nlp.add_pipe('sentencizer')

sentences = []
for sent in nlp(plain).sents:
    col1.write(f"* {sent}")
    sentences.append(sent)
""")

from spacy.lang.en import English
nlp = English()
nlp.add_pipe('sentencizer')

col1.write('spacy found the following sentences:')
sentences = []
for sent in nlp(plain).sents:
    col1.write(f"* {sent}")
    sentences.append(sent)

col2.write('4. Add annotations')
col2.code(
    """# 4. retrieve results from spacy,
# resolve original character positions
# and add annotations to the tree
for isent, sent in enumerate(sentences):

    start_ind = view.get_table_pos(sent.start_char)
    end_ind = view.get_table_pos(sent.end_char-1)+1

    so.add_inline(
        begin=start_ind,
        end=end_ind,
        tag="s",
        depth=None,
        attrib={'id':f'{isent}'}
    )

""")
for isent, sent in enumerate(sentences):

    start_ind = view.get_table_pos(sent.start_char)
    end_ind = view.get_table_pos(sent.end_char-1)+1

    try:
        so.add_inline(
            begin=start_ind,
            end=end_ind,
            tag="s",
            depth=None,
            attrib={'id':f'{isent}'}
        )
    except (ValueError, IndexError):
        raise ValueError(f"Unable to add sentence tag for '{sent}'. It probably violates the tree constraint of XML.")

col3.write("final TEI")
col3.code(etree.tostring(so.tree).decode("utf-8"))
