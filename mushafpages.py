#!/bin/python

import sys
import zipfile
import warnings
import re
import os
from io import BytesIO
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

zip_file = zipfile.ZipFile(sys.argv[1], 'r')
riwaayah = sys.argv[2]
word_doc = [x for x in zip_file.namelist() if '.docx' in x][0]
word_zip = zipfile.ZipFile(BytesIO(zip_file.read(word_doc)))
decoded = word_zip.read('word/document.xml').decode()
pages = decoded.split('w:br w:type="page"')

surah_regex = '^س[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\ufc62]و[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\ufc62]?ر[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\ufc62]ة[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\ufc62]'
basmalah_regex = '^ب[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\ufc62]س[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]?م[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]\s+[ٱا][\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\u06ec\ufc62]*لل[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]+ه[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]\s+[ٱا][\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\u06ec\ufc62]*لر[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]+ح[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]?م[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62\u0670]+ن[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]\s+[ٱا][\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\u06ec\ufc62]*لر[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]+ح[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]ي[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]?م[\u064e\u064f\u0650\u0651\u0652\u064c\u064b\u064d\u0640\u06e1\ufc62]'

for index, page in enumerate(pages):
    soup = BeautifulSoup(page, features='lxml')
    text = [x.text.strip() for x in soup.select("w\:t")]

    html = []
    separator = "w:jc"
    try:
        first = BeautifulSoup(page.split(separator)[int(not index)], 'lxml')
        first_text = ''.join([x.text for x in first.select('w\:t')])
    except IndexError:
        separator = "w:spacing"
        first = BeautifulSoup(page.split(separator)[int(not index)], 'lxml')
        first_text = ''.join([x.text for x in first.select('w\:t')])

    if re.match(surah_regex, first_text):
        html.append(f'<h1 class="surah">{first_text}</h1>')
        split = "".join(page.split(separator)[int(not index) + 1:])
        soup = BeautifulSoup(split, features='lxml')
        text = [x.text for x in soup.select("w\:t")]

    ayah_text = ''
    for portion in text:
        if re.match(basmalah_regex, portion):
            html.append(f'<h2 class="basmalah">{portion}</h2>')
        elif re.match('[٠-٩\s]', portion):
            ayah_text = ayah_text.strip()
            html.append(f'<span class="text">{ayah_text}</span>')
            ayah_text = ''
            html.append(f'<span class="ayah_num">{portion}</span>')
        elif portion != '':
            ayah_text += portion

    # if index == 0:
        # exit()

    basmalah = [x for x in html if 'h2' in x]
    if basmalah:
        basmalah = basmalah[0]
        basmalah_index = html.index(basmalah)
        post_basmalah_index = basmalah_index + 1
        if post_basmalah_index < len(html):
            post_basmalah = html[post_basmalah_index]
            if 'ayah' in post_basmalah:
                html.pop(post_basmalah_index)
                post_basmalah = ' ' + post_basmalah
                html[basmalah_index] = html[basmalah_index].replace('</h2>', post_basmalah + '</h2>')

    page_num = index + 1
    riwaayah_dir = f'MushafPages/{riwaayah}'
    html_file = f'{riwaayah_dir}/{page_num}.html'

    try:
        os.mkdir(riwaayah_dir)
    except FileExistsError:
        pass

    with open(html_file, 'w') as f:
        f.write('\n'.join(html))
