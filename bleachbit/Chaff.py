# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2020 Andrew Ziem
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

import email.generator
from email.mime.text import MIMEText
import json
import logging
import os
import random
import tempfile
from datetime import datetime

from bleachbit import _, bleachbit_exe_path
from bleachbit import options_dir

from . import markovify

logger = logging.getLogger(__name__)

RECIPIENTS = ['0emillscd@state.gov', '1ilotylc@state.gov', 'abdinh@state.gov', 'abedin@state.gov', 'abedinh@state.gov', 'abendinh@state.gov', 'adedinh@state.gov', 'adlerce@state.gov', 'aliilscd@state.gov', 'baerdb@state.gov', 'baldersonkm@state.gov', 'balderstonkm@state.gov', 'bam@mikuiski.senate.gov', 'bam@mikulski.senate.gov', 'bealeca@state.gov', 'bedinh@state.gov', 'benjamin_moncrief@lemieux.senate.gov', 'blaker2@state.gov', 'brimmere@state.gov', 'brod17@clintonemail.com', 'burnswj@state.gov', 'butzgych2@state.gov', 'campbelikm@state.gov', 'carsonj@state.gov', 'cholletdh@state.gov', 'cindy.buhl@mail.house.gov', 'colemancl@state.gov', 'crowleypj@state.gov', 'danielil@state.gov', 'daniew@state.gov', 'david_garten@lautenberg.senate.gov', 'dewanll@state.gov', 'dilotylc@state.gov', 'eabedinh@state.gov', 'emillscd@state.gov', 'esullivanjj@state.gov', 'feltmanjd@state.gov', 'filotylc@state.gov', 'fuchsmh@state.gov', 'gll@state.gov', 'goldbergps@state.gov', 'goldenjr@state.gov', 'gonzalezjs@state.gov', 'gordonph@state.gov', 'h@state.gov', 'hanieymr@state.gov', 'hanleymr@state.gov', 'hanleyrnr@state.gov', 'harileymr@state.gov', 'hdr22@clintonemai1.com', 'hilicr@state.gov', 'hillcr@state.gov', 'holbrookerc@state.gov', 'hormatsrd@state.gov', 'hr15@att.blackberry.net', 'hr15@mycingular.blackberry.net', 'hrod17@clintonemail.com', 'huma@clintonemail.com', 'hyded@state.gov', 'ian1evqr@state.gov', 'ieltmanjd@state.gov', 'iewjj@state.gov', 'iilotylc@state.gov', 'imillscd@state.gov', 'info@mailva.evite.com', 'inh@state.gov',
              'iviillscd@state.gov', 'jilotylc@state.gov', 'jj@state.gov', 'jonespw2@state.gov', 'kellyc@state.gov', 'klevorickcb@state.gov', 'kohhh@state.gov', 'kohliff@state.gov', 'laszczychj@state.gov', 'lc@state.gov', 'lewij@state.gov', 'lewjj@state.gov', 'lewn@state.gov', 'lilotylc@state.gov', 'macmanusje@state.gov', 'marshalicp@state.gov', 'marshallcp@state.gov', 'mchaleja@state.gov', 'mhcaleja@state.gov', 'millscd@state.aov', 'millscd@state.gov', 'millscd@tate.gov', 'mr@state.gov', 'muscantinel@state.gov', 'muscatinel@state.gov', 'nidestr@state.gov', 'njj@state.gov', 'nulandvi@state.gov', 'ogordonph@state.gov', 'oterom2@state.gov', 'posnermh@state.gov', 'postmaster@state.gov', 'r@state.gov', 'reines@state.gov', 'reinesp@state.gov', 'reinespi@state.gov', 'ricese@state.gov', 'rnillscd@state.gov', 'rodriguezme@state.gov', 'rooneym@state.gov', 's_specialassistants@state.gov', 'schwerindb@state.gov', 'shannonta@state.gov', 'shapiroa@state.gov', 'shermanwr@state.gov', 'slaughtera@state.gov', 'smithje@state.gov', 'steinbertjb@state.gov', 'sterntd@state.gov', 'stillivaral@state.gov', 'sullivanjj@state.gov', 'tanleyrnr@state.gov', 'tauschere0@state.gov', 'tauschereo@state.gov', 'tillemannts@state.gov', 'toivnf@state.gov', 'tommy_ross@reid.senate.gov', 'u@state.gov', 'ullivanjj@state.gov', 'vaimorou@state.gov', 'valenzuelaaa@state.gov', 'valmdrou@state.gov', 'valmmorolj@state.gov', 'valmorolj@state.gov', 'vermarr@state.gov', 'verveerms@state.gov', 'walmorou@state.gov', 'werveerms@state.gov', 'woodardew@state.gov', 'yeryeerms@state.gov']
