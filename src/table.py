import re

from yattag import Doc, indent


def make_table(header, content):
    if not content or len(content) == 0:
        return ""

    doc, tag, text, line = Doc().ttl()

    with tag('table', klass=header.replace(' ', '_')):
        with tag('thead'):
            with tag('tr'):
                with tag('th', colspan=2):
                    text(header)

        with tag('tbody'):
            for row in content:
                if type(row) is not dict:
                    raise ValueError("Row must be a dictionary: " + row)
                if len(list(row)) is not 1:
                    raise ValueError("Row must have only one entry: " + row)

                role = list(row)[0]
                val = row[role]
                val_type = type(val)

                with tag('tr'):
                    line('td', role, klass='role')
                    with tag('td', klass='name'):
                        if val_type is str:
                            render_with_email(val, tag, text)
                        elif val_type is list:
                            for person in val:
                                render_with_email(person, tag, text)
                                doc.stag('br')
                        else:
                            raise ValueError("Exception: table entry {} has unknown value of type {}", role, val_type)

    return indent(doc.getvalue())


def render_with_email(s, tag, text):
    match = re.search("^(.+)<(.+)>$", s)
    if match:
        with tag('a', href='mailto:' + match.group(2).strip()):
            text(match.group(1).strip())
    else:
        text(s)
