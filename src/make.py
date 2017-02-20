import shows
import utils
from utils import load_or_die, render_template, write

import yaml
import collections


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
    utils.main_data = main_data
    utils.current_show_tokens = main_data['Current Show'].split('/')

    render_index()
    render_about()
    shows.render_shows()

    print("Success!")


def render_about():
    about_template = load_or_die('templates', 'about.htmpl')
    rendered = render_template(about_template, context='main')
    write('MTG - About MTG', rendered, 'main', 'site', 'about.html')


def render_index():
    index_template = load_or_die('templates', 'index.htmpl')
    rendered = render_template(index_template, context='main')
    file = open('../site/index.html', 'w')
    file.write(rendered)
    file.close()


if __name__ == '__main__':
    main()
