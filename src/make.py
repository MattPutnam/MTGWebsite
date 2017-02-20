import shows
import utils
from utils import load_or_die, render_page, write


def main():
    main_data = load_or_die('site', 'main.yaml')
    main_data['current_show_page'] = main_data['Current Show'] + '/show.html'
    utils.main_data = main_data
    utils.current_show_tokens = main_data['Current Show'].split('/')

    render_index()
    render_about()
    shows.render_shows()


def render_about():
    about_template = load_or_die('templates', 'about.htmpl')
    rendered = render_page(about_template, context='main')
    write('MTG - About MTG', rendered, 'main', 'site', 'about.html')


def render_index():
    index_template = load_or_die('templates', 'index.htmpl')
    rendered = render_page(index_template, context='main')
    file = open('../site/index.html', 'w')
    file.write(rendered)
    file.close()


if __name__ == "__main__":
    main()
