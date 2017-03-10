import re
from copy import deepcopy
from glob import glob
from os import path

import mistune

END = '~~~END~~~'
ELSE = '~~~ELSE~~~'

macro_pattern = '(\{\{.+?}})'
eval_pattern = '^eval\((.*)\)$'


class TemplateData:
    def __init__(self, data: dict, root, path):
        self.data = data
        self.root = root
        self.path = path

    def bind(self, key, value):
        self.data[key] = value

    def resolve_variable(self, variable: str, throw: bool = False) -> object:
        # So you can use constants in place of variables:
        if not variable[0] == '$':
            return variable

        variable = variable[1:]

        tokens = re.split('[()]', variable)
        for index, token in enumerate(tokens):
            if token == '':
                continue
            if token[0] == '$':
                tokens[index] = self.resolve_variable(token, throw)
        variable = ''.join(tokens)

        thing = self.data
        for token in variable.split('->'):
            if token in thing:
                thing = thing[token]
            else:
                if throw:
                    raise ValueError(f'Unable to resolve variable: {variable}')
                else:
                    return ''
        return thing


class Macro:
    def __init__(self, block=False):
        self.block = block

    def is_block(self):
        return self.block

    def render(self, template_data: TemplateData) -> str:
        raise NotImplementedError('Render not implemented')


class String(Macro):
    def __init__(self, contents: str):
        super().__init__()
        self.contents = contents

    def render(self, template_data: TemplateData) -> str:
        return self.contents

    def __repr__(self):
        return 'String[' + self.contents + ']'


class Variable(Macro):
    def __init__(self, variable: str):
        super().__init__()
        self.variable = variable

    def render(self, template_data: TemplateData) -> str:
        result = template_data.resolve_variable(self.variable)
        return str(result)

    def __repr__(self):
        return 'Variable[' + self.variable + "]"


class Foreach(Macro):
    def __init__(self, source: str, variable_name: str):
        super().__init__(block=True)
        self.source = source
        self.variable_name = variable_name
        self.body = []

    def render(self, template_data: TemplateData) -> str:
        resolved_source = template_data.resolve_variable(self.source)

        bodies = []
        for value in resolved_source:
            local_data = deepcopy(template_data)
            local_data.data[self.variable_name] = value
            bodies.append(CompiledTemplate(self.body).evaluate(local_data))

        return ''.join(bodies)

    def __repr__(self):
        return 'Foreach[' + self.variable_name + ' in ' + str(self.source) + '] {' + str(self.body) + '}'


class StaticResource(Macro):
    def __init__(self, file: str):
        super().__init__()
        self.file = file

    def render(self, template_data: TemplateData) -> str:
        return ('../' * len(template_data.path)) + str(template_data.resolve_variable(self.file))

    def __repr__(self):
        return 'StaticResource[' + self.file + ']'


class If(Macro):
    def __init__(self, condition: str, binding=None):
        super().__init__(block=True)
        self.condition = condition
        self.binding = binding
        self.body = []

    def render(self, template_data: TemplateData) -> str:
        resolved = template_data.resolve_variable(self.condition)

        if self.binding:
            local_data = deepcopy(template_data)
            local_data.bind(self.binding, resolved)
        else:
            local_data = template_data

        if ELSE in self.body:
            else_index = self.body.index(ELSE)
            body_true = self.body[:else_index]
            body_false = self.body[else_index+1:]
        else:
            body_true = self.body
            body_false = []

        if self.condition[0] != '$' or resolved:
            body = body_true
        else:
            body = body_false

        return CompiledTemplate(body).evaluate(local_data)

    def __repr__(self):
        return 'If[' + self.condition + '] {' + str(self.body) + '}'


class Eval(Macro):
    def __init__(self, full_expr: str):
        super().__init__()
        match = re.match(eval_pattern, full_expr)
        self.expression = match.groups()[0]

    def render(self, template_data: TemplateData) -> str:
        expr = self.expression
        for variable in re.findall('\$[a-zA-Z()\->$]+', expr):
            expr = expr.replace(variable, str(template_data.resolve_variable(variable)))
        return str(eval(expr))

    def __repr__(self):
        return 'eval(' + self.expression + ')'


class Template(Macro):
    def __init__(self, data: dict):
        super().__init__()
        self.file = data.pop('file')
        self.data = data

    def render(self, template_data: TemplateData) -> str:
        resolved_data = {}
        for key in self.data:
            resolved_data[key] = template_data.resolve_variable(self.data[key])

        local_data = deepcopy(template_data)
        local_data.data.update(resolved_data)
        with open(self.file) as stream:
            contents = stream.read()
            return evaluate_template(contents, local_data)

    def __repr__(self):
        return 'Template[' + self.file + ']'


