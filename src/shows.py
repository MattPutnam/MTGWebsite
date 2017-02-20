from yattag import Doc
import utils
from utils import load_or_die, root, render_page, write, make_venue_link
from os import listdir, path
import re


show_template = load_or_die('templates', 'show.htmpl')


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
    rendered = render_page(show_template, {}, show_data)
    write('MTG - ' + show_data['Title'] + ' (' + year + ")", rendered, 'site', year, season, 'show.html')

    show_list.append(make_show_banner(year, season, is_current, is_future, show_data))


def make_show_banner(year, season, is_current, is_future, show_data):
    if is_current:
        performance_verb = 'in'
    elif is_future:
        performance_verb = 'will be in'
    else:
        performance_verb = 'were in'

    graphic = utils.find_show_file('graphic')
    if graphic:
        graphic = year + '/' + season + '/' + graphic
    else:
        if is_current or is_future:
            graphic = 'images/comingsoon.jpg'
        else:
            graphic = 'images/placeholder.png'

    link = path.join(year, season, 'show.html')

    doc, tag, text, line = Doc().ttl()

    with tag('div', klass='show_summary'):
        with tag('a', klass='summary_graphic', href=link):
            doc.stag('img', src=graphic)
        with tag('div', klass='summary_info'):
            with tag('div', klass='summary_slot'):
                text(season + ' ' + year)
            with tag('a', href=link, klass='summary_title'):
                text(show_data['Title'])
            with tag('div', klass='summary_credits'):
                text(show_data['Credits'])
            with tag('div', klass='summary_dates'):
                text(show_data['Performance Dates'])
            with tag('div', klass='summary_venue'):
                doc.asis('Performances ' + performance_verb + ' ' + make_venue_link(show_data['Venue']))

    return doc.getvalue()

