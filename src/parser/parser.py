import re

from parser import macros


def trim_all(strings):
    return list(map(lambda s: s.strip(), strings))


class Parser:
    def __init__(self, data: dict, root, path):
        self.data = data
        self.root = root
        self.path = path

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
        variable = "".join(tokens)

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

    def parse(self, string: str) -> list:
        result = []
        tokens = re.split(macros.macro_pattern, string)
        while len(tokens) > 0:
            token, *tokens = tokens
            if token == '':
                pass
            elif re.match(macros.macro_pattern, token):
                colon_split = trim_all(token[2:-2].split(":", 1))
                if len(colon_split) == 1:
                    value = colon_split[0]
                    if value == 'end':
                        result.append(macros.END)
                    elif value == 'else':
                        result.append(macros.ELSE)
                    elif re.match(macros.eval_pattern, value):
                        result.append(macros.Eval(value))
                    elif value[0] == '$':
                        result.append(macros.Variable(value))
                    elif value.startswith("comment"):
                        pass
                    elif value.startswith("blockcomment"):
                        result.append(macros.BlockComment())
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
            return macros.Foreach(data['source'], data['var'])
        elif name == 'static_resource':
            assert set(data) == {'file'}
            return macros.StaticResource(data['file'])
        elif name == 'if':
            assert set(data) == {'condition'}
            return macros.If(data['condition'])
        elif name == 'template':
            assert set(data) >= {'file'}
            return macros.Template(data)
        elif name == 'with_local_resource':
            assert set(data) >= {'glob'}
            return macros.WithLocalResource(data['glob'], reference=data.get('as'), all_files=data.get('all_files'))
        else:
            raise ValueError(f'Unknown component: {name}')

    @staticmethod
    def pack_macros(segments: list):
        component_stack = []
        block_stack = [[]]
        while len(segments) > 0:
            segment, *segments = segments
            if segment is macros.END:
                top_component = component_stack.pop()
                top_component.body = block_stack.pop()
                block_stack[-1].append(top_component)
            elif issubclass(type(segment), macros.Macro) and segment.is_block():
                component_stack.append(segment)
                block_stack.append([])
            else:
                block_stack[-1].append(segment)

        assert len(block_stack) == 1
        return block_stack[0]

    def render_list(self, segments: list) -> str:
        result = []
        for item in segments:
            if type(item) is str:
                result.append(item)
            elif issubclass(type(item), macros.Macro):
                result.append(item.render(self))
            else:
                raise ValueError(f'Unknown type: {item}')
        return ''.join(result)

    def evaluate(self, string: str) -> str:
        parsed = self.parse(string)
        resolved = self.pack_macros(parsed)
        return self.render_list(resolved)
