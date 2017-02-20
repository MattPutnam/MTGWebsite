from os import path, listdir
from yattag import Doc, indent
import yaml
import re
import table
from fnmatch import fnmatch


main_data = {}

current_show = ""
root = path.dirname(path.dirname(path.abspath(__file__)))
cur_path = ""


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


token_pattern = "\{\{.+?\}\}"


def render_page(template, context, show_data={}, local_data={}):
    page = template
    for token in re.findall(token_pattern, template):
        page = page.replace(token, resolve_token(token, context, show_data, local_data))
    return page


def resolve_token(token, context, show_data, local_data):
    colon_split = trim_all(token[2:-2].split(":"))
    if len(colon_split) == 1:
        return resolve_variable(colon_split[0], show_data, local_data)
    elif len(colon_split) == 2:
        component, variables = colon_split
        data = {}
        for var_entry in trim_all(variables.split(",")):
            var, value = trim_all(var_entry.split("=", 1))
            data[var] = resolve_variable(value, show_data, local_data)
        return resolve_component(component, data, context)


def resolve_variable(variable, show_data, local_data):
    if variable[0] != '$':
        return variable

    namespace, name = variable[1:].split("/")
    if namespace == 'main':
        return main_data.get(name, '')
    elif namespace == 'show':
        return show_data.get(name, '')
    elif namespace == 'local':
        return local_data.get(name, '')
    else:
        raise ValueError("Exception: Unknown variable namespace '{}'", namespace)


def resolve_component(component, data, context):
    if component == 'table':
        return table.make_table(header=data['header'], content=data['content'])
    elif component == 'performances':
        return make_performance_section(dates=data['dates'], venue=data['venue'])
    elif component == 'banner':
        return resolve_banner(data['filename'])
    elif component == 'img':
        return resolve_img(data['filename'])
    elif component == 'resource':
        return resolve_resource(data['file'], context)
    elif component == 'foreach':
        return resolve_foreach(data['source'], data['content'])
    else:
        raise ValueError('Error: Unknown component "{}"', component)


def resolve_banner(filename):
    file = find_show_file(filename)
    if file:
        doc, tag, text = Doc().tagtext()
        with tag('div', klass='show_banner', align='middle'):
            doc.stag('img', src=file)
        return doc.getvalue()
    else:
        return ""


def resolve_img(filename):
    file = find_show_file(filename)
    if file:
        doc, tag, text = Doc().tagtext()
        doc.stag('img', src=file)
        return doc.getvalue()
    else:
        return ""


def resolve_resource(file, context):
    prefix = '../../' if context == 'show' else ''
    return prefix + file


def resolve_foreach(source, content):
    return "".join(map(lambda item: content.replace('$loopvar', item), source))


def make_performance_section(dates, venue):
    doc, tag, text = Doc().tagtext()

    text('Performances ')
    with tag('span', klass='performance_dates'):
        text(dates)
    text(' in ')
    doc.asis(make_venue_link(venue))

    return doc.getvalue()


page_template = load_or_die('templates', 'page.htmpl')


def write(title, content, context, *paths):
    filename = path.join(root, *paths)
    dir_name = path.dirname(filename)
    css_files = [f for f in listdir(dir_name) if fnmatch(f, '*.css')]
    if context == 'show':
        css_files.append('../../main.css')

    local_data = {'title': title, 'content': content, 'css_files': css_files}

    page = render_page(page_template, context=context, local_data=local_data)

    file = open(filename, "w")
    file.write(indent(page))
    file.close()


def make_venue_link(venue):
    venue = venue.lower()
    if venue == 'klt':
        venue_text = 'Kresge Little Theater'
        venue_href = 'http://whereis.mit.edu/?go=W16'
    elif venue == 'sala':
        venue_text = 'La Sala de Puerto Rico'
        venue_href = 'http://whereis.mit.edu/?go=W20'
    else:
        raise ValueError("Unknown venue: {}", venue)

    doc, tag, text, line = Doc().ttl()

    with tag('a', href=venue_href, klass='venue_link', target='_blank'):
        text(venue_text)

    return doc.getvalue()


def find_show_file(name):
    if cur_path:
        files = [file for file in listdir(cur_path) if fnmatch(file.lower(), name + '.*')]
        if len(files) > 0:
            return files[0]


def trim_all(strings):
    return list(map(lambda s: s.strip(), strings))
