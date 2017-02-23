from fnmatch import fnmatch
from os import path, listdir

import yaml


root = path.dirname(path.dirname(path.abspath(__file__)))


def load_or_die(*paths):
    filename = path.join(root, *paths)
    ext = path.splitext(filename)[1][1:]
    if ext == 'yaml':
        with open(filename) as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as e:
                print(e)
                exit(-1)
    else:
        file = open(filename)
        return file.read()


page_template = load_or_die('templates', 'page.htmpl')


def write(parser, title, content, *paths):
    filename = path.join(root, *paths)
    dir_name = path.dirname(filename)
    css_files = [f for f in listdir(dir_name) if fnmatch(f, '*.css')]
    if len(parser.path) > 0:
        css_files.insert(0, ('../' * len(parser.path)) + 'main.css')

    local_data = {'title': title, 'content': content, 'css_files': css_files}
    parser.data['local'] = local_data

    page = parser.evaluate(page_template)

    with open(filename, 'w') as stream:
        stream.write(page)


def find_show_file(file_path, name):
    files = [file for file in listdir(file_path) if fnmatch(file.lower(), name + '.*')]
    if len(files) > 0:
        return files[0]


def trim_all(strings):
    return list(map(lambda s: s.strip(), strings))
