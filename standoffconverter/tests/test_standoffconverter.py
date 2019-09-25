import unittest
from lxml import etree

import standoffconverter

input_xml1 = b'''<W><text type='a'>A B C</text></W>'''
input_xml2 = b'''<W><text type='a'>The answer is 42.</text></W>'''

class TestStandoffConverter(unittest.TestCase):

    def test_from_lxml_tree_plain(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        self.assertTrue(so.plain == "A B C")
    
    def test_from_lxml_tree_standoff(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        self.assertTrue(so.standoffs[0]["begin"] == 0)
        self.assertTrue(so.standoffs[-1]["begin"] == 0)
        self.assertTrue(so.standoffs[0]["end"] == len(so.plain))
        self.assertTrue(so.standoffs[-1]["end"] == len(so.plain))

    def test_to_xml(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        output_xml = so.to_xml()
        self.assertTrue(input_xml1.decode("utf-8") == output_xml)

    def test_add_annotation(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        so.add_annotation(0,1,"xx",0,{"resp":"machine"})
        output_xml = so.to_xml()
        expected_out = "<W><text type='a'><xx resp='machine'>A</xx> B C</text></W>"
        self.assertTrue(expected_out == output_xml)

    def test_is_duplicate_annotation(self):
        tree = etree.fromstring(input_xml1)
        so = standoffconverter.Standoff.from_lxml_tree(tree)
        self.assertTrue(
            so.is_duplicate_annotation(0,len(so.plain), "W", {})
        )

    # def test_add_spacy_annotations(self):
        
    #     tree = etree.fromstring(input_xml2)
    #     so = standoffconverter.Standoff()
    #     so.from_lxml_tree(tree)

    #     spacified = nlp(so.plain)
    #     inds = []
    #     labels = []
    #     attributes = []
    #     for itoken, token in enumerate(spacified):
    #         if token.is_digit:
    #             inds.append(itoken)
    #             labels.append("digit")
    #             attributes.append({"resp":"spacy"})

    #     so.add_spacy_annotations(spacified, inds, labels, attributes)
        
    #     output_xml = so.to_xml()
    #     expected_output = "<W><text type='a'>The answer is <digit resp='spacy'>42</digit>.</text></W>"
    #     self.assertTrue(expected_output == output_xml)

if __name__ == '__main__':
    unittest.main()