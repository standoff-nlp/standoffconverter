from standoffconverter.standoffs import Standoff
import unittest

from datetime import datetime
import math
from unittest import result
from pandas.core.base import PandasObject
from lxml import etree

import standoffconverter
import pandas as pd

import cProfile
from itertools import product




class ProfileStandoffConverter(unittest.TestCase):

    """
    parameters to change
    * document length
    * item more at root position or more at leaf position
    * item length
    * add/delete
    """


    def __init__(self, testcase, document_depth, document_length, working_depth, item_length):

        self.document_length = document_length
        self.document_depth = document_depth
        self.working_depth = working_depth
        self.item_length = item_length
        super().__init__(testcase)


    def setUp(self):

        base_template = "<TEI><teiHeader></teiHeader><text><body>{}</body></text></TEI>"
        p_template = "<p>{}</p>"
        
        item = 's'*self.item_length
        
        doc_str_portions = ['d'*(math.ceil(self.document_length/self.document_depth))]*self.document_depth

        doc_str_portions[self.working_depth] += item
        
        self.item_start = "".join(doc_str_portions).index('s')
        self.item_end = self.item_start + self.item_length

        text_str = ""

        for portion in doc_str_portions[::-1]:
            text_str = p_template.format(portion + text_str)
        
        self.tree = etree.fromstring(base_template.format(text_str))
        
    def __speedtest(self):
        
        so = standoffconverter.Standoff(self.tree)
        so.add_inline(
            begin=self.item_start,
            end=self.item_end,
            tag="xx"
        )
        
    def speedtest(self):
        self.profile = cProfile.Profile()
        self.profile.enable()
        self.__speedtest()
        self.profile.disable()


def get_suite():
    suite = unittest.TestSuite()

    depths = [10, 50, 100]
    lengths = [100, 500, 1000]
    working_depths = [1, 3, -1]
    item_length = [10, 50]

    params = [
        depths,
        lengths,
        working_depths,
        item_length
    ]

    for param_set in product(*params):
        suite.addTest(ProfileStandoffConverter('speedtest', *param_set))

    return suite

def print_results(suite):

    results = []
    for testcase in suite:
        # print(f'document_length: {testcase.document_length}')
        # print(f'document_depth: {testcase.document_depth}')
        # print(f'working_depth: {testcase.working_depth}')
        # print(f'item_length: {testcase.item_length}')
        testcase.run()
    
        total_time = 0
        for profiler_entry in testcase.profile.getstats():
            if hasattr(profiler_entry.code, 'co_name') and profiler_entry.code.co_name == '__speedtest':
                total_time = profiler_entry.totaltime

        results.append({
            "document_length": testcase.document_length,
            "document_depth": testcase.document_depth,
            "working_depth": testcase.working_depth,
            "item_length": testcase.item_length,
            "tottime": total_time,
        })
    results = pd.DataFrame(results)

    fname = datetime.now().isoformat(timespec='seconds').replace(":","_")
    results.to_pickle(f'profiling/{fname}.pkl')


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    suite = get_suite()
    # runner.run(suite)
    print_results(suite)