DEFAULT_SUBJECT_LENGTH = 64
DEFAULT_NUMBER_OF_SENTENCES_CLINTON = 50
DEFAULT_NUMBER_OF_SENTENCES_2600 = 50
URL_CLINTON_SUBJECT = 'https://sourceforge.net/projects/bleachbit/files/chaff/clinton_subject_model.json.bz2/download'
URL_CLINTON_CONTENT = 'https://sourceforge.net/projects/bleachbit/files/chaff/clinton_content_model.json.bz2/download'
URL_2600 = 'https://sourceforge.net/projects/bleachbit/files/chaff/2600_model.json.bz2/download'
DEFAULT_CONTENT_MODEL_PATH = os.path.join(
    options_dir, 'clinton_content_model.json.bz2')
DEFAULT_SUBJECT_MODEL_PATH = os.path.join(
    options_dir, 'clinton_subject_model.json.bz2')
DEFAULT_2600_MODEL_PATH = os.path.join(
    options_dir, '2600_model.json.bz2')


def _load_model(model_path):
    _open = open
    if model_path.endswith('.bz2'):
        import bz2
        _open = bz2.open
    with _open(model_path, 'rt', encoding='utf-8') as model_file:
        return markovify.Text.from_dict(json.load(model_file))


def load_subject_model(model_path):
    return _load_model(model_path)


def load_content_model(model_path):
    return _load_model(model_path)


def load_2600_model(model_path):
    return _load_model(model_path)


def _get_random_recipient():
    return random.choice(RECIPIENTS)


def _get_random_datetime(min_year=2011, max_year=2012):
    date = datetime.strptime('{} {}'.format(random.randint(
        1, 365), random.randint(min_year, max_year)), '%j %Y')
    # Saturday, September 15, 2012 2:20 PM
    return date.strftime('%A, %B %d, %Y %I:%M %p')


def _get_random_content(content_model, number_of_sentences=DEFAULT_NUMBER_OF_SENTENCES_CLINTON):
    content = []
    for _ in range(number_of_sentences):
        content.append(content_model.make_sentence())
        content.append(random.choice([' ', ' ', '\n\n']))
    try:
        return MIMEText(''.join(content))
    except UnicodeEncodeError:
        return _get_random_content(content_model, number_of_sentences=number_of_sentences)


def _generate_email(subject_model, content_model, number_of_sentences=DEFAULT_NUMBER_OF_SENTENCES_CLINTON, subject_length=DEFAULT_SUBJECT_LENGTH):
    message = _get_random_content(
        content_model, number_of_sentences=number_of_sentences)

    message['Subject'] = subject_model.make_short_sentence(subject_length)
    message['To'] = _get_random_recipient()
    message['From'] = _get_random_recipient()
    message['Sent'] = _get_random_datetime()

    return message


