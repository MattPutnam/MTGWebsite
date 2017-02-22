import unittest
from src.parser import Parser


def make_data(main_data=None, show_data=None, local_data=None):
    return {'main': main_data if main_data else {},
            'show': show_data if show_data else {},
            'local': local_data if local_data else {}}


class ParserTest(unittest.TestCase):
    def test_make_data(self):
        main_data = {'foo': 'bar'}
        local_data = {'a': 'b'}
        data = make_data(main_data = main_data, local_data = local_data)
        expected = {'main': main_data, 'show': {}, 'local': local_data}
        self.assertEqual(expected, data)

    def test_no_tokens(self):
        text = "this is some text"
        parser = Parser(make_data())
        rendered = parser.evaluate(text)
        self.assertEqual(text, rendered)

    def test_variables(self):
        text = "{{$local.greeting}}, {{$main.name.first}}!"
        local_data = {'greeting': "Hello"}
        main_data = {'name': {'first': 'John', 'last': 'Smith'}}
        parser = Parser(make_data(local_data=local_data, main_data=main_data))
        rendered = parser.evaluate(text)
        expected = 'Hello, John!'
        self.assertEqual(expected, rendered)

    def test_nested_variables(self):
        text = "{{$data.($data.keyA.keyB).keyC}}"
        parser = Parser({'data': {'keyA': {'keyB': 'foo'},
                                  'foo': {'keyC': 'bar'}}})
        rendered = parser.evaluate(text)
        expected = 'bar'
        self.assertEqual(expected, rendered)

    def test_foreach(self):
        text = '{{$main.header}}\n' \
               '{{foreach:var=$foo, source=$main.data}}[test $foo]\n' \
               '{{end}}\n' \
               '{{$main.footer}}'
        main_data = {'header': 'start', 'data': ['a', 'b', 'c'], 'footer': 'end'}
        parser = Parser(make_data(main_data=main_data))
        rendered = parser.evaluate(text)
        expected = 'start\n' \
                   '[test a]\n' \
                   '[test b]\n' \
                   '[test c]\n' \
                   '\n' \
                   'end'
        self.assertEqual(expected, rendered)

    def test_foreach_cartesian(self):
        text = '{{foreach:var=$row, source=$data.rows}}' \
               '{{foreach:var=$col, source=$data.cols}}' \
               '[$row $col]' \
               '{{end}}{{end}}'
        parser = Parser({'data': {'rows': [1, 2, 3], 'cols': ['A', 'B', 'C']}})
        rendered = parser.evaluate(text)
        expected = '[1 A][1 B][1 C][2 A][2 B][2 C][3 A][3 B][3 C]'
        self.assertEqual(expected, rendered)

    def test_resource(self):
        text = "<img src={{resource:file=test/file.txt}} />"
        parser = Parser({}, depth=2)
        rendered = parser.evaluate(text)
        expected = '<img src=../../test/file.txt />'
        self.assertEqual(expected, rendered)

    def test_if_no_var(self):
        text = "{{if:condition=$foo.dne}}{{$main.true}}\n" \
               "{{else}}{{$main.false}}\n" \
               "{{end}}"
        parser = Parser({'main': {'true': 'Condition passed', 'false': 'expected'}})
        rendered = parser.evaluate(text)
        expected = 'expected\n'
        self.assertEqual(expected, rendered)

    def test_if_true(self):
        text = "{{if:condition=$foo.hello}}YES{{end}}"

        parser = Parser({'foo': {'hello': True}})
        rendered = parser.evaluate(text)
        expected = 'YES'
        self.assertEqual(expected, rendered)

        parser = Parser({'foo': {'hello': 'strings are truthy'}})
        rendered = parser.evaluate(text)
        expected = 'YES'
        self.assertEqual(expected, rendered)

    def test_if_false_no_else(self):
        text = "{{if:condition=$foo.hello}}YES{{end}}"

        parser = Parser({'foo': {'hello': False}})
        rendered = parser.evaluate(text)
        expected = ''
        self.assertEqual(expected, rendered)

        parser = Parser({'foo': {}}) # None is falsy
        rendered = parser.evaluate(text)
        expected = ''
        self.assertEqual(expected, rendered)

    def test_eval_no_vars(self):
        text = 'abc {{eval(2 + 2)}} xyz'
        parser = Parser({})
        rendered = parser.evaluate(text)
        expected = 'abc 4 xyz'
        self.assertEqual(expected, rendered)

    def test_eval_vars(self):
        text = '{{$head}} {{eval($nums.x + $nums.($data.var))}} {{$tail}}'
        parser = Parser({'head': 'abc', 'tail': 'xyz',
                         'data': {'var': 'y'},
                         'nums': {'x': '42', 'y': 11}})
        rendered = parser.evaluate(text)
        expected = 'abc 53 xyz'
        self.assertEqual(expected, rendered)


if __name__ == '__main__':
    unittest.main()
