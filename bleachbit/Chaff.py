# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2019 Andrew Ziem
# https://www.bleachbit.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import email.generator
from email.mime.text import MIMEText
import json
import logging
import os
import random
import tempfile
from datetime import datetime, timedelta

try:
    import certifi
except:
    HAVE_CERTIFI = False
else:
    HAVE_CERTIFI = True

from bleachbit import _
from bleachbit import options_dir

import markovify

logger = logging.getLogger(__name__)

RECIPIENTS = ['0emillscd@state.gov', '1ilotylc@state.gov', 'abdinh@state.gov', 'abedin@state.gov', 'abedinh@state.gov', 'abendinh@state.gov', 'adedinh@state.gov', 'adlerce@state.gov', 'aliilscd@state.gov', 'baerdb@state.gov', 'baldersonkm@state.gov', 'balderstonkm@state.gov', 'bam@mikuiski.senate.gov', 'bam@mikulski.senate.gov', 'bealeca@state.gov', 'bedinh@state.gov', 'benjamin_moncrief@lemieux.senate.gov', 'blaker2@state.gov', 'brimmere@state.gov', 'brod17@clintonemail.com', 'burnswj@state.gov', 'butzgych2@state.gov', 'campbelikm@state.gov', 'carsonj@state.gov', 'cholletdh@state.gov', 'cindy.buhl@mail.house.gov', 'colemancl@state.gov', 'crowleypj@state.gov', 'danielil@state.gov', 'daniew@state.gov', 'david_garten@lautenberg.senate.gov', 'dewanll@state.gov', 'dilotylc@state.gov', 'eabedinh@state.gov', 'emillscd@state.gov', 'esullivanjj@state.gov', 'feltmanjd@state.gov', 'filotylc@state.gov', 'fuchsmh@state.gov', 'gll@state.gov', 'goldbergps@state.gov', 'goldenjr@state.gov', 'gonzalezjs@state.gov', 'gordonph@state.gov', 'h@state.gov', 'hanieymr@state.gov', 'hanleymr@state.gov', 'hanleyrnr@state.gov', 'harileymr@state.gov', 'hdr22@clintonemai1.com', 'hilicr@state.gov', 'hillcr@state.gov', 'holbrookerc@state.gov', 'hormatsrd@state.gov', 'hr15@att.blackberry.net', 'hr15@mycingular.blackberry.net', 'hrod17@clintonemail.com', 'huma@clintonemail.com', 'hyded@state.gov', 'ian1evqr@state.gov', 'ieltmanjd@state.gov', 'iewjj@state.gov', 'iilotylc@state.gov', 'imillscd@state.gov', 'info@mailva.evite.com', 'inh@state.gov',
              'iviillscd@state.gov', 'jilotylc@state.gov', 'jj@state.gov', 'jonespw2@state.gov', 'kellyc@state.gov', 'klevorickcb@state.gov', 'kohhh@state.gov', 'kohliff@state.gov', 'laszczychj@state.gov', 'lc@state.gov', 'lewij@state.gov', 'lewjj@state.gov', 'lewn@state.gov', 'lilotylc@state.gov', 'macmanusje@state.gov', 'marshalicp@state.gov', 'marshallcp@state.gov', 'mchaleja@state.gov', 'mhcaleja@state.gov', 'millscd@state.aov', 'millscd@state.gov', 'millscd@tate.gov', 'mr@state.gov', 'muscantinel@state.gov', 'muscatinel@state.gov', 'nidestr@state.gov', 'njj@state.gov', 'nulandvi@state.gov', 'ogordonph@state.gov', 'oterom2@state.gov', 'posnermh@state.gov', 'postmaster@state.gov', 'r@state.gov', 'reines@state.gov', 'reinesp@state.gov', 'reinespi@state.gov', 'ricese@state.gov', 'rnillscd@state.gov', 'rodriguezme@state.gov', 'rooneym@state.gov', 's_specialassistants@state.gov', 'schwerindb@state.gov', 'shannonta@state.gov', 'shapiroa@state.gov', 'shermanwr@state.gov', 'slaughtera@state.gov', 'smithje@state.gov', 'steinbertjb@state.gov', 'sterntd@state.gov', 'stillivaral@state.gov', 'sullivanjj@state.gov', 'tanleyrnr@state.gov', 'tauschere0@state.gov', 'tauschereo@state.gov', 'tillemannts@state.gov', 'toivnf@state.gov', 'tommy_ross@reid.senate.gov', 'u@state.gov', 'ullivanjj@state.gov', 'vaimorou@state.gov', 'valenzuelaaa@state.gov', 'valmdrou@state.gov', 'valmmorolj@state.gov', 'valmorolj@state.gov', 'vermarr@state.gov', 'verveerms@state.gov', 'walmorou@state.gov', 'werveerms@state.gov', 'woodardew@state.gov', 'yeryeerms@state.gov']
