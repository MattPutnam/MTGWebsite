import re


macro_pattern = '(\{\{.+?}})'
eval_pattern = '^eval\((.*)\)'


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
        for token in variable.split('.'):
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
                        result.append(Eval(self, value))
                    elif value[0] == '$':
                        result.append(Variable(self, value))
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

    def resolve_component(self, name: str, data: dict):
        if name == 'foreach':
            assert {'source', 'var'} == set(data)
            return Foreach(self, data['source'], data['var'])
        elif name == 'resource':
            assert {'file'} == set(data)
            return Resource(self, data['file'])
        elif name == 'if':
            assert {'condition'} == set(data)
            return If(self, data['condition'])
        else:
            raise ValueError(f'Unknown component: {name}')

    @staticmethod
    def resolve_macros(segments: list):
        component_stack = []
        block_stack = [[]]
        while len(segments) > 0:
            segment, *segments = segments
            if segment is END:
                top_component = component_stack[-1]
                top_component.body = block_stack[-1]

                component_stack = component_stack[:-1]
                block_stack = block_stack[:-1]
                block_stack[-1].append(top_component)
            elif issubclass(type(segment), Macro) and segment.is_block():
                component_stack.append(segment)
                block_stack.append([])
            else:
                block_stack[-1].append(segment)

        assert len(block_stack) == 1
        return block_stack[0]

    @staticmethod
    def render_list(segments: list):
        result = []
        for item in segments:
            if type(item) is str:
                result.append(item)
            elif issubclass(type(item), Macro):
                result.append(item.render())
            else:
                raise ValueError(f'Unknown type: {item}')
        return "".join(result)

    def evaluate(self, string: str) -> str:
        parsed = self.parse(string)
        resolved = self.resolve_macros(parsed)
        return self.render_list(resolved)


class Macro:
    def __init__(self, parser: Parser, name: str):
        self.parser = parser
        self.name = name

    def is_block(self):
        return False

    def render(self) -> str:
        raise NotImplementedError(f'Not implemented in {self.name}')


class Variable(Macro):
    def __init__(self, parser: Parser, variable: str):
        super().__init__(parser, 'Variable')
        self.variable = variable

    def render(self) -> str:
        result = self.parser.resolve_variable(self.variable)
        if type(result) is str:
            return str(result)
        else:
            raise ValueError("Variable didn't resolve to string")

    def __repr__(self):
        return 'Variable[' + self.variable + "]"


class Foreach(Macro):
    def __init__(self, parser: Parser, source: str, variable_name: str):
        super().__init__(parser, 'Foreach')
        self.source = source
        self.variable_name = variable_name
        self.body = []

    def is_block(self):
        return True

    def render(self) -> str:
        rendered_body = self.parser.render_list(self.body)
        resolved_source = self.parser.resolve_variable(self.source)
        emitted = map(lambda item: rendered_body.replace(self.variable_name, str(item)), resolved_source)
        return "".join(emitted)

    def __repr__(self):
        return 'Foreach[' + self.variable_name + ' in ' + str(self.source) + '] {' + str(self.body) + '}'


class Resource(Macro):
    def __init__(self, parser: Parser, file: str):
        super().__init__(parser, 'Resource')
        self.file = file

    def render(self) -> str:
        return ('../' * self.parser.depth) + str(self.parser.resolve_variable(self.file))

    def __repr__(self):
        return 'Resource[' + self.file + ']'


class If(Macro):
    def __init__(self, parser: Parser, condition: str):
        super().__init__(parser, 'If')
        self.condition = condition
        self.body = []

    def is_block(self):
        return True

    def render(self) -> str:
        if ELSE in self.body:
            else_index = self.body.index(ELSE)
            body_true = self.body[:else_index]
            body_false = self.body[else_index+1:]
        else:
            body_true = self.body
            body_false = []

        if self.condition[0] != '$' or self.parser.resolve_variable(self.condition, throw=False):
            body = body_true
        else:
            body = body_false

        return "".join(self.parser.render_list(body))

    def __repr__(self):
        return 'If[' + self.condition + '] {' + str(self.body) + '}'


class Eval(Macro):
    def __init__(self, parser: Parser, full_expr: str):
        super().__init__(parser, "Eval")
        match = re.match(eval_pattern, full_expr)
        self.expression = match.groups()[0]

    def render(self) -> str:
        expr = self.expression
        for variable in re.findall('\$\S+', expr):
            expr = expr.replace(variable, str(self.parser.resolve_variable(variable)))
        return str(eval(expr))


END = '~~~END~~~'
ELSE = '~~~ELSE~~~'