class WithLocalResource(Macro):
    def __init__(self, pattern, reference=None, all_files=False):
        super().__init__(block=True)
        self.pattern = pattern
        self.reference = reference
        self.all_files = all_files
        self.body = []

    def render(self, template_data: TemplateData) -> str:
        file_path = path.join(template_data.root, *template_data.path, self.pattern)
        files = glob(file_path)
        if files:
            local_compiled = CompiledTemplate(self.body)
            local_data = deepcopy(template_data)
            if self.reference:
                if self.all_files:
                    results = []
                    for file in files:
                        local_data.bind(self.reference, path.basename(file))
                        results.append(local_compiled.evaluate(local_data))
                    return ''.join(results)
                else:
                    local_data.bind(self.reference, path.basename(files[0]))
                    return local_compiled.evaluate(local_data)
            else:
                return local_compiled.evaluate(local_data)
        else:
            return ''

    def __repr__(self):
        return 'WithLocalResource[' + self.pattern + ']'


class BlockComment(Macro):
    def __init__(self):
        super().__init__(block=True)
        self.body = []

    def render(self, template_data: TemplateData) -> str:
        return ''

    def __repr__(self):
        return 'BlockComment'


class Markdown(Macro):
    def __init__(self):
        super().__init__(block=True)
        self.body = []

    def render(self, template_data: TemplateData) -> str:
        # leading spaces cause mistune to think it's preformatted code:
        rendered = CompiledTemplate(self.body).evaluate(template_data)
        rendered = '\n'.join(map(lambda s: s.strip(), rendered.split('\n')))
        return mistune.markdown(rendered)

    def __repr__(self):
        return 'Markdown'


class CompiledTemplate:
    def __init__(self, segments):
        self.segments = segments

    def evaluate(self, data: TemplateData) -> str:
        return ''.join(map(lambda x: x.render(data), self.segments))


def _trim_all(strings):
    return list(map(lambda s: s.strip(), strings))


def _resolve_component(name: str, data: dict):
    if name == 'foreach':
        assert set(data) == {'source', 'var'}
        return Foreach(data['source'], data['var'])
    elif name == 'static_resource':
        assert set(data) == {'file'}
        return StaticResource(data['file'])
    elif name == 'if':
        assert set(data) >= {'condition'}
        return If(data['condition'], binding=data.get('as'))
    elif name == 'template':
        assert set(data) >= {'file'}
        return Template(data)
    elif name == 'with_local_resource':
        assert set(data) >= {'glob'}
        return WithLocalResource(data['glob'], reference=data.get('as'), all_files=data.get('all_files'))
    else:
        raise ValueError(f'Unknown component: {name}')


def _pack_macros(segments: list):
    component_stack = []
    block_stack = [[]]
    while len(segments) > 0:
        segment, *segments = segments
        if segment is END:
            top_component = component_stack.pop()
            top_component.body = block_stack.pop()
            block_stack[-1].append(top_component)
        elif issubclass(type(segment), Macro) and segment.is_block():
            component_stack.append(segment)
            block_stack.append([])
        else:
            block_stack[-1].append(segment)

    assert len(block_stack) == 1
    return block_stack[0]


def compile_template(template: str) -> CompiledTemplate:
    segments = []
    tokens = re.split(macro_pattern, template)
    while len(tokens) > 0:
        token, *tokens = tokens
        if token == '':
            pass
        elif re.match(macro_pattern, token):
            innards = token[2:-2]
            if innards.startswith('comment'):
                continue

            colon_split = _trim_all(innards.split(":", 1))
            if len(colon_split) == 1:
                value = colon_split[0]
                if value == 'end':
                    segments.append(END)
                elif value == 'else':
                    segments.append(ELSE)
                elif re.match(eval_pattern, value):
                    segments.append(Eval(value))
                elif value[0] == '$':
                    segments.append(Variable(value))
                elif value.startswith("blockcomment"):
                    segments.append(BlockComment())
                elif value == 'markdown':
                    segments.append(Markdown())
                else:
                    raise ValueError(f'Unable to parse macro {token}')
            else:
                name, props = _trim_all(colon_split)
                data = {}

                for var_entry in _trim_all(props.split(',')):
                    var, value = _trim_all(var_entry.split('=', 1))
                    data[var] = value

                segments.append(_resolve_component(name, data))
        else:
            segments.append(String(token))
    return CompiledTemplate(_pack_macros(segments))


def evaluate_template(template: str, template_data: TemplateData) -> str:
    return compile_template(template).evaluate(template_data)
