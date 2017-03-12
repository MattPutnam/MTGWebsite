import collections
import sys
import time
from copy import deepcopy

import yaml

import shows
from htmpl import TemplateData, evaluate_template
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

    current_year, current_season = main_data['Current Show'].split('/')
    shows.current_year = current_year
    shows.current_season = current_season

    data = {'main': main_data,
            'current': load_or_die('site', current_year, current_season, 'show.yaml'),
            'venues': load_or_die('site', 'venues.yaml'),
            'tickets': load_or_die('site', 'tickets.yaml')}

    template_data = TemplateData(data, root + '/site', [])

    if command == 'all':
        make_all(template_data)
    elif command == 'shows':
        make_shows(template_data)
    elif command == 'about':
        render_about(template_data)
    else:
        print_usage()
        exit()

    print('Success!')
    print('Completed in %s seconds' % (time.time() - start_time))


def make_all(template_data):
    render_index(template_data)
    make_shows(template_data)
    render_about(template_data)
    render_directions(template_data)
    render_faq(template_data)
    render_contact(template_data)


def make_shows(template_data):
    shows.render_all_show_pages(template_data)
    shows.make_show_list(template_data)


def render_about(template_data):
    about_template = load_or_die('templates', 'about.htmpl')
    rendered = evaluate_template(about_template, template_data)
    write(template_data, 'MTG - About MTG', rendered, 'site', 'about.html')


def render_index(template_data):
    index_template = load_or_die('templates', 'index.htmpl')
    year, season = template_data.data['main']['Current Show'].split('/')

    graphic = shows.get_show_graphic(year, season)

    current_show_data = load_or_die('site', year, season, 'show.yaml')
    current_show_data.update({'year': year, 'season': season, 'graphic': graphic})

    index_data = deepcopy(template_data)
    index_data.bind('show', current_show_data)

    rendered = evaluate_template(index_template, index_data)
    write(index_data, 'MIT Musical Theatre Guild', rendered, 'site', 'index.html')


def render_directions(template_data):
    directions_template = load_or_die('templates', 'directions.htmpl')
    rendered = evaluate_template(directions_template, template_data)
    write(template_data, 'MTG - Directions', rendered, 'site', 'directions.html')


def render_faq(template_data):
    faq_template = load_or_die('templates', 'faq.htmpl')
    rendered = evaluate_template(faq_template, template_data)
    write(template_data, 'MTG - Frequently Asked Questions', rendered, 'site', 'faq.html')


def render_contact(template_data):
    contact_template = load_or_die('templates', 'contact.htmpl')
    rendered = evaluate_template(contact_template, template_data)
    write(template_data, 'MTG - Contact Us', rendered, 'site', 'contact.html')


def print_usage():
    print('usage: make.py all      # remake all files')
    print('       make.py shows    # remake only the show pages')
    print('       make.py about    # remake only the about page')


if __name__ == '__main__':
    main()
