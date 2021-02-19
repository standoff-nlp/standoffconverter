from lxml import etree
from standoffconverter import Converter

input_xml = '''<TEI><teiHeader></teiHeader><text><body><p>1 2 3 4 5 6 7 9 10</p><p> 11 12 13 14</p></body></text></TEI>'''

if __name__ == "__main__":
      
	print("INPUT XML:")
	print(input_xml)

	tree = etree.fromstring(input_xml)
	converter = Converter(tree)

	with converter.cached_standoff():

		converter.add_inline(
			begin=4,
			end=7,
			tag="threefour",
			attrib={"resp":"David Lassner"},
			depth=None,
		)

		print("Collapsed view:")
		print(converter.collapsed_table)

	new_xml = etree.tostring(converter.text_el).decode("utf-8")

	print("\n\n####\nOUTPUT XML")

	print(new_xml)