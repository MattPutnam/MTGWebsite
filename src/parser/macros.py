from copy import deepcopy
import re
from os import listdir, path


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


class Resource(Macro):
    def __init__(self, file: str):
        super().__init__()
        self.file = file

    def render(self, parser) -> str:
        return ('../' * len(parser.path)) + str(parser.resolve_variable(self.file))

    def __repr__(self):
        return 'Resource[' + self.file + ']'


class If(Macro):
    def __init__(self, condition: str):
        super().__init__()
        self.condition = condition
        self.body = []

    def is_block(self):
        return True

    def render(self, parser) -> str:
        if ELSE in self.body:
            else_index = self.body.index(ELSE)
            body_true = self.body[:else_index]
            body_false = self.body[else_index+1:]
        else:
            body_true = self.body
            body_false = []

        if self.condition[0] != '$' or parser.resolve_variable(self.condition, throw=False):
            body = body_true
        else:
            body = body_false

        return ''.join(parser.render_list(body))

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


class WithResource(Macro):
    def __init__(self, file, reference=None):
        super().__init__()
        self.file = file
        self.reference = reference
        self.body = []

    def is_block(self):
        return True

    def render(self, parser) -> str:
        file_path = path.join(parser.root, *parser.path, self.file)
        if path.exists(file_path):
            if self.reference:
                local_parser = deepcopy(parser)
                local_parser.data[self.reference] = file_path
            else:
                local_parser = parser
            return ''.join(local_parser.render_list(self.body))
        else:
            return ''
