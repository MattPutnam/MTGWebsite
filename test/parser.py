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

    def test_if_false_no_else(self):
        text = "{{if:condition=$foo.hello}}YES{{end}}"
        parser = Parser({'foo': {'hello': False}})
        rendered = parser.evaluate(text)
        expected = ''
        self.assertEqual(expected, rendered)


if __name__ == '__main__':
    unittest.main()
