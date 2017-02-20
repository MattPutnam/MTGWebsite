from os import path, listdir
from yattag import Doc, indent
import yaml
import re
import table
from fnmatch import fnmatch


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


token_pattern = "\{\{.+\}\}"


def render_page(template, main_data, show_data):
    page = template
    for token in re.findall(token_pattern, template):
        page = page.replace(token, resolve_token(token, main_data, show_data))
    return page


def resolve_token(token, main_data, show_data):
    colon_split = trim_all(token[2:-2].split(":"))
    if len(colon_split) == 1:
        return resolve_variable(colon_split[0], main_data, show_data)
    elif len(colon_split) == 2:
        component, variables = colon_split
        data = {}
        for var_entry in trim_all(variables.split(",")):
            var, value = trim_all(var_entry.split("="))
            data[var] = resolve_variable(value, main_data, show_data)
        return resolve_component(component, data)


def resolve_variable(variable, main_data, show_data):
    if variable[0] != '$':
        return variable

    namespace, name = variable[1:].split("/")
    if namespace == 'main':
        return main_data.get(name, '')
    elif namespace == 'show':
        return show_data.get(name, '')
    else:
        raise ValueError("Exception: Unknown variable namespace '{}'", namespace)


def resolve_component(component, data):
    if component == 'table':
        return table.make_table(header=data['header'], content=data['content'])
    elif component == 'performances':
        return make_performance_section(dates=data['dates'], venue=data['venue'])
    elif component == 'banner':
        return resolve_banner(data['filename'])
    elif component == 'img':
        return resolve_img(data['filename'])
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


def make_performance_section(dates, venue):
    doc, tag, text = Doc().tagtext()

    text('Performances ')
    with tag('span', klass='performance_dates'):
        text(dates)
    text(' in ')
    doc.asis(make_venue_link(venue))

    return doc.getvalue()


def write(title, content, *paths):
    filename = path.join(root, *paths)
    dir_name = path.dirname(filename)
    css_files = [f for f in listdir(dir_name) if fnmatch(f, '*.css')]
    is_show = paths[-1] == 'show.html'
    if is_show:
        css_files.append('../../main.css')

    doc, tag, text, line = Doc().ttl()
    doc.asis('<!-- This file has been automatically generated -->')
    doc.asis('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN">')
    with tag('html'):
        doc.asis(make_head(title, css_files))
        with tag('body'):
            doc.asis(make_header(is_show))
            with tag('div', klass='page'):
                doc.asis(content)

    file = open(filename, "w")
    file.write(indent(doc.getvalue()))
    file.close()


def make_head(title, css_files):
    doc, tag, text, line = Doc().ttl()
    with tag('head'):
        doc.stag('meta', ('http-equiv', 'Content-Type'), content='text/html; charset=UTF-8')
        doc.stag('meta', name='description', content='The non-profit, student-run MIT Musical Theatre Guild is the oldest and largest theatre organization at MIT.')
        for css_file in css_files:
            doc.stag('link', type='text/css', href=css_file, rel='stylesheet')
        doc.stag('link', type='image/png', href='images/mtg-16.png', rel='icon')
        with tag('title'):
            text(title)

    return doc.getvalue()


def make_header(is_show):
    prefix = '../../' if is_show else ''

    doc, tag, text, line = Doc().ttl()
    with tag('div', id='header'):
        doc.stag('img', alt='MTG', klass='mtglogo', src=prefix+'images/mtg-bg.gif')
        with tag('span', klass='links'):
            with tag('a', href=prefix + '/'.join(current_show) + '/show.html'):
                text('Current Show')
            with tag('a', href=prefix+'show_list.html'):
                text('Show List')
            with tag('a', href=prefix+'about.html'):
                text('About MTG')
            with tag('a', href=prefix+'contact.html'):
                text('Contact Us')
            with tag('a', href='http://web.mit.edu/'):
                doc.stag('img', alt='MIT', klass='mitlogo', src=prefix+'images/mit-redgrey-header.png')

    return doc.getvalue()


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
