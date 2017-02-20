import shows
import utils
from utils import load_or_die, render_page, write
from yattag import Doc


def main():
    main_data = load_or_die('site', 'main.yaml')
    utils.current_show = main_data['Current Show'].split('/')

    render_about(main_data)
    shows.render_shows()
    render_index()


def render_about(main_data):
    about_template = load_or_die('templates', 'about.htmpl')
    rendered = render_page(about_template, main_data, {})
    write('MTG - About MTG', rendered, 'site', 'about.html')


def render_index():
    year, season = utils.current_show
    doc, tag, text = Doc().tagtext()
    with tag('html'):
        with tag('head'):
            doc.stag('meta', ('http-equiv', 'refresh'), content="0; url='" + year + "/" + season + "/show.html'")

    file = open('../site/index.html', 'w')
    file.write(doc.getvalue())
    file.close()


if __name__ == "__main__":
    main()
