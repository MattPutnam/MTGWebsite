import re
from copy import deepcopy


macro_pattern = '(\{\{.+?}})'
eval_pattern = '^eval\((.*)\)$'


def trim_all(strings):
    return list(map(lambda s: s.strip(), strings))


class Parser:
    def __init__(self, data: dict, depth: int = 0):
        self.data = data
        self.depth = depth

    def resolve_variable(self, variable: str, throw: bool = True) -> object:
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
        variable = "".join(tokens)

        thing = self.data
        for token in variable.split('/'):
            if token in thing:
                thing = thing[token]
            else:
                if throw:
                    raise ValueError(f'Unable to resolve variable: {variable}')
                else:
                    return {}
        return thing

    def parse(self, string: str) -> list:
        result = []
        tokens = re.split(macro_pattern, string, re.DOTALL | re.MULTILINE)
        while len(tokens) > 0:
            token, *tokens = tokens
            if token == '':
                pass
            elif re.match(macro_pattern, token):
                colon_split = trim_all(token[2:-2].split(":", 1))
                if len(colon_split) == 1:
                    value = colon_split[0]
                    if value == 'end':
                        result.append(END)
                    elif value == 'else':
                        result.append(ELSE)
                    elif re.match(eval_pattern, value):
                        result.append(Eval(value))
                    elif value[0] == '$':
                        result.append(Variable(value))
                    else:
                        raise ValueError(f'Unable to parse macro {token}')
                else:
                    name, props = trim_all(colon_split)
                    data = {}

                    for var_entry in trim_all(props.split(',')):
                        var, value = trim_all(var_entry.split('=', 1))
                        data[var] = value

                    result.append(self.resolve_component(name, data))
            else:
                result.append(token)
        return result

    @staticmethod
    def resolve_component(name: str, data: dict):
        if name == 'foreach':
            assert set(data) == {'source', 'var'}
            return Foreach(data['source'], data['var'])
        elif name == 'resource':
            assert set(data) == {'file'}
            return Resource(data['file'])
        elif name == 'if':
            assert set(data) == {'condition'}
            return If(data['condition'])
        elif name == 'template':
            assert set(data) >= {'file'}
            return Template(data)
        else:
            raise ValueError(f'Unknown component: {name}')

    @staticmethod
    def pack_macros(segments: list):
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

    def render_list(self, segments: list):
        result = []
        for item in segments:
            if type(item) is str:
                result.append(item)
            elif issubclass(type(item), Macro):
                result.append(item.render(self))
            else:
                raise ValueError(f'Unknown type: {item}')
        return "".join(result)

    def evaluate(self, string: str) -> str:
        parsed = self.parse(string)
        resolved = self.pack_macros(parsed)
        return self.render_list(resolved)


class Macro:
    def __init__(self):
        pass

    def is_block(self):
        return False

    def render(self, parser: Parser) -> str:
        raise NotImplementedError('Render not implemented')


class Variable(Macro):
    def __init__(self, variable: str):
        super().__init__()
        self.variable = variable

    def render(self, parser: Parser) -> str:
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

    def render(self, parser: Parser) -> str:
        resolved_source = parser.resolve_variable(self.source)
        assert type(resolved_source) is list

        bodies = []
        for value in list(resolved_source):
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

    def render(self, parser: Parser) -> str:
        return ('../' * parser.depth) + str(parser.resolve_variable(self.file))

    def __repr__(self):
        return 'Resource[' + self.file + ']'


class If(Macro):
    def __init__(self, condition: str):
        super().__init__()
        self.condition = condition
        self.body = []

    def is_block(self):
        return True

    def render(self, parser: Parser) -> str:
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

        return "".join(parser.render_list(body))

    def __repr__(self):
        return 'If[' + self.condition + '] {' + str(self.body) + '}'


class Eval(Macro):
    def __init__(self, full_expr: str):
        super().__init__()
        match = re.match(eval_pattern, full_expr)
        self.expression = match.groups()[0]

    def render(self, parser: Parser) -> str:
        expr = self.expression
        for variable in re.findall('\$[a-zA-Z()/$]+', expr):
            expr = expr.replace(variable, str(parser.resolve_variable(variable)))
        return str(eval(expr))


class Template(Macro):
    def __init__(self, data: dict):
        super().__init__()
        self.file = data.pop('file')
        self.data = data

    def render(self, parser: Parser) -> str:
        resolved_data = {}
        for key in self.data:
            resolved_data[key] = parser.resolve_variable(self.data[key])

        parser.data.update(resolved_data)
        with open(self.file) as stream:
            contents = stream.read()
            return parser.evaluate(contents)


END = '~~~END~~~'
ELSE = '~~~ELSE~~~'
