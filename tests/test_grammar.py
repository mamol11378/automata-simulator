import unittest
from grammar import ContextFreeGrammar, EPSILON

class GrammarTests(unittest.TestCase):
    def test_first_follow(self):
        g=ContextFreeGrammar().parse("S -> a A\nA -> b A | ε")
        self.assertEqual(g.first_sets()["S"], {"a"})
        self.assertIn("$", g.follow_sets()["S"])
        self.assertIn("$", g.follow_sets()["A"])

    def test_parse_string(self):
        g=ContextFreeGrammar().parse("S -> a A\nA -> b A | ε")
        ok, tree, tokens = g.parse_string("abb")
        self.assertTrue(ok)
        self.assertIsNotNone(tree)

    def test_left_recursion(self):
        g=ContextFreeGrammar().parse("E -> E + T | T\nT -> id")
        g.remove_left_recursion()
        self.assertFalse(any(p.right and p.right[0] == p.left for p in g.productions))
