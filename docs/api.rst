API
===

.. autoclass:: standoffconverter.Converter
    
    .. automethod:: from_lxml_tree
    .. automethod:: to_tree
    .. automethod:: to_json
    .. automethod:: add_annotation
    .. automethod:: remove_annotation
    .. automethod:: transaction

    .. automethod:: __init__


.. autoclass:: standoffconverter.AnnotationPair
    
    .. automethod:: from_so
    .. automethod:: xpath
    .. automethod:: get_so
    .. automethod:: get_el
    .. automethod:: get_dict
    .. automethod:: get_tag
    .. automethod:: get_depth
    .. automethod:: get_attrib
    .. automethod:: get_begin
    .. automethod:: get_end
    .. automethod:: __init__