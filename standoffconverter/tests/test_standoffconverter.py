import unittest
import os
from lxml import etree

import standoffconverter

input_xml1 = b'''<TEI><teiHeader></teiHeader><text><body><p>1 2 3 4 5 6 7 9 10</p><p> 11 12 13 14</p></body></text></TEI>'''


file_xml1 = os.path.join(os.path.dirname(__file__), 'xml1.xml')

class TestStandoffConverter(unittest.TestCase):

    def test_from_tree_plain(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
        with so.cached_standoff(): 
            self.assertTrue(so.plain == '1 2 3 4 5 6 7 9 10 11 12 13 14')
    
    def test_from_tree_standoff(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
        with so.cached_standoff():
            self.assertTrue(so.table.iloc[0].sos[0].begin == 0)
            self.assertTrue(so.table.iloc[-1].sos[0].begin == 0)
            self.assertTrue(so.table.iloc[0].sos[0].end == len(so.plain))
            self.assertTrue(so.table.iloc[-1].sos[0].end == len(so.plain))

    def test_add_annotation_1(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
        so.add_inline(
            begin=0,
            end=1,
            tag="xx",
            depth=None,
            attrib={"resp":"machine"}
        )
        output_xml = etree.tostring(so.text_el).decode("utf-8")
        expected_out = '''<text><body><p><xx resp="machine">1</xx> 2 3 4 5 6 7 9 10</p><p> 11 12 13 14</p></body></text>'''

        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_2(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
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
        expected_out = '<text><body><p><xx resp="machine">1</xx> <xx resp="machine">2</xx> 3 4 5 6 7 9 10</p><p> 11 12 13 14</p></body></text>'
        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_3(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
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

        expected_out = '<text><body><p>1 <vv resp="machine"><xx resp="machine">2</xx></vv> 3 4 5 6 7 9 10</p><p> 11 12 13 14</p></body></text>'
        self.assertTrue(expected_out == output_xml)

    def test_add_annotation_4(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
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

        expected_out = '<text><body><p>1 <xx resp="machine"><vv resp="machine">2</vv></xx> 3 4 5 6 7 9 10</p><p> 11 12 13 14</p></body></text>'
        self.assertTrue(expected_out == output_xml)

    def test_collapsed_table(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
        collapsed_table = so.collapsed_table
        self.assertTrue(collapsed_table.iloc[0].text == "1 2 3 4 5 6 7 9 10")
        self.assertTrue(collapsed_table.iloc[1].text == " 11 12 13 14")
    
    def test_json(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
        output_json = so.json
        expected_out = '[{"tag": "text", "attrib": {}, "begin": 0, "end": 30, "depth": 0}, {"tag": "body", "attrib": {}, "begin": 0, "end": 30, "depth": 1}, {"tag": "p", "attrib": {}, "begin": 0, "end": 18, "depth": 2}, {"tag": "p", "attrib": {}, "begin": 18, "end": 30, "depth": 2}]'
        self.assertTrue(expected_out == output_json)

    def test_remove_annotation(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
        to_remove = so.standoffs[2]

        so.remove_inline(to_remove)
        output_xml = etree.tostring(so.text_el).decode("utf-8")
        expected_output = '<text><body>1 2 3 4 5 6 7 9 10<p> 11 12 13 14</p></body></text>'
        self.assertTrue(
            output_xml == expected_output
        )

    def test_add_remove_annotation1(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
        so.ensure_cache()
        len_lookupel2so = len(so.el2so)
        len_lookupso2el = len(so.so2el)
        for _ in range(5):
            so.add_inline(
                begin=2,
                end=3,
                tag="vv",
                depth=4,
                attrib={"resp":"machine"}
            )

            to_remove = [it for it in so.standoffs if it.tag =='vv'][0]

            so.remove_inline(to_remove)

        self.assertTrue(len_lookupel2so == len(so.el2so))
        self.assertTrue(len_lookupso2el == len(so.so2el))

        output_xml = etree.tostring(so.text_el).decode("utf-8")

        expected_output = "<text><body><p>1 2 3 4 5 6 7 9 10</p><p> 11 12 13 14</p></body></text>"

        self.assertTrue(
            output_xml == expected_output
        )

    def test_add_remove_annotation2(self):

        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Converter(tree)
        so.ensure_cache()
        len_lookupel2so = len(so.el2so)
        len_lookupso2el = len(so.so2el)
        for _ in range(5):
            so.add_inline(
                begin=2,
                end=3,
                tag="vv",
                depth=4,
                attrib={"resp":"machine"}
            )
        for _ in range(5):
            to_remove = [it for it in so.standoffs if it.tag =='vv'][0]

            so.remove_inline(to_remove)

        self.assertTrue(len_lookupel2so == len(so.el2so))
        self.assertTrue(len_lookupso2el == len(so.so2el))

        output_xml = etree.tostring(so.text_el).decode("utf-8")

        expected_output = "<text><body><p>1 2 3 4 5 6 7 9 10</p><p> 11 12 13 14</p></body></text>"

        self.assertTrue(
            output_xml == expected_output
        )

if __name__ == '__main__':
    unittest.main()