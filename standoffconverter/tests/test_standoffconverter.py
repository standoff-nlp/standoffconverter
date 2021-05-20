import unittest
import os
from lxml import etree

import standoffconverter

input_xml1 = b'''<TEI><teiHeader></teiHeader><text><body><p>1 2 3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text></TEI>'''

input_xml2 = b'''<TEI><teiHeader></teiHeader><text><body><p>1 2\n3 4   \n 5 6\t 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text></TEI>'''

input_xml3 = b'''<TEI><teiHeader></teiHeader><text><body><p>1 2\n3 4 <lb/>  \n 5 6\t 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text></TEI>'''


file_xml1 = os.path.join(os.path.dirname(__file__), 'xml1.xml')

class TestStandoffConverter(unittest.TestCase):


    def test_from_tree_plain(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        self.assertTrue(so.plain == '1 2 3 4 5 6 7 9 10 11 12 13 14')
    
    # def test_from_tree_standoff(self):
    #     tree = etree.fromstring(input_xml1)
    #     so = standoffconverter.Standoff(tree)
    #     # TODO back to tree?

    def test_add_annotation_1(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        so.add_inline(
            begin=0,
            end=1,
            tag="xx",
            depth=None,
            attrib={"resp":"machine"}
        )
        output_xml = etree.tostring(so.text_el).decode("utf-8")
        expected_out = '''<text><body><p><xx resp="machine">1</xx> 2 3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>'''

        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_2(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        so.add_inline(
            begin=0,
            end=1,
            tag="xx",
            depth=None,
            attrib={"resp":"machine"}
        )

        so.add_inline(
            begin=2,
            end=3,
            tag="xx",
            depth=None,
            attrib={"resp":"machine"}
        )
        output_xml = etree.tostring(so.text_el).decode("utf-8")
        expected_out = '<text><body><p><xx resp="machine">1</xx> <xx resp="machine">2</xx> 3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>'

        # print(expected_out)
        # print(output_xml)

        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_3(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        so.add_inline(
            begin=2,
            end=3,
            tag="xx",
            depth=3,
            attrib={"resp":"machine"}
        )
        so.add_inline(
            begin=2,
            end=3,
            tag="vv",
            depth=3,
            attrib={"resp":"machine"}
        )
        output_xml = etree.tostring(so.text_el).decode("utf-8")

        expected_out = '<text><body><p>1 <vv resp="machine"><xx resp="machine">2</xx></vv> 3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>'

        # print(expected_out)
        # print(output_xml)

        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_4(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        so.add_inline(
            begin=2,
            end=3,
            tag="xx",
            depth=3,
            attrib={"resp":"machine"}
        )
        so.add_inline(
            begin=2,
            end=3,
            tag="vv",
            depth=4,
            attrib={"resp":"machine"}
        )
        output_xml = etree.tostring(so.text_el).decode("utf-8")

        expected_out = '<text><body><p>1 <xx resp="machine"><vv resp="machine">2</vv></xx> 3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>'
        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_5(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        so.add_inline(
            begin=4,
            end=4,
            tag="xx",
            depth=3,
            attrib={"resp":"machine"}
        )

        output_xml = etree.tostring(so.text_el).decode("utf-8")

        expected_out = '<text><body><p>1 2 <xx resp="machine"/>3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>'

        # print(output_xml)
        # print(expected_out)

        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_6(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        so.add_inline(
            begin=4,
            end=4,
            tag="xx",
            depth=3,
            attrib={"resp":"machine"}
        )

        so.add_inline(
            begin=5,
            end=5,
            tag="xx",
            depth=3,
            attrib={"resp":"machine"}
        )

        output_xml = etree.tostring(so.text_el).decode("utf-8")

        expected_out = '<text><body><p>1 2 <xx resp="machine"/>3<xx resp="machine"/> 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>'

        # print(output_xml)
        # print(expected_out)

        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_fail1(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        with self.assertRaises(ValueError):

            so.add_inline(
                begin=17,
                end=19,
                tag="xx",
                depth=3,
                attrib={"resp":"machine"}
            )
            output_xml = etree.tostring(so.text_el).decode("utf-8")
            # print(output_xml)

    def test_add_annotation_fail2(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        so.add_inline(
            begin=2,
            end=4,
            tag="xx",
            depth=None,
            attrib={"resp":"machine"}
        )
        with self.assertRaises(ValueError):
            so.add_inline(
                begin=3,
                end=5,
                tag="xx",
                depth=None,
                attrib={"resp":"machine"}
            )

    def test_add_empty_element(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)

        so.add_inline(
            begin=1,
            end=1,
            tag="lb",
            depth=None,
            attrib={}
        )
        output_xml = etree.tostring(so.text_el).decode("utf-8")

        expected_out = '''<text><body><p>1<lb/> 2 3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>'''

        self.assertTrue(expected_out == output_xml)

    def test_add_empty_element_2(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)

        so.add_inline(
            begin=1,
            end=1,
            tag="lb",
            depth=None,
            attrib={}
        )

        so.add_inline(
            begin=3,
            end=3,
            tag="lb",
            depth=None,
            attrib={}
        )

        so.add_inline(
            begin=3,
            end=4,
            tag="s",
            depth=None,
            attrib={}
        )
        output_xml = etree.tostring(so.text_el).decode("utf-8")

        expected_out = '''<text><body><p>1<lb/> 2<s><lb/> </s>3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>'''


        self.assertTrue(expected_out == output_xml)

    def test_remove_empty_element(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        to_remove = so.standoffs[-1]
        so.remove_inline(to_remove['el'])
        output_xml = etree.tostring(so.text_el).decode("utf-8")
        expected_out = '''<text><body><p>1 2 3 4 5 6 7 9 10</p><p> 11 12 13 14</p></body></text>'''

        self.assertTrue(expected_out == output_xml)

    def test_collapsed_table_1(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        collapsed_table = so.collapsed_table

        self.assertTrue(collapsed_table.iloc[0].text == "1 2 3 4 5 6 7 9 10")
        self.assertTrue(collapsed_table.iloc[3].text == " 12 13 14")

    def test_collapsed_table_2(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        collapsed_table = so.collapsed_table
        self.assertTrue(
            str(collapsed_table.iloc[0].context) == "text>body>p"
        )
    
    def test_json(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        output_json = so.json
        expected_out = '[{"tag": "text", "attrib": {}, "begin": 0, "end": 30, "depth": 0}, {"tag": "body", "attrib": {}, "begin": 0, "end": 30, "depth": 1}, {"tag": "p", "attrib": {}, "begin": 0, "end": 18, "depth": 2}, {"tag": "p", "attrib": {}, "begin": 18, "end": 30, "depth": 2}, {"tag": "lb", "attrib": {}, "begin": 21, "end": 21, "depth": 3}]'
        self.assertTrue(expected_out == output_json)


    def test_view_exclude_1(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        so.add_inline(
            begin=2,
            end=4,
            tag="xx",
            depth=None,
            attrib={"resp":"machine"}
        )
        view = standoffconverter.View(so.table)
        
        view = view.exclude_inside(["xx"])
        plain, lookup = view.get_plain()

        self.assertTrue(
            so.table.df.iloc[
                lookup.get_table_index(plain.index("5"))
            ].text == "5"
        )

    def test_view_exclude_2(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        so.add_inline(
            begin=2,
            end=5,
            tag="xx",
            depth=None,
            attrib={"resp":"machine"}
        )
        view = standoffconverter.View(so.table)
        
        view = view.exclude_outside(["xx"])
        plain, lookup = view.get_plain()
         
        self.assertTrue(
            plain == '2 3'
        )

    def test_view_shrink_whitespace_1(self):
        tree = etree.fromstring(input_xml2)
        so = standoffconverter.Standoff(tree)
        view = standoffconverter.View(so.table)
        view = view.shrink_whitespace()
        plain, lookup = view.get_plain()

        self.assertTrue(
            so.table.df.iloc[
                lookup.get_table_index(plain.index("7"))
            ].text == "7"
        )
        self.assertTrue(
            plain == '1 2\n3 4 5 6 7 9 10 11 12 13 14'
        )

    
    def test_view_shrink_whitespace_2(self):
        tree = etree.fromstring(input_xml3)
        so = standoffconverter.Standoff(tree)
        view = standoffconverter.View(so.table)
        view = view.shrink_whitespace()
        plain, lookup = view.get_plain()
        self.assertTrue(
            plain == '1 2\n3 4 5 6 7 9 10 11 12 13 14'
        )

    def test_view_insert_tag_text(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        
        view = standoffconverter.View(so.table)
        view.insert_tag_text("lb", "\n")

        plain, lookup = view.get_plain()

        self.assertTrue(
            so.table.df.iloc[
                lookup.get_table_index(plain.index("12"))
            ].text == "1"
        )

        self.assertTrue(
            plain == '1 2 3 4 5 6 7 9 10 11\n 12 13 14'
        )

    def test_remove_annotation(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        to_remove = so.standoffs[2]
        so.remove_inline(to_remove["el"])
        output_xml = etree.tostring(so.text_el).decode("utf-8")
        expected_output = '<text><body>1 2 3 4 5 6 7 9 10<p> 11<lb/> 12 13 14</p></body></text>'
        self.assertTrue(
            output_xml == expected_output
        )

    def test_add_remove_annotation1(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        
        for _ in range(5):
            so.add_inline(
                begin=2,
                end=3,
                tag="vv",
                depth=None,
                attrib={"resp":"machine"}
            )

            to_remove = [it['el'] for it in so.standoffs if it["el"].tag =='vv'][0]
            # import pdb; pdb.set_trace()
            so.remove_inline(to_remove)

        output_xml = etree.tostring(so.text_el).decode("utf-8")
        expected_output = "<text><body><p>1 2 3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>"
        # print(expected_output)
        # print(output_xml)

        self.assertTrue(
            output_xml == expected_output
        )

    def test_add_remove_annotation2(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
        
        for _ in range(5):
            so.add_inline(
                begin=2,
                end=3,
                tag="vv",
                depth=3,
                attrib={"resp":"machine"}
            )
        for _ in range(5):
            to_remove = [it["el"] for it in so.standoffs if it["el"].tag =='vv'][0]
            so.remove_inline(to_remove)

        output_xml = etree.tostring(so.text_el).decode("utf-8")

        expected_output = "<text><body><p>1 2 3 4 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>"

        self.assertTrue(
            output_xml == expected_output
        )
        
    def test_span_1(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
    
        so.add_span(
            begin=2,
            end=7, 
            tag="span",
            depth=None,
            attrib=None,
            id_="test1"
            )
        
        output_xml = etree.tostring(so.text_el).decode("utf-8")
        expected_output = "<text><body><p>1 <span spanTo=\"test1\"/>2 3 4<anchor id=\"test1\"/> 5 6 7 9 10</p><p> 11<lb/> 12 13 14</p></body></text>"

        self.assertTrue(
            output_xml == expected_output
        )

    def test_span_2(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff(tree)
    
        so.add_span(
            begin=2,
            end=22, 
            tag="span",
            depth=None,
            attrib=None,
            id_="test2"
            )
        
        output_xml = etree.tostring(so.text_el).decode("utf-8")
        expected_output = "<text><body><p>1 <span spanTo=\"test2\"/>2 3 4 5 6 7 9 10</p><p> 11<lb/> <anchor id=\"test2\"/>12 13 14</p></body></text>"
        self.assertTrue(
            output_xml == expected_output
        )

if __name__ == '__main__':
    unittest.main()
