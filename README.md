# standoffconverter

## Simple use case
I intended this package to be used in the following situation:
Given a collection of TEI files, I would like to add new annotations (for example with an ML method). The workflow would include the following steps:

1. create a standoff representation of the lxml Tree (`so = Standoff(some_xml_tree)`)
2. create a view of the standoff data that works well for NLP methods, such as converting `<lb>` into `\n` or strip multiple white spaces into a single one (`view = View(so.table).shrink_whitespace().insert_tag_text({"{http://www.tei-c.org/ns/1.0}lb": "\n",})`). The resulting text can be retrieved by `plain, lookup = view.get_plain()`, note that a lookup table is also returned that keeps the links between the character position in `plain` and its original position in the `so.table`. 
3. pass the resulting plain text into an NLP pipeline and retrieve results on character level (for example Named Entities): 
```
for ent in nlp(plain).ents:
    break;
```
4. use the lookups to annotate the original lxml Tree
```
start_ind = lookup.get_pos(ent.start_char)
end_ind = lookup.get_pos(ent.end_char+1)

so.add_inline(
    begin=start_ind,
    end=end_ind,
    tag="entity",
)
```
## Examples
[Find more examples here](https://github.com/standoff-nlp/standoffconverter/tree/master/examples)
# Documentation
[https://standoffconverter.readthedocs.io](https://standoffconverter.readthedocs.io/)
