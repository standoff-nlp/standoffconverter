



# def standoff_to_tree(so, plain):
#     """convert the standoff representation to a etree representation

#     arguments:
#         so -- standoff object

#     returns:
#         tree (str) -- the root element of the resulting tree
#     """
#     order = __get_order_for_traversal(so)

#     pos_to_so = [[] for _ in range(len(converter.plain))]

#     for c_so in order:
        
#         el = create_el_from_so(c_pair.so)

#         for pos in range(c_so["begin"], c_so["end"]):
#             pos_to_so[pos].append(el)
    
#     for i in range(len(plain)):
#         c_parents = pos_to_so[i]
#         for i_parent in range(len(c_parents)-1):
#             c_parent = c_parents[i_parent]
#             c_child = c_parents[i_parent+1]
#             if c_child not in c_parent:
#                 c_parent.append(c_child)
#         if len(c_parents[-1]) == 0:
#             if c_parents[-1].text is None:
#                 c_parents[-1].text = ""

#             c_parents[-1].text += plain[i]
#         else:
#             if c_parents[-1][-1].tail is None:
#                 c_parents[-1][-1].tail = ""
#             c_parents[-1][-1].tail += plain[i]

#     root = pos_to_so[0][0].el.getroottree().getroot()

#     return root
