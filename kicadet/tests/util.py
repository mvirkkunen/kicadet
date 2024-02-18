import unittest
from kicadet.node import Node
from kicadet.sexpr import sexpr_serialize, sexpr_parse

class TestCase(unittest.TestCase):
    def assertSexprEqual(self, node: Node, sexpr: str) -> None:
        self.maxDiff = None
        self.assertMultiLineEqual(
            node.serialize(),
            sexpr_serialize(sexpr_parse(sexpr)),
        )
