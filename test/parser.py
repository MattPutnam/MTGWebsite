import unittest
from src.parser import Parser


def test(self, template, expected, data={}, depth=0):
    parser = Parser(data, depth)
    rendered = parser.evaluate(template)
    self.assertEqual(expected, rendered)


class ParserTest(unittest.TestCase):
    def test_no_tokens(self):
        test(self, template='this is some text', expected='this is some text')

    def test_variables(self):
        test(self,
             template="{{$local.greeting}}, {{$main.name.first}}!",
             expected='Hello, John!',
             data={'local': {'greeting': 'Hello'},
                   'main': {'name': {'first': 'John', 'last': 'Smith'}}})

    def test_nested_variables(self):
        test(self,
             template='{{$data.($data.keyA.keyB).keyC}}',
             expected='bar',
             data={'data': {'keyA': {'keyB': 'foo'},
                                  'foo': {'keyC': 'bar'}}})

    def test_foreach(self):
        test(self,
             template='{{$main.header}}\n'
                      '{{foreach:var=$foo, source=$main.data}}[test $foo]\n'
                      '{{end}}\n'
                      '{{$main.footer}}',
             expected='start\n'
                      '[test a]\n'
                      '[test b]\n'
                      '[test c]\n'
                      '\n'
                      'end',
             data={'main': {'header': 'start', 'data': ['a', 'b', 'c'], 'footer': 'end'}})

    def test_foreach_cartesian(self):
        test(self,
             template='{{foreach:var=$row, source=$data.rows}}'
                      '{{foreach:var=$col, source=$data.cols}}'
                      '[$row $col]'
                      '{{end}}{{end}}',
             expected='[1 A][1 B][1 C][2 A][2 B][2 C][3 A][3 B][3 C]',
             data={'data': {'rows': [1, 2, 3], 'cols': ['A', 'B', 'C']}})

    def test_resource(self):
        test(self, depth=2,
             template='<img src={{resource:file=test/file.txt}} />',
             expected='<img src=../../test/file.txt />')

    def test_resource_var(self):
        test(self, depth=1,
             template='<img src={{resource:file=$test.file}} />',
             expected='<img src=../graphic.png />',
             data={'test': {'file': 'graphic.png'}})

    def test_if_no_var(self):
        test(self,
             template='{{if:condition=$foo.dne}}{{$main.true}}\n'
                      '{{else}}{{$main.false}}\n'
                      '{{end}}',
             expected='expected\n',
             data={'main': {'true': 'Condition passed', 'false': 'expected'}})

    def test_if_true_bool(self):
        test(self,
             template='{{if:condition=$foo.hello}}YES{{end}}',
             expected='YES',
             data={'foo': {'hello': True}})

    def test_if_true_val(self):
        test(self,
             template='{{if:condition=$foo.hello}}YES{{end}}',
             expected='YES',
             data={'foo': {'hello': 'strings are truthy'}})

    def test_if_false_no_else_boolean(self):
        test(self,
             template='{{if:condition=$foo.hello}}YES{{end}}',
             expected='',
             data={'foo': {'hello': False}})

    def test_if_false_no_else_none(self):
        test(self,
             template='{{if:condition=$foo.hello}}YES{{end}}',
             expected='',
             data={'foo': {'hello': None}})

    def test_eval_no_vars(self):
        test(self,
             template='abc {{eval(2 + 2)}} xyz',
             expected='abc 4 xyz')

    def test_eval_vars(self):
        test(self,
             template='{{$head}} {{eval($nums.x + $nums.($data.var))}} {{$tail}}',
             expected='abc 53 xyz',
             data={'head': 'abc', 'tail': 'xyz',
                   'data': {'var': 'y'},
                   'nums': {'x': '42', 'y': 11}})


if __name__ == '__main__':
    unittest.main()
