from lxml import etree
from standoffconverter import Converter
from tqdm import tqdm
import random

def main():

    init_tree = etree.Element("root")
    sub = etree.Element("sub")
    init_tree.append(sub)
    sub.text = "abc"*200
    converter = Converter.from_tree(init_tree)
    
    ii = list(range(1, len(sub.text)//2-1))
    random.shuffle(ii)

    for i in tqdm(ii, desc="add many elements"):
        converter.add_annotation(i,len(sub.text)-i, "sometag", 0, {})

if __name__ == "__main__":
    import cProfile

    cProfile.run('main()', "stats")

    import pstats
    p = pstats.Stats('stats')
    p.sort_stats('cumulative').print_stats(15)