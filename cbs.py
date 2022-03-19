#!/usr/bin/env python3

import socket, ssl, urllib
import PySimpleGUI as sg

urllib.parse.uses_relative.append('gemini')
urllib.parse.uses_netloc.append('gemini')


# ------------------------------------------------------------------------------
# Settings


homepage = 'gemini://medusae.space/index.gmi'

preform_font = 'courier 10'
preform_color = 'gray'

content_font = 'helvetica 10'
content_color = 'black'

link_font = content_font
link_color = 'blue'

list_font = content_font
list_color = content_color

quote_font = content_font
quote_color = content_color

h3_font = 'helvetica 14'
h3_color = 'green'
h2_font = 'helvetica 18'
h2_color = 'green'
h1_font = 'helvetica 22'
h1_color = 'green'


# ------------------------------------------------------------------------------


def gemini_request(url):
    """
    Make a request to a Gemini server
    :param url: URL to request
    :return: Tuple(status:int, meta:str, body:str)
    """

    parsed = urllib.parse.urlparse(url)
    ctxt = ssl.create_default_context()
    ctxt.check_hostname = False
    ctxt.verify_mode = ssl.CERT_NONE
    with socket.create_connection((parsed.hostname, parsed.port or 1965)) as sock:
        with ctxt.wrap_socket(sock, server_hostname=parsed.hostname) as ssock:
            ssock.write((url + '\r\n').encode('utf-8'))
            resp = b''
            while data := ssock.recv(4096):
                resp += data
    resp = resp.split(b'\r\n', maxsplit=1)
    header = resp[0].split(maxsplit=1)
    status = int(header[0] if len(header) >= 1 else b'')
    meta = header[1] if len(header) >= 2 else b''
    body = resp[1] if len(resp) >= 1 else b''
    return status, meta.decode('utf-8'), body.decode('utf-8')


def browser_window_layout():
    # Navbar
    nav = [sg.Button('Back'), sg.Button('Forward'), sg.Text('URL:'), sg.InputText(homepage, expand_x=True, key='-URL-'), sg.Button('Go'), sg.Button('Home')]

    # Pane contents
    overv = [[sg.Listbox([], enable_events=True, horizontal_scroll=True, expand_x=True, expand_y=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, key='-OVERV-')]]
    certs = [[sg.Listbox([], enable_events=True, horizontal_scroll=True, expand_x=True, expand_y=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, key='-CERTS-')]]
    links = [[sg.Listbox([], enable_events=True, horizontal_scroll=True, expand_x=True, expand_y=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, key='-LINKS-')]]

    # Panes
    left_sidebar = sg.Column([[sg.TabGroup([
        [sg.Tab('Overview', overv), sg.Tab('Certs', certs)]
    ], expand_x=True, expand_y=True)]])
    content = sg.Column([
        [sg.Multiline(size=(100, 100), expand_x=True, expand_y=True, write_only=True, key='-CONTENT-')]
    ])
    right_sidebar = sg.Column([[sg.TabGroup([
        [sg.Tab('Links', links)]
    ], expand_x=True, expand_y=True)]])

    # Window
    return [
        nav,
        [sg.Pane([left_sidebar, content, right_sidebar], orientation='h', expand_x=True, expand_y=True)],
    ]


