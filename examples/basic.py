from lxml import etree
import standoffconverter.Converter as Co

input_xml = '''
<W>
  <header>
    <date>
      2019
    </date>
    <location>
      Berlin, Germany
    </location>
  </header>
  <text type="a">
    Lorem ipsum dolor sit amet, <add>consetetur</add> sadipscing <del>elitr</del>, <note resp="David Lassner">sed</note> diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.
  </text>
</W>
'''

if __name__ == "__main__":
      
      print("INPUT XML:")
      print(input_xml)
      
      tree = etree.fromstring(input_xml)
      
      converter = Co.from_tree(tree)
      
      t = "aliquyam"
      begin = converter.plain.index(t)
      end = begin + len(t)
      converter.add_annotation(begin, end, "del", 0, {"resp": "David Lassner"})

      new_xml = etree.tostring(converter.to_tree(), encoding=str)

      print("\n\n####\nOUTPUT XML")

      print(new_xml)