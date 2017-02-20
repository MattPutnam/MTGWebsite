import shows
import utils
from utils import load_or_die, render_page, write


def main():
    main_data = load_or_die('site', 'main.yaml')
    utils.current_show = main_data['Current Show'].split('/')

    render_index(main_data)
    render_about(main_data)
    shows.render_shows()


def render_about(main_data):
    about_template = load_or_die('templates', 'about.htmpl')
    rendered = render_page(about_template, context='main', main_data=main_data)
    write('MTG - About MTG', rendered, 'main', 'site', 'about.html')


def render_index(main_data):
    index_template = load_or_die('templates', 'index.htmpl')
    rendered = render_page(index_template, context='main',
                           local_data={'current_show': main_data['Current Show'] + "/show.html"})
    file = open('../site/index.html', 'w')
    file.write(rendered)
    file.close()


if __name__ == "__main__":
    main()
