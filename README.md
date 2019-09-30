# standoffconverter


I intended this package to be used in the following situation:
Given a bunch of XML files (e.g. standard TEI files), I would like to add new annotations (for example with an ML method). The workflow would then be

```
import standoffconverter as so
from standoffconverter import Filter as sofilter

# 1. load the original TEI file and convert it to standoff format
sobj = so.load("some_file.xml")

# 2. create new annotations (automatically) and add them to the original
so.add_annotation(begin, end, "SOMETAG", 0, {})

# 3. store the modified XML
sobj.save("some_new_file.xml")
```