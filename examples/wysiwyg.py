import streamlit as st
from lxml import etree
from standoffconverter import Standoff, View


st.set_page_config(layout="wide")

st.write("## Interactive demo of the standoff converter")

col1, col2, col3 = st.beta_columns(3)


input_xml = col1.text_area(
    'input_xml:',
    value="""<TEI>
    <teiHeader></teiHeader>
    <text>
        <body>
            <p>1 2 3 4 5 6<lb/> 7 9 10</p>
            <p> 11 12 13 14</p>
        </body>
    </text>
</TEI>""",
    height=400,
    max_chars=300,
)



col2.text("collapsed table")

col2.code(
    """# 1. create standoff 
tree = etree.fromstring(input_xml)
so = Standoff(tree)
print(so.collapsed_table)"""
)
tree = etree.fromstring(input_xml)
so = Standoff(tree)

col2.write(so.collapsed_table)
col3.text("plain text")

view = (
    View(so.table)
        .shrink_whitespace()
        .insert_tag_text(
            "lb",
            "\n"
        )
)
plain, lookup = view.get_plain()

col3.code(
    """# 2. create view
view = (
    View(so.table)
        .shrink_whitespace()
        .insert_tag_text(
            "lb",
            "\\n"
        )
)
plain, lookup = view.get_plain()
print(plain)"""
)
col3.text(plain)

st.write('''
This demo shows the two steps involved to get from TEI XML to plain text. This way you can use standard NLP tools on your TEI documents. 

1. On the left side, you can modify the TEI document
2. In the center, the standoff view of the document is shown, where the text and the annotations are separated
3. On the right, a view of the document is created that (as an example) reduces the whitespace between tags and adds line breaks for `<lb/>` tags.  

[The code for this demo is available in our Github Repository](https://github.com/standoff-nlp/standoffconverter/blob/master/examples/wysiwyg.py)  

''')