import re

from parser import macros
from parser.template_data import TemplateData


def _trim_all(strings):
    return list(map(lambda s: s.strip(), strings))


def _resolve_component(name: str, data: dict):
    if name == 'foreach':
        assert set(data) == {'source', 'var'}
        return macros.Foreach(data['source'], data['var'])
    elif name == 'static_resource':
        assert set(data) == {'file'}
        return macros.StaticResource(data['file'])
    elif name == 'if':
        assert set(data) >= {'condition'}
        return macros.If(data['condition'], binding=data.get('as'))
    elif name == 'template':
        assert set(data) >= {'file'}
        return macros.Template(data, evaluate_template)
    elif name == 'with_local_resource':
        assert set(data) >= {'glob'}
        return macros.WithLocalResource(data['glob'], reference=data.get('as'), all_files=data.get('all_files'))
    else:
        raise ValueError(f'Unknown component: {name}')


def _pack_macros(segments: list):
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


def compile_template(template: str) -> macros.CompiledTemplate:
    segments = []
    tokens = re.split(macros.macro_pattern, template)
    while len(tokens) > 0:
        token, *tokens = tokens
        if token == '':
            pass
        elif re.match(macros.macro_pattern, token):
            innards = token[2:-2]
            if innards.startswith('comment'):
                continue

            colon_split = _trim_all(innards.split(":", 1))
            if len(colon_split) == 1:
                value = colon_split[0]
                if value == 'end':
                    segments.append(macros.END)
                elif value == 'else':
                    segments.append(macros.ELSE)
                elif re.match(macros.eval_pattern, value):
                    segments.append(macros.Eval(value))
                elif value[0] == '$':
                    segments.append(macros.Variable(value))
                elif value.startswith("blockcomment"):
                    segments.append(macros.BlockComment())
                elif value == 'markdown':
                    segments.append(macros.Markdown())
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
            segments.append(macros.String(token))
    return macros.CompiledTemplate(_pack_macros(segments))


def evaluate_template(template: str, template_data: TemplateData) -> str:
    return compile_template(template).evaluate(template_data)
