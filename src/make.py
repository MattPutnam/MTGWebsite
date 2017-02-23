import shows
from utils import load_or_die, write

import yaml
import collections

from parser import Parser

# Setup yaml importer to use OrderedDict
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())


def dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))

yaml.add_representer(collections.OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)


def main():
    main_data = load_or_die('site', 'main.yaml')
    main_data['current_show_page'] = main_data['Current Show'] + '/show.html'

    parser = Parser({'main': main_data})

    render_index(parser)
    render_about(parser)
    shows.render_shows(parser, main_data['Current Show'].split('/'))

    print("Success!")


def render_about(parser):
    about_template = load_or_die('templates', 'about.htmpl')
    rendered = parser.evaluate(about_template)
    write(parser, 'MTG - About MTG', rendered, 'site', 'about.html')


def render_index(parser):
    index_template = load_or_die('templates', 'index.htmpl')
    rendered = parser.evaluate(index_template)
    with open('../site/index.html', 'w') as stream:
        stream.write(rendered)


if __name__ == '__main__':
    main()
