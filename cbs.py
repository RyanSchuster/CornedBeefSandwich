#!/usr/bin/env python3

import socket, ssl, urllib
import PySimpleGUI as sg


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

h3_font = 'helvetica 14'
h3_color = 'green'
h2_font = 'helvetica 18'
h2_color = 'green'
h1_font = 'helvetica 22'
h1_color = 'green'


# ------------------------------------------------------------------------------


def gemini_request(url):
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
            return resp


def browser_window_layout():
    return [
        [sg.Button('Back'), sg.Button('Forward'), sg.Text('URL:'), sg.InputText(homepage, key='-URL-'), sg.Button('Go'), sg.Button('Home')],
        [sg.Multiline(size=(100, 100), expand_x=True, expand_y=True, write_only=True, key='-CONTENT-')]
    ]


def update_content(window):
    is_format = True
    window['-CONTENT-'].update('')
    content = gemini_request(window['-URL-'].get()).decode('utf-8')
    for line in content.splitlines(keepends=True):
        if line.startswith('```'):
            is_format = not is_format
            continue
        if not is_format:
            window['-CONTENT-'].update(line, text_color_for_value=preform_color, font_for_value=preform_font, append=True)
        elif line.startswith('=> '):
            window['-CONTENT-'].update(line, text_color_for_value=link_color, font_for_value=link_font, append=True)
        elif line.startswith('# '):
            window['-CONTENT-'].update(line[2:], text_color_for_value=h1_color, font_for_value=h1_font, append=True)
        elif line.startswith('## '):
            window['-CONTENT-'].update(line[3:], text_color_for_value=h2_color, font_for_value=h2_font, append=True)
        elif line.startswith('###'):
            window['-CONTENT-'].update(line[4:], text_color_for_value=h3_color, font_for_value=h3_font, append=True)
        elif line.startswith('* '):
            window['-CONTENT-'].update(line, text_color_for_value=list_color, font_for_value=list_font, append=True)
        else:
            window['-CONTENT-'].update(line, text_color_for_value=content_color, font_for_value=content_font, append=True)


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


def main():
    window = sg.Window('Gemini Client', browser_window_layout(), resizable=True)
    hist = History()
    hist.add(window['-URL-'].get())
    window.finalize()
    update_content(window)
    while True:
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED:
            break
        else:
            if event == 'Go':
                hist.add(values['-URL-'])
            elif event == 'Back':
                if url := hist.back():
                    window['-URL-'].update(url)
            elif event == 'Forward':
                if url := hist.forward():
                    window['-URL-'].update(url)
            elif event == 'Home':
                window['-URL-'].update(homepage)
            update_content(window)


if __name__ == '__main__':
    main()
