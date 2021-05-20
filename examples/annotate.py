import urllib.request
from lxml import etree
from standoffconverter import Standoff, View

import streamlit as st

import spacy
from spacy import displacy
from spacy_streamlit.util import get_html

def view_md_collapsed_table(collapsed_table):

    md_table_rows = []
    for _,row in collapsed_table.iterrows():
        # if row.text.strip() != "":
        text = row.text.replace("\n", "<br>")
        md_table_rows.append(f"|{row.context}|{text}|")

    return (
        "| Context       | Text          |\n"
        +"| ------------- |:-------------|\n"   
        +"\n".join(md_table_rows)
    )

url = "https://raw.githubusercontent.com/FloChiff/DAHNProject/master/Correspondence/Berlin_Intellectuals/Corpus/Brief105BoeckhanVarnhagen.xml"
response = urllib.request.urlopen(url)
xml_input_str = response.read()

#st.text(xml_input_str.decode('utf-8'))

tree = etree.fromstring(xml_input_str)

so = Standoff(tree, namespaces={"tei":"http://www.tei-c.org/ns/1.0"})

st.write("# Input XML")
st.text(etree.tostring(so.text_el).decode("utf-8"))

st.write("# Collapsed Standoff Table View")

st.markdown(view_md_collapsed_table(so.collapsed_table), unsafe_allow_html=True)

st.write("# The Filtered Text")

view = (
    View(so.table)
        .exclude([
            "{http://www.tei-c.org/ns/1.0}note",
            "{http://www.tei-c.org/ns/1.0}abbr"
        ])
        .shrink_whitespace()
        .insert_tag_text(
            "{http://www.tei-c.org/ns/1.0}lb",
            "\n"
        )
        .insert_tag_text(
            "{http://www.tei-c.org/ns/1.0}milestone",
            "\n"
        )
)

plain, lookup = view.get_plain()
st.text(plain)

st.write("# Spacy NER solution")

model_identifier = "de_core_news_lg"
nlp = spacy.load(model_identifier)
doc = nlp(plain)

html = displacy.render(
    doc, style="ent"#, options={"ents": ["PERSON"], "colors": {}}
)

style = "<style>mark.entity { display: inline-block }</style>"

st.write(f"{style}{get_html(html)}", unsafe_allow_html=True)

st.write("# Embed solution into TEI")

for ent in doc.ents:
    if ent.label_ in ["PER"]:
        try:
            start_ind = lookup.get_pos(ent.start_char)
            end_ind = lookup.get_pos(ent.end_char+1)

            so.add_inline(
                begin=start_ind,
                end=end_ind,
                tag="spacyPersName",
                depth=None,
                attrib={"resp": model_identifier}
            )
        except ValueError:
            so.add_span(
                str(hash(ent)),
                begin=start_ind,
                end=end_ind,
                tag="spacyPersName",
                depth=None,
                attrib={"resp": model_identifier}
            )

st.markdown(view_md_collapsed_table(so.collapsed_table), unsafe_allow_html=True)

st.write("# Output XML")
st.text(etree.tostring(so.text_el).decode("utf-8"))