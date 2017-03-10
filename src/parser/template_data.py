import re


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