DEFAULT_SUBJECT_LENGTH = 64
DEFAULT_NUMBER_OF_SENTENCES = 5
URL_SUBJECT = 'https://sourceforge.net/projects/bleachbit/files/chaff/subject_model.json.bz2/download'
URL_CONTENT = 'https://sourceforge.net/projects/bleachbit/files/chaff/content_model.json.bz2/download'
DEFAULT_CONTENT_MODEL_PATH = os.path.join(
    options_dir, 'clinton_content_model.json.bz2')
DEFAULT_SUBJECT_MODEL_PATH = os.path.join(
    options_dir, 'clinton_subject_model.json.bz2')


def _load_model(model_path):
    _open = open
    if model_path.endswith('.bz2'):
        import bz2
        _open = bz2.BZ2File
    with _open(model_path, 'r') as model_file:
        return markovify.Text.from_dict(json.load(model_file))


def load_subject_model(model_path):
    return _load_model(model_path)


def load_content_model(model_path):
    return _load_model(model_path)


def _get_random_recipient():
    return random.choice(RECIPIENTS)


def _get_random_datetime(min_year=2011, max_year=2012):
    date = datetime.strptime('{} {}'.format(random.randint(
        1, 365), random.randint(min_year, max_year)), '%j %Y')
    # Saturday, September 15, 2012 2:20 PM
    return date.strftime('%A, %B %d, %Y %I:%M %p')


def _get_random_content(content_model, number_of_sentences=DEFAULT_NUMBER_OF_SENTENCES):
    content = []
    for _ in range(number_of_sentences):
        content.append(content_model.make_sentence())
        content.append(random.choice([' ', '\n']))
    try:
        return MIMEText(''.join(content))
    except UnicodeEncodeError:
        return _get_random_content(content_model, number_of_sentences=number_of_sentences)


def _generate_email(subject_model, content_model, number_of_sentences=DEFAULT_NUMBER_OF_SENTENCES, subject_length=DEFAULT_SUBJECT_LENGTH):
    message = _get_random_content(
        content_model, number_of_sentences=number_of_sentences)

    message['Subject'] = subject_model.make_short_sentence(subject_length)
    message['To'] = _get_random_recipient()
    message['From'] = _get_random_recipient()
    message['Sent'] = _get_random_datetime()

    return message


def download_models(content_model_path=DEFAULT_CONTENT_MODEL_PATH, subject_model_path=DEFAULT_SUBJECT_MODEL_PATH, on_error=None):
    """Download models

    Calls on_error(primary_message, secondary_message) in case of error

    Returns success as boolean value
    """
    from urllib2 import urlopen, URLError, HTTPError
    from httplib import HTTPException
    import socket
    if HAVE_CERTIFI:
        cafile = certifi.where()
    else:
        cafile = None
    for (url, fn) in ((URL_SUBJECT, subject_model_path), (URL_CONTENT, content_model_path)):
        if os.path.exists(fn):
            logger.debug('File %s already exists', fn)
            continue
        logger.info('Downloading %s to %s', url, fn)
        try:
            resp = urlopen(url, cafile=cafile)
            with open(fn, 'wb') as f:
                f.write(resp.read())
        except (URLError, HTTPError, HTTPException, socket.error) as exc:
            msg = _('Downloading url failed: %s') % url
            msg2 = '{}: {}'.format(type(exc).__name__, exc)
            logger.exception(msg)
            if on_error:
                on_error(msg, msg2)
            from bleachbit.FileUtilities import delete
            delete(fn, ignore_missing=True)  # delete any partial download
            return False
    return True


def generate_emails(number_of_emails, content_model_path, subject_model_path, email_output_dir,
                    number_of_sentences=DEFAULT_NUMBER_OF_SENTENCES, on_progress=None, *kwargs):
    logger.debug('Loading two email models')
    subject_model = load_subject_model(subject_model_path)
    content_model = load_content_model(content_model_path)
    logger.debug('Generating {:,} emails'.format(number_of_emails))
    for i in range(1, number_of_emails + 1):
        with tempfile.NamedTemporaryFile(prefix='outlook-', suffix='.eml', dir=email_output_dir, delete=False) as email_output_file:
            email_generator = email.generator.Generator(email_output_file)
            msg = _generate_email(
                subject_model, content_model, number_of_sentences=number_of_sentences)
            email_generator.write(msg.as_string())
        if on_progress:
            on_progress(1.0*i/number_of_emails)
