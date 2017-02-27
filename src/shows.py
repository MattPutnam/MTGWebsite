import re
from copy import deepcopy
from os import listdir, path

import utils
from utils import load_or_die, write

show_template = load_or_die('templates', 'show.htmpl')
summary_template = load_or_die('templates', 'summary.htmpl')


def render_shows(parser, current_show_tokens):
    years = [year for year in listdir(path.join(utils.root, 'site')) if re.match("\d{4}", year)]
    years.sort()
    seasons = ['IAP', 'Spring', 'Summer', 'Fall']

    is_future = True
    show_list = []

    for year in reversed(years):
        for season in reversed(seasons):
            is_current = [year, season] == current_show_tokens
            if is_current:
                is_future = False

            cur_path = path.join(utils.root, 'site', year, season)
            if path.isdir(cur_path):
                make_show_page(parser, cur_path, year, season, is_current, is_future, show_list)

    write(parser,
          'MTG - Show List',
          "".join(show_list),
          'site', 'show_list.html')


def make_show_page(main_parser, show_path, year, season, is_current, is_future, show_list):
    yaml_path = path.join(show_path, 'show.yaml')
    if not path.isfile(yaml_path):
        return

    show_data = load_or_die(yaml_path)

    graphic = utils.find_show_file(show_path, 'graphic')
    if graphic:
        graphic = year + '/' + season + '/' + graphic
    else:
        if is_current or is_future:
            graphic = 'images/comingsoon.jpg'
        else:
            graphic = 'images/placeholder.png'

    show_data.update({'year': year, 'season': season, 'graphic': graphic})

    main_parser.data['show'] = show_data
    show_parser = deepcopy(main_parser)
    show_parser.path=[year, season]

    rendered = show_parser.evaluate(show_template)

    write(show_parser,
          'MTG - ' + show_data['Title'] + ' (' + year + ")",
          rendered,
          'site', year, season, 'show.html')

    show_list.append(main_parser.evaluate(summary_template))
