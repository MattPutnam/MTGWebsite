import re
from os import listdir, path

import utils
from utils import load_or_die, root, render_page, write

show_template = load_or_die('templates', 'show.htmpl')
summary_template = load_or_die('templates', 'summary.htmpl')


def render_shows():
    years = [year for year in listdir(path.join(root, 'site')) if re.match("\d{4}", year)]
    years.sort()
    seasons = ['IAP', 'Spring', 'Summer', 'Fall']

    is_future = True
    show_list = []

    for year in reversed(years):
        for season in reversed(seasons):
            is_current = [year, season] == utils.current_show
            if is_current:
                is_future = False

            utils.cur_path = path.join(root, 'site', year, season)
            if path.isdir(utils.cur_path):
                make_show_page(year, season, is_current, is_future, show_list)

    write('MTG - Show List', "".join(show_list), 'site', 'show_list.html')


def make_show_page(year, season, is_current, is_future, show_list):
    yaml_path = path.join(root, 'site', year, season, 'show.yaml')
    if not path.isfile(yaml_path):
        return

    show_data = load_or_die(yaml_path)

    graphic = utils.find_show_file('graphic')
    if graphic:
        graphic = year + '/' + season + '/' + graphic
    else:
        if is_current or is_future:
            graphic = 'images/comingsoon.jpg'
        else:
            graphic = 'images/placeholder.png'
    banner = utils.find_show_file('banner')

    show_data.update({'year': year, 'season': season, 'graphic': graphic})
    if banner:
        show_data['banner'] = banner

    rendered = render_page(show_template, {}, show_data)
    write('MTG - ' + show_data['Title'] + ' (' + year + ")", rendered, 'site', year, season, 'show.html')

    show_list.append(render_page(summary_template, {}, show_data))
