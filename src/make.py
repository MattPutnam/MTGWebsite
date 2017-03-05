import collections
import sys
import time
from copy import deepcopy

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
    start_time = time.time()

    if len(sys.argv) != 2:
        print_usage()
        exit()

    command = sys.argv[1]

    main_data = load_or_die('site', 'main.yaml')
    main_data['current_show_page'] = main_data['Current Show'] + '/show.html'
    shows.current_year, shows.current_season = main_data['Current Show'].split('/')

    venue_data = load_or_die('site', 'venues.yaml')
    ticket_data = load_or_die('site', 'tickets.yaml')

    data = {'main': main_data, 'venues': venue_data, 'tickets': ticket_data}

    parser = Parser(data, root + '/site', [])

    if command == 'all':
        make_all(parser, data)
    elif command == 'shows':
        make_shows(parser)
    elif command == 'about':
        render_about(parser)
    else:
        print_usage()
        exit()

    print('Success!')
    print('Completed in %s seconds' % (time.time() - start_time))


def make_all(parser, data):
    render_index(parser, data)
    make_shows(parser)
    render_about(parser)


def make_shows(parser):
    shows.render_all_show_pages(parser)


def render_about(parser):
    about_template = load_or_die('templates', 'about.htmpl')
    rendered = parser.evaluate(about_template)
    write(parser, 'MTG - About MTG', rendered, 'site', 'about.html')


def render_index(parser, data):
    index_template = load_or_die('templates', 'index.htmpl')
    year, season = data['main']['Current Show'].split('/')

    graphic = shows.get_show_graphic(year, season)

    current_show_data = load_or_die('site', year, season, 'show.yaml')
    current_show_data.update({'year': year, 'season': season, 'graphic': graphic})

    index_parser = deepcopy(parser)
    index_parser.data['show'] = current_show_data

    rendered = index_parser.evaluate(index_template)
    write(index_parser, 'MIT Musical Theatre Guild', rendered, 'site', 'index.html')


def print_usage():
    print('usage: make.py all      # remake all files')
    print('       make.py shows    # remake only the show pages')
    print('       make.py about    # remake only the about page')


if __name__ == '__main__':
    main()