class Client(object):
    def __init__(self):
        self.window = sg.Window('Gemini Client', browser_window_layout(), resizable=True)
        self.links = []
        self.overview = []

    def update_content_gemtext(self, content: str):
        is_format = True
        self.window['-CONTENT-'].update('')
        new_links = []
        new_overv = []
        pos = 0
        for line in content.splitlines(keepends=True):
            if line.startswith('```'):
                is_format = not is_format
                continue
            if not is_format:
                # FIXME: This will still word-wrap - probably nothing to be done about that
                self.window['-CONTENT-'].update(line, text_color_for_value=preform_color, font_for_value=preform_font,
                                                append=True)
            elif line.startswith('=>'):
                splitlink = line[2:].strip().split(maxsplit=1)
                link = urllib.parse.urljoin(self.window['-URL-'].get(),
                                            (splitlink[0] if len(splitlink) >= 1 else '').strip())
                text = (splitlink[1] if len(splitlink) >= 2 else '').strip()
                self.window['-CONTENT-'].update('[{}] => {} {}\n'.format(len(new_links), link, text),
                                           text_color_for_value=link_color, font_for_value=link_font, append=True)
                new_links.append((text or link, link))
            elif line.startswith('###'):
                self.window['-CONTENT-'].update(line[4:], text_color_for_value=h3_color, font_for_value=h3_font, append=True)
                new_overv.append((pos, line))
            elif line.startswith('##'):
                self.window['-CONTENT-'].update(line[3:], text_color_for_value=h2_color, font_for_value=h2_font, append=True)
                new_overv.append((pos, line))
            elif line.startswith('#'):
                self.window['-CONTENT-'].update(line[2:], text_color_for_value=h1_color, font_for_value=h1_font, append=True)
                new_overv.append((pos, line))
            elif line.startswith('*'):
                self.window['-CONTENT-'].update(line, text_color_for_value=list_color, font_for_value=list_font, append=True)
            elif line.startswith('>'):
                self.window['-CONTENT-'].update(line, text_color_for_value=quote_color, font_for_value=quote_font,
                                           append=True)
            else:
                self.window['-CONTENT-'].update(line, text_color_for_value=content_color, font_for_value=content_font,
                                           append=True)
            pos += 1 + int(len(line) / 120)  # Just sorta assume that lines wrap aroundabout 120 characters
        self.window['-LINKS-'].update(['{} - {}'.format(i, text) for i, (text, _) in enumerate(new_links)])
        self.window['-OVERV-'].update([line for (p, line) in new_overv])
        self.links = [link for (text, link) in new_links]
        self.overview = [p / pos for (p, line) in new_overv]


class History(object):
    def __init__(self):
        self._hist = []
        self._i = -1

    def back(self):
        if len(self._hist) > -self._i:
            self._i -= 1
            return self._hist[self._i]

    def forward(self):
        if self._i < -1:
            self._i += 1
            return self._hist[self._i]

    def add(self, url):
        if self._i < -1: self._hist = self._hist[:self._i+1]
        self._i = -1
        self._hist.append(url)


def load_url(client, url):
    # TODO: only update the window url for gemini:// urls, do something different for other schemes
    client.window['-URL-'].update(url)
    status, meta, body = gemini_request(url)

    # TODO: examine meta field for other mime types
    if 10 <= status < 20:
        # Input request
        layout = [[sg.Text(meta)], [sg.InputText()], [sg.Submit(), sg.Cancel()]]
        event, values = sg.Window('Input Requested', layout).read(close=True)
        query = '?' + urllib.parse.quote(values[0])
        url = urllib.parse.urljoin(client.window['-URL-'].get(), query)
        return load_url(client.window, url)
    elif 20 <= status < 30:  # if instead of elif to allow processing of new request made with input
        pass  # Success
    elif 30 <= status < 40:
        body = '# {} - Redirect\n## {}'.format(status, meta)
        # TODO: auto-redirect?
    elif 40 <= status < 50:
        body = '# {} - Temporary falure\n## {}'.format(status, meta)
    elif 50 <= status < 60:
        body = '# {} - Permanent falure\n## {}'.format(status, meta)
    elif 60 <= status < 70:
        body = '# {} - Certificate required\n## {}'.format(status, meta)
    else:
        body = '# {} - Unknown status code\n## {}'.format(status, meta)
    return client.update_content_gemtext(body)


def main():
    client = Client()
    #window = sg.Window('Gemini Client', browser_window_layout(), resizable=True)
    hist = History()
    hist.add(homepage)
    client.window.finalize()
    load_url(client, homepage)
    while True:
        event, values = client.window.read()
        if event == sg.WIN_CLOSED:
            break
        else:
            if event == 'Go':
                hist.add(values['-URL-'])
                url = values['-URL-']
            elif event == 'Back':
                if url := hist.back() is None:
                    continue  # Nothing to go back to, no page load
            elif event == 'Forward':
                if url := hist.forward() is None:
                    continue  # Nothing to go forward to, no page load
            elif event == 'Home':
                url = homepage
            elif event == '-LINKS-':
                url = client.links[client.window['-LINKS-'].get_indexes()[0]]
            elif event == '-OVERV-':
                item = client.window['-OVERV-'].get_indexes()[0]
                client.window['-CONTENT-'].set_vscroll_position(client.overview[item])
                continue  # No page load, only scroll existing content
            else:
                continue  # Unexpected event, ignore it
            load_url(client, url)


if __name__ == '__main__':
    main()
