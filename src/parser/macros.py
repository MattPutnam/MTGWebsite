import re
from copy import deepcopy
from glob import glob
from os import path

import mistune

from parser.template_data import TemplateData

END = '~~~END~~~'
ELSE = '~~~ELSE~~~'

macro_pattern = '(\{\{.+?}})'
eval_pattern = '^eval\((.*)\)$'


class CompiledTemplate:
    def __init__(self, segments):
        self.segments = segments

    def evaluate(self, data: TemplateData) -> str:
        return ''.join(map(lambda x: x.render(data), self.segments))


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
    def __init__(self, data: dict, evaluate):
        super().__init__()
        self.file = data.pop('file')
        self.data = data
        self.evaluate = evaluate

    def render(self, template_data: TemplateData) -> str:
        resolved_data = {}
        for key in self.data:
            resolved_data[key] = template_data.resolve_variable(self.data[key])

        local_data = deepcopy(template_data)
        local_data.data.update(resolved_data)
        with open(self.file) as stream:
            contents = stream.read()
            return self.evaluate(contents, local_data)

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
