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

    # def test_add_annotation_3(self):
    #     tree = etree.fromstring(input_xml1)
    #     so = standoffconverter.Converter.from_tree(tree)
    #     # so.add_annotation(0,1,"xx",0,{"resp":"machine"})
    #     so.add_annotation(2,3,"xx",0,{"resp":"machine"})
    #     output_xml = etree.tostring(so.tree).decode("utf-8")
    #     expected_out = '<W><text type="a">A <xx resp="machine">B</xx> C</text></W>'
    #     self.assertTrue(expected_out == output_xml)

    # def test_add_annotation_4(self):
    #     tree = etree.fromstring(input_xml1)
    #     so = standoffconverter.Converter.from_tree(tree)
    #     # so.add_annotation(0,1,"xx",0,{"resp":"machine"})
    #     so.add_annotation(2,3,"xx",0,{"resp":"machine"})
    #     so.add_annotation(2,3,"vv",1,{"resp":"machine"})
    #     output_xml = etree.tostring(so.tree).decode("utf-8")
    #     expected_out = '<W><text type="a">A <xx resp="machine"><vv resp="machine">B</vv></xx> C</text></W>'
    #     self.assertTrue(expected_out == output_xml)

    # def test_is_duplicate_annotation(self):
    #     tree = etree.fromstring(input_xml1)
    #     so = standoffconverter.Converter.from_tree(tree)
    #     self.assertTrue(
    #         so._Converter__is_duplicate_annotation(0,len(so.plain), "W", {})
    #     )

    # def test_remove_annotation(self):
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)
    #     to_remove = converter.collection[0]
    #     converter.remove_annotation(to_remove)
    #     output_xml = etree.tostring(converter.tree).decode("utf-8")
    #     expected_output = '<text type="a">A B C</text>'
    #     self.assertTrue(
    #         output_xml == expected_output
    #     )

    # def test_transaction(self):

    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     with converter.transaction("standoff"):
    #         converter.add_annotation(0,1,"xx",0,{"resp":"machine"})
    #         converter.add_annotation(2,3,"xx",0,{"resp":"machine"})

    #     output_xml = etree.tostring(converter.tree).decode("utf-8")
    #     expected_out = '<W><text type="a"><xx resp="machine">A</xx> <xx resp="machine">B</xx> C</text></W>'
    #     self.assertTrue(expected_out == output_xml)

    # def test_to_tree(self):

    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     self.assertTrue(
    #         converter.to_tree() == tree
    #     )

    # def test_to_json(self):
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)
    #     json = converter.to_json()
    #     expected_output = '[{"begin": 0, "end": 5, "attrib": {}, "depth": 0, "tag": "W"}, {"begin": 0, "end": 5, "attrib": {"type": "a"}, "depth": 1, "tag": "text"}]'
    #     self.assertTrue(
    #         json == expected_output
    #     )

    # def test_annotationpair_from_so(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     pair = converter.collection[0]
    #     orig_el = pair.get_el()
    #     so = pair.get_so()
    #     new_el = AnnotationPair.from_so(so, converter)
        
    #     self.assertTrue(
    #         new_el.get_tag() == orig_el.tag
    #     )
        
    #     for k,v in orig_el.attrib.items():
    #         self.assertTrue(
    #             k in new_el.get_attrib() and new_el.get_attrib()[k] == v
    #         )

    # def test_annotationpair_get_so(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     self.assertTrue(
    #         converter.collection[0].get_so() == converter.collection[0].so
    #     )

    # def test_annotationpair_get_el(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     self.assertTrue(
    #         converter.collection[0].get_el() == converter.collection[0].el
    #     )

    # def test_annotationpair_xpath(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     root_el = converter.tree
    #     root_pair = converter.el2pair[root_el]

    #     result = root_pair.xpath("//text")

    #     self.assertTrue(
    #         result[0].get_tag() == "text"
    #     )

    # def test_annotationpair_find(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     root_el = converter.tree
    #     root_pair = converter.el2pair[root_el]

    #     result = root_pair.find(".//text")

    #     self.assertTrue(
    #         result.get_tag() == "text"
    #     )

    # def test_annotationpair_get_tag(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     self.assertTrue(
    #         converter.collection[0].get_tag() == converter.collection[0].so.tag
    #     )

    # def test_annotationpair_get_depth(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     self.assertTrue(
    #         converter.collection[0].get_depth() == converter.collection[0].so.depth
    #     )

    # def test_annotationpair_get_attrib(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     true_attrib = converter.collection[0].so.attrib
    #     new_attrib = converter.collection[0].get_attrib()
        
    #     self.assertTrue(
    #         len(new_attrib) == len(true_attrib)
    #     )

    #     for k,v in true_attrib.items():
    #         self.assertTrue(
    #             k in new_attrib and new_attrib[k] == v
    #         )

    # def test_annotationpair_get_begin(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)


    #     self.assertTrue(
    #         converter.collection[0].get_begin() == converter.collection[0].so.begin
    #     )

    # def test_annotationpair_get_end(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)

    #     self.assertTrue(
    #         converter.collection[0].get_end() == converter.collection[0].so.end
    #     )

    # def test_annotationpair_get_dict(self):
        
    #     tree = etree.fromstring(input_xml1)
    #     converter = standoffconverter.Converter.from_tree(tree)
    #     true_dict = {
    #         "tag" : "text",
    #         "attrib": {
    #             "type": "a"
    #         },
    #         "begin":0,
    #         "end":5,
    #         "depth":1
    #     }
    #     new_dict = converter.collection[1].get_dict()

    #     for k,v in true_dict.items():
    #         if isinstance(v, str) or isinstance(v, int):
    #             self.assertTrue(
    #                 k in new_dict and new_dict[k] == v
    #             )

    #     for k,v in true_dict["attrib"].items():
    #         if isinstance(v, str) or isinstance(v, int):
    #             self.assertTrue(
    #                 k in new_dict["attrib"] and new_dict["attrib"][k] == v
    #             )


if __name__ == '__main__':
    unittest.main()