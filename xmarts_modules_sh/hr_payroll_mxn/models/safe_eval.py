# -*- coding: utf-8 -*-
# flake8: noqa

import ast


class Transformer(ast.NodeTransformer):
    # Helper class to evaluate user input expression and raising exceptions
    # in case non allowed names and/or functions used
    ALLOWED_NAMES = set([
        'None', 'False', 'True', 'result',
        'sbc', 'smgvdf',  # available variables
    ])
    ALLOWED_NODE_TYPES = set([
        'Expression',  # a top node for an expression
        'Tuple',  # makes a tuple
        'Call',  # a function call (hint, Decimal())
        'Name',  # an identifier...
        'Load',  # loads a value of a variable with given identifier
        'BinOp',  # Generic class for binary operators.
        'Str',  # a string literal
        'Num',  # allow numbers too
        'List',  # and list literals
        'Dict',  # and dicts...
        'Add', 'Sub',  # and allow all operators
        'Mult', 'Div', 'Mod', 'Pow', 'LShift', 'RShift',
        'BitOr', 'BitXor', 'BitAnd', 'FloorDiv',
    ])

    def visit_Name(self, node):
        if node.id not in self.ALLOWED_NAMES:
            raise RuntimeError('Name access to %s is not allowed' % node.id)

        # traverse to child nodes
        return self.generic_visit(node)

    def generic_visit(self, node):
        nodetype = type(node).__name__
        if nodetype not in self.ALLOWED_NODE_TYPES:
            raise RuntimeError('Invalid expression: %s not allowed' % nodetype)

        return ast.NodeTransformer.generic_visit(self, node)
