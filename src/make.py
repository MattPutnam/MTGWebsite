import collections
import sys
import time

import yaml

import shows
from parser.parser import Parser
from utils import load_or_die, write, root

# Setup yaml importer to use OrderedDict
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())


def dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))

yaml.add_representer(collections.OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)


def main():
    if len(sys.argv) != 2:
        print_usage()
        exit()

    command = sys.argv[1]

    main_data = load_or_die('site', 'main.yaml')
    main_data['current_show_page'] = main_data['Current Show'] + '/show.html'

    venue_data = load_or_die('site', 'venues.yaml')

    parser = Parser({'main': main_data, 'venues': venue_data}, root + '/site', [])

    start_time = time.time()

    if command == 'all':
        make_all(parser, main_data)
    elif command == 'shows':
        make_shows(parser, main_data)
    elif command == 'about':
        render_about(parser)
    else:
        print_usage()
        exit()

    print('Success!')
    print('Completed in %s seconds' % (time.time() - start_time))


def make_all(parser, main_data):
    make_shows(parser, main_data)
    render_about(parser)


def make_shows(parser, main_data):
    shows.render_shows(parser, main_data['Current Show'].split('/'))


def render_about(parser):
    about_template = load_or_die('templates', 'about.htmpl')
    rendered = parser.evaluate(about_template)
    write(parser, 'MTG - About MTG', rendered, 'site', 'about.html')


def render_index(parser):
    index_template = load_or_die('templates', 'index.htmpl')
    rendered = parser.evaluate(index_template)
    with open('../site/index.html', 'w') as stream:
        stream.write(rendered)


def print_usage():
    print('usage: make.py all      # remake all files')
    print('       make.py shows    # remake only the show pages')
    print('       make.py about    # remake only the about page')


if __name__ == '__main__':
    main()
