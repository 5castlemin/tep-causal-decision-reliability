import unittest
import networkx as nx
from src.causalman_do_contract_fixture import remove_incoming_for_fixture

class DoGraphFixtureTests(unittest.TestCase):
    def test_only_target_incoming_removed(self):
        g = nx.DiGraph([('u','a'),('v','a'),('a','m'),('m','y'),('u','y')])
        fixed = remove_incoming_for_fixture(g, 'a')
        self.assertEqual(set(fixed.in_edges('a')), set())
        self.assertEqual(set(fixed.edges()), {('a','m'),('m','y'),('u','y')})
        self.assertEqual(len(g.in_edges('a')), 2)
        def evaluate(graph):
            values = {}
            for node in nx.topological_sort(graph):
                values[node] = {'u': lambda: 3, 'v': lambda: 4,
                                'a': lambda: 16000,
                                'm': lambda: 2 * values['a'],
                                'y': lambda: values['m'] + values['u']}[node]()
            return values['y']
        self.assertEqual(evaluate(g), 32003)
        self.assertEqual(evaluate(fixed), evaluate(g))

    def test_source_and_isolated_nodes(self):
        g = nx.DiGraph(); g.add_nodes_from(['a','y']); g.add_edge('a','y')
        self.assertEqual(set(remove_incoming_for_fixture(g,'a').edges()), {('a','y')})