def download_url_to_fn(url, fn, on_error=None, max_retries=2, backoff_factor=0.5):
    """Download a URL to the given filename"""
    logger.info('Downloading %s to %s', url, fn)
    import requests
    import sys
    if hasattr(sys, 'frozen'):
        # when frozen by py2exe, certificates are in alternate location
        CA_BUNDLE = os.path.join(bleachbit_exe_path, 'cacert.pem')
        requests.utils.DEFAULT_CA_BUNDLE_PATH = CA_BUNDLE
        requests.adapters.DEFAULT_CA_BUNDLE_PATH = CA_BUNDLE
    from urllib3.util.retry import Retry
    from requests.adapters import HTTPAdapter
    session = requests.Session()
    # 408: request timeout
    # 429: too many requests
    # 500: internal server error
    # 502: bad gateway
    # 503: service unavailable
    # 504: gateway_timeout
    status_forcelist = (408, 429, 500, 502, 503, 504)
    # sourceforge.net directories to download mirror
    retries = Retry(total=max_retries, backoff_factor=backoff_factor,
                    status_forcelist=status_forcelist, redirect=5)
    session.mount('http://', HTTPAdapter(max_retries=retries))
    msg = _('Downloading url failed: %s') % url

    from bleachbit.Update import user_agent
    headers = {'user_agent': user_agent()}

    def do_error(msg2):
        if on_error:
            on_error(msg, msg2)
        from bleachbit.FileUtilities import delete
        delete(fn, ignore_missing=True)  # delete any partial download
    try:
        response = session.get(url, headers=headers)
        content = response.content
    except requests.exceptions.RequestException as exc:
        msg2 = '{}: {}'.format(type(exc).__name__, exc)
        logger.exception(msg)
        do_error(msg2)
        return False
    else:
        if not response.status_code == 200:
            logger.error(msg)
            msg2 = 'Status code: %s' % response.status_code
            do_error(msg2)
            return False

    with open(fn, 'wb') as f:
        f.write(content)
    return True


def download_models(content_model_path=DEFAULT_CONTENT_MODEL_PATH,
                    subject_model_path=DEFAULT_SUBJECT_MODEL_PATH,
                    twentysixhundred_model_path=DEFAULT_2600_MODEL_PATH,
                    on_error=None):
    """Download models

    Calls on_error(primary_message, secondary_message) in case of error

    Returns success as boolean value
    """
    for (url, fn) in ((URL_CLINTON_SUBJECT, subject_model_path),
                      (URL_CLINTON_CONTENT, content_model_path),
                      (URL_2600, twentysixhundred_model_path)):
        if os.path.exists(fn):
            logger.debug('File %s already exists', fn)
            continue
        if not download_url_to_fn(url, fn):
            return False
    return True


def generate_emails(number_of_emails,
                    email_output_dir,
                    content_model_path=DEFAULT_CONTENT_MODEL_PATH,
                    subject_model_path=DEFAULT_SUBJECT_MODEL_PATH,
                    number_of_sentences=DEFAULT_NUMBER_OF_SENTENCES_CLINTON,
                    on_progress=None,
                    *kwargs):
    logger.debug('Loading two email models')
    subject_model = load_subject_model(subject_model_path)
    content_model = load_content_model(content_model_path)
    logger.debug('Generating {:,} emails'.format(number_of_emails))
    generated_file_names = []
    for i in range(1, number_of_emails + 1):
        with tempfile.NamedTemporaryFile(mode='w+', prefix='outlook-', suffix='.eml', dir=email_output_dir, delete=False) as email_output_file:
            email_generator = email.generator.Generator(email_output_file)
            msg = _generate_email(
                subject_model, content_model, number_of_sentences=number_of_sentences)
            email_generator.write(msg.as_string())
            generated_file_names.append(email_output_file.name)
        if on_progress:
            on_progress(1.0*i/number_of_emails)
    return generated_file_names


def _generate_2600_file(model, number_of_sentences=DEFAULT_NUMBER_OF_SENTENCES_2600):
    content = []
    for _ in range(number_of_sentences):
        content.append(model.make_sentence())
        # The space is repeated to make paragraphs longer.
        content.append(random.choice([' ', ' ', '\n\n']))
    return ''.join(content)


def generate_2600(file_count,
                  output_dir,
                  model_path=DEFAULT_2600_MODEL_PATH,
                  on_progress=None):
    logger.debug('Loading 2600 model')
    model = _load_model(model_path)
    logger.debug('Generating {:,} files'.format(file_count))
    generated_file_names = []
    for i in range(1, file_count + 1):
        with tempfile.NamedTemporaryFile(mode='w+', encoding='utf-8', prefix='2600-', suffix='.txt', dir=output_dir, delete=False) as output_file:
            txt = _generate_2600_file(model)
            output_file.write(txt)
            generated_file_names.append(output_file.name)
        if on_progress:
            on_progress(1.0*i/file_count)
    return generated_file_names


def have_models():
    """Check whether the models exist in the default location.

    Used to check whether download is needed."""
    for fn in (DEFAULT_CONTENT_MODEL_PATH, DEFAULT_SUBJECT_MODEL_PATH, DEFAULT_2600_MODEL_PATH):
        if not os.path.exists(fn):
            return False
    return True
