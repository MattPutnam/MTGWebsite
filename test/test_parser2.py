import unittest

from parser import TemplateData, compile_template


def test(self, template, expected, data={}, path=[]):
    template_data = TemplateData(data, '', path)
    compiled = compile_template(template)
    rendered = compiled.evaluate(template_data)
    self.assertEqual(expected, rendered)


def read_file(filename):
    with open(filename) as stream:
        return stream.read()


class ParserTest(unittest.TestCase):
    def test_no_tokens(self):
        test(self, template='this is some text', expected='this is some text')

    def test_variables(self):
        test(self,
             template="{{$local->greeting}}, {{$main->name->first}}!",
             expected='Hello, John!',
             data={'local': {'greeting': 'Hello'},
                   'main': {'name': {'first': 'John', 'last': 'Smith'}}})

    def test_nested_variables(self):
        test(self,
             template='{{$data->($data->keyA->keyB)->keyC}}',
             expected='bar',
             data={'data': {'keyA': {'keyB': 'foo'},
                            'foo': {'keyC': 'bar'}}})

    def test_foreach(self):
        test(self,
             template='{{$main->header}}\n'
                      '{{foreach:var=foo, source=$main->data}}[test {{$foo}}]\n'
                      '{{end}}\n'
                      '{{$main->footer}}',
             expected='start\n'
                      '[test a]\n'
                      '[test b]\n'
                      '[test c]\n'
                      '\n'
                      'end',
             data={'main': {'header': 'start', 'data': ['a', 'b', 'c'], 'footer': 'end'}})

    def test_foreach_map(self):
        # just testing a single k/v pair since the order for multiple is undefined
        test(self,
             template='{{foreach:var=x, source=$data}}'
                      '{{$x}} {{$data->($x)}}{{end}}',
             expected='foo bar',
             data={'data': {'foo': 'bar'}})

    def test_foreach_cartesian(self):
        test(self,
             template='{{foreach:var=row, source=$data->rows}}'
                      '{{foreach:var=col, source=$data->cols}}'
                      '[{{$row}} {{$col}}]'
                      '{{end}}{{end}}',
             expected='[1 A][1 B][1 C][2 A][2 B][2 C][3 A][3 B][3 C]',
             data={'data': {'rows': [1, 2, 3], 'cols': ['A', 'B', 'C']}})

    def test_static_resource(self):
        test(self, path=['foo', 'bar'],
             template='<img src={{static_resource:file=test/file.txt}} />',
             expected='<img src=../../test/file.txt />')

    def test_static_resource_var(self):
        test(self, path=['foo'],
             template='<img src={{static_resource:file=$test->file}} />',
             expected='<img src=../graphic.png />',
             data={'test': {'file': 'graphic.png'}})

    def test_if_no_var(self):
        test(self,
             template='{{if:condition=$foo->dne}}{{$main->true}}\n'
                      '{{else}}{{$main->false}}\n'
                      '{{end}}',
             expected='expected\n',
             data={'main': {'true': 'Condition passed', 'false': 'expected'}})

    def test_if_true_bool(self):
        test(self,
             template='{{if:condition=$foo->hello}}YES{{end}}',
             expected='YES',
             data={'foo': {'hello': True}})

    def test_if_true_val(self):
        test(self,
             template='{{if:condition=$foo->hello}}YES{{end}}',
             expected='YES',
             data={'foo': {'hello': 'strings are truthy'}})

    def test_if_false_no_else_boolean(self):
        test(self,
             template='{{if:condition=$foo->hello}}YES{{end}}',
             expected='',
             data={'foo': {'hello': False}})

    def test_if_false_no_else_none(self):
        test(self,
             template='{{if:condition=$foo->hello}}YES{{end}}',
             expected='',
             data={'foo': {'hello': None}})

    def test_if_with_as(self):
        test(self,
             template='{{if:condition=$foo->bar->baz, as=temp}}{{$temp}}{{end}}',
             expected='hello',
             data={'foo': {'bar': {'baz': 'hello'}}})

    def test_eval_no_vars(self):
        test(self,
             template='abc {{eval(2 + 2)}} xyz',
             expected='abc 4 xyz')

    def test_eval_vars(self):
        test(self,
             template='{{$head}} {{eval($nums->x + $nums->($data->var))}} {{$tail}}',
             expected='abc 53 xyz',
             data={'head': 'abc', 'tail': 'xyz',
                   'data': {'var': 'y'},
                   'nums': {'x': '42', 'y': 11}})

    def test_template(self):
        test(self,
             template='abc {{template:file=test.htmpl, a=b, c=$baz}} xyz',
             expected='abc template text bar b qux xyz',
             data={'foo': 'bar', 'baz': 'qux'})

    def test_table_template_1(self):
        test(self,
             template='{{template:file=table1/table.htmpl, header=$header, content=$content}}',
             expected=read_file('table1/table_expected.txt'),
             data={'header': 'Test Table',
                   'content': [{'role': 'Producer', 'name': 'Alice'},
                               {'role': 'Director', 'name': 'Bob'}]})

    def test_table_template_2(self):
        test(self,
             template='{{template:file=table2/table.htmpl, header=Test Table 2, content=$content}}',
             expected=read_file('table2/table_expected.txt'),
             data={'content': {'Producer': 'Carol',
                               'Director': 'Dave'}})

    def test_with_local_resource_none(self):
        test(self,
             template='{{with_local_resource:glob=does/not/exist.png, as=nomatter}}'
                      'Hello file: <img src={{$nomatter}} />{{end}}',
             expected = '')

    def test_with_local_resource_exists(self):
        test(self,
             template='{{with_local_resource:glob=test.htmpl, as=file}}'
                      'Hello file: <img src={{$file}} />{{end}}',
             expected='Hello file: <img src=test.htmpl />')

    def test_with_local_resource_multi(self):
        test(self,
             template='{{with_local_resource:glob=*.htmpl, as=file, all_files=True}}'
                      'Test {{$file}} {{end}}',
             expected='Test test.htmpl Test test2.htmpl ')

    def test_comment(self):
        test(self,
             template="before {{comment: hey there I shouldn't render}} after",
             expected='before  after')

    def test_block_comment(self):
        test(self,
             template='before {{blockcomment}} {{$dne}} {{if:condition=$foo}} text {{end}}{{end}} after',
             expected='before  after')


if __name__ == '__main__':
    unittest.main()
