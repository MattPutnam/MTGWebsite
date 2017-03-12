import re
from copy import deepcopy
from os import listdir, path

import utils
from htmpl import compile_template
from utils import load_or_die, write

compiled_show_template = compile_template(load_or_die('templates', 'show.htmpl'))
compiled_summary_template = compile_template(load_or_die('templates', 'summary.htmpl'))
compiled_show_list_template = compile_template(load_or_die('templates', 'show_list.htmpl'))

seasons = ['IAP', 'Spring', 'Summer', 'Fall']

current_year = 0
current_season = ''


def render_show_page(main_data, year, season):
    """
    Renders the show page for a given slot, if it exists
    :param main_data: the main TemplateData instance
    :param year: the year to target
    :param season: the season to target
    :return: empty
    """
    yaml_path = path.join(utils.root, 'site', year, season, 'show.yaml')
    if not path.isfile(yaml_path):
        return

    show_data = load_or_die(yaml_path)
    show_data.update({'year': year,
                      'season': season,
                      'graphic': get_show_graphic(year, season),
                      'is_current': year == current_year and season == current_season})

    show_template_data = deepcopy(main_data)
    show_template_data.bind('show', show_data)
    show_template_data.path = [year, season]

    rendered = compiled_show_template.evaluate(show_template_data)
    write(show_template_data,
          'MTG - ' + show_data['Title'] + ' (' + year + ")",
          rendered,
          'site', year, season, 'show.html')


def render_all_show_pages(main_data):
    """
    Renders all show pages that have a year/season/show.yaml defined
    :param main_data: the main TemplateData instance
    :return: empty
    """
    for year in get_defined_years():
        for season in reversed(seasons):
            render_show_page(main_data, year, season)


def make_show_list(main_data):
    """
    Renders the show list page
    :param main_data: the main TemplateData instance
    :return: empty
    """
    show_template_data = deepcopy(main_data)
    show_summaries = []

    for year in get_defined_years():
        for season in reversed(seasons):
            yaml_path = path.join(utils.root, 'site', year, season, 'show.yaml')
            if not path.isfile(yaml_path):
                continue

            show_data = load_or_die(yaml_path)
            graphic = get_show_graphic(year, season)
            is_current = year == current_year and season == current_season
            show_data.update({'year': year, 'season': season, 'graphic': graphic, 'is_current': is_current})

            show_template_data.bind('show', show_data)
            show_summaries.append(compiled_summary_template.evaluate(show_template_data))

    show_list_data = deepcopy(main_data)
    show_list_data.bind('show_list', show_summaries)

    write(show_list_data,
          'MTG - Show List',
          compiled_show_list_template.evaluate(show_list_data),
          'site', 'show_list.html')


def get_defined_years():
    """
    Gets the list of years that are defined in /site
    :return: the defined show years, in reverse order (most recent first)
    """
    years = [year for year in listdir(path.join(utils.root, 'site')) if re.match("\d{4}", year)]
    years.sort()
    years.reverse()
    return years


def is_upcoming(query_year, query_season):
    """
    Determines if the given year/season represents an upcoming (or current) show
    :param query_year: the year to test
    :param query_season: the season to test
    :return: True iff this is a future or current show
    """
    if current_year == 0:
        raise ValueError('current_year has not been set')

    if query_year > current_year:
        return True
    elif query_year < current_year:
        return False
    else:
        return seasons.index(query_season) >= seasons.index(current_season)


def get_show_graphic(year, season):
    """
    Gets the appropriate graphic image for a given show slot
    :param year: the year to query
    :param season: the season to query
    :return: [year]/[season]'s show graphic, or the proper placeholder if it doesn't exist
    """
    graphic = utils.find_show_file(path.join(utils.root, 'site', year, season), 'graphic')
    if graphic:
        return year + '/' + season + '/' + graphic
    else:
        if is_upcoming(year, season):
            return 'images/comingsoon.jpg'
        else:
            return 'images/placeholder.png'
