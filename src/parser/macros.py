from copy import deepcopy
import re
from os import path
from glob import glob

import mistune


END = '~~~END~~~'
ELSE = '~~~ELSE~~~'

macro_pattern = '(\{\{.+?}})'
eval_pattern = '^eval\((.*)\)$'


class Macro:
    def __init__(self):
        pass

    def is_block(self):
        return False

    def render(self, parser) -> str:
        raise NotImplementedError('Render not implemented')


class Variable(Macro):
    def __init__(self, variable: str):
        super().__init__()
        self.variable = variable

    def render(self, parser) -> str:
        result = parser.resolve_variable(self.variable)
        return str(result)

    def __repr__(self):
        return 'Variable[' + self.variable + "]"


class Foreach(Macro):
    def __init__(self, source: str, variable_name: str):
        super().__init__()
        self.source = source
        self.variable_name = variable_name
        self.body = []

    def is_block(self):
        return True

    def render(self, parser) -> str:
        resolved_source = parser.resolve_variable(self.source)

        bodies = []
        for value in resolved_source:
            local_parser = deepcopy(parser)
            local_parser.data[self.variable_name] = value
            bodies.append(local_parser.render_list(self.body))

        return "".join(bodies)

    def __repr__(self):
        return 'Foreach[' + self.variable_name + ' in ' + str(self.source) + '] {' + str(self.body) + '}'


class StaticResource(Macro):
    def __init__(self, file: str):
        super().__init__()
        self.file = file

    def render(self, parser) -> str:
        return ('../' * len(parser.path)) + str(parser.resolve_variable(self.file))

    def __repr__(self):
        return 'StaticResource[' + self.file + ']'


class If(Macro):
    def __init__(self, condition: str, binding=None):
        super().__init__()
        self.condition = condition
        self.binding = binding
        self.body = []

    def is_block(self):
        return True

    def render(self, parser) -> str:
        resolved = parser.resolve_variable(self.condition)

        if self.binding:
            local_parser = deepcopy(parser)
            local_parser.data[self.binding] = resolved
        else:
            local_parser = parser

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

        return ''.join(local_parser.render_list(body))

    def __repr__(self):
        return 'If[' + self.condition + '] {' + str(self.body) + '}'


class Eval(Macro):
    def __init__(self, full_expr: str):
        super().__init__()
        match = re.match(eval_pattern, full_expr)
        self.expression = match.groups()[0]

    def render(self, parser) -> str:
        expr = self.expression
        for variable in re.findall('\$[a-zA-Z()\->$]+', expr):
            expr = expr.replace(variable, str(parser.resolve_variable(variable)))
        return str(eval(expr))

    def __repr__(self):
        return 'eval(' + self.expression + ')'


class Template(Macro):
    def __init__(self, data: dict):
        super().__init__()
        self.file = data.pop('file')
        self.data = data

    def render(self, parser) -> str:
        resolved_data = {}
        for key in self.data:
            resolved_data[key] = parser.resolve_variable(self.data[key])

        parser.data.update(resolved_data)
        with open(self.file) as stream:
            contents = stream.read()
            return parser.evaluate(contents)

    def __repr__(self):
        return 'Template[' + self.file + ']'


class WithLocalResource(Macro):
    def __init__(self, pattern, reference=None, all_files=False):
        super().__init__()
        self.pattern = pattern
        self.reference = reference
        self.all_files = all_files
        self.body = []

    def is_block(self):
        return True

    def render(self, parser) -> str:
        file_path = path.join(parser.root, *parser.path, self.pattern)
        files = glob(file_path)
        if files:
            if self.reference:
                local_parser = deepcopy(parser)
                if self.all_files:
                    results = []
                    for file in files:
                        local_parser.data[self.reference] = path.basename(file)
                        results.append(local_parser.render_list(self.body))
                    return ''.join(results)
                else:
                    local_parser.data[self.reference] = path.basename(files[0])
                    return local_parser.render_list(self.body)
            else:
                return parser.render_list(self.body)
        else:
            return ''

    def __repr__(self):
        return 'WithLocalResource[' + self.pattern + ']'


class BlockComment(Macro):
    def __init__(self):
        super().__init__()
        self.body = []

    def is_block(self):
        return True

    def render(self, parser) -> str:
        return ''

    def __repr__(self):
        return 'BlockComment'


class Markdown(Macro):
    def __init__(self):
        super().__init__()
        self.body = []

    def is_block(self):
        return True

    def render(self, parser) -> str:
        return mistune.markdown(parser.render_list(self.body))

    def __repr__(self):
        return 'Markdown'
