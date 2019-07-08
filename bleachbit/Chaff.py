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

import markovify

logger = logging.getLogger(__name__)

RECIPIENTS = ['0emillscd@state.gov', '1ilotylc@state.gov', 'abdinh@state.gov', 'abedin@state.gov', 'abedinh@state.gov', 'abendinh@state.gov', 'adedinh@state.gov', 'adlerce@state.gov', 'aliilscd@state.gov', 'baerdb@state.gov', 'baldersonkm@state.gov', 'balderstonkm@state.gov', 'bam@mikuiski.senate.gov', 'bam@mikulski.senate.gov', 'bealeca@state.gov', 'bedinh@state.gov', 'benjamin_moncrief@lemieux.senate.gov', 'blaker2@state.gov', 'brimmere@state.gov', 'brod17@clintonemail.com', 'burnswj@state.gov', 'butzgych2@state.gov', 'campbelikm@state.gov', 'carsonj@state.gov', 'cholletdh@state.gov', 'cindy.buhl@mail.house.gov', 'colemancl@state.gov', 'crowleypj@state.gov', 'danielil@state.gov', 'daniew@state.gov', 'david_garten@lautenberg.senate.gov', 'dewanll@state.gov', 'dilotylc@state.gov', 'eabedinh@state.gov', 'emillscd@state.gov', 'esullivanjj@state.gov', 'feltmanjd@state.gov', 'filotylc@state.gov', 'fuchsmh@state.gov', 'gll@state.gov', 'goldbergps@state.gov', 'goldenjr@state.gov', 'gonzalezjs@state.gov', 'gordonph@state.gov', 'h@state.gov', 'hanieymr@state.gov', 'hanleymr@state.gov', 'hanleyrnr@state.gov', 'harileymr@state.gov', 'hdr22@clintonemai1.com', 'hilicr@state.gov', 'hillcr@state.gov', 'holbrookerc@state.gov', 'hormatsrd@state.gov', 'hr15@att.blackberry.net', 'hr15@mycingular.blackberry.net', 'hrod17@clintonemail.com', 'huma@clintonemail.com', 'hyded@state.gov', 'ian1evqr@state.gov', 'ieltmanjd@state.gov', 'iewjj@state.gov', 'iilotylc@state.gov', 'imillscd@state.gov', 'info@mailva.evite.com', 'inh@state.gov', 'iviillscd@state.gov', 'jilotylc@state.gov', 'jj@state.gov', 'jonespw2@state.gov', 'kellyc@state.gov', 'klevorickcb@state.gov', 'kohhh@state.gov', 'kohliff@state.gov', 'laszczychj@state.gov', 'lc@state.gov', 'lewij@state.gov', 'lewjj@state.gov', 'lewn@state.gov', 'lilotylc@state.gov', 'macmanusje@state.gov', 'marshalicp@state.gov', 'marshallcp@state.gov', 'mchaleja@state.gov', 'mhcaleja@state.gov', 'millscd@state.aov', 'millscd@state.gov', 'millscd@tate.gov', 'mr@state.gov', 'muscantinel@state.gov', 'muscatinel@state.gov', 'nidestr@state.gov', 'njj@state.gov', 'nulandvi@state.gov', 'ogordonph@state.gov', 'oterom2@state.gov', 'posnermh@state.gov', 'postmaster@state.gov', 'r@state.gov', 'reines@state.gov', 'reinesp@state.gov', 'reinespi@state.gov', 'ricese@state.gov', 'rnillscd@state.gov', 'rodriguezme@state.gov', 'rooneym@state.gov', 's_specialassistants@state.gov', 'schwerindb@state.gov', 'shannonta@state.gov', 'shapiroa@state.gov', 'shermanwr@state.gov', 'slaughtera@state.gov', 'smithje@state.gov', 'steinbertjb@state.gov', 'sterntd@state.gov', 'stillivaral@state.gov', 'sullivanjj@state.gov', 'tanleyrnr@state.gov', 'tauschere0@state.gov', 'tauschereo@state.gov', 'tillemannts@state.gov', 'toivnf@state.gov', 'tommy_ross@reid.senate.gov', 'u@state.gov', 'ullivanjj@state.gov', 'vaimorou@state.gov', 'valenzuelaaa@state.gov', 'valmdrou@state.gov', 'valmmorolj@state.gov', 'valmorolj@state.gov', 'vermarr@state.gov', 'verveerms@state.gov', 'walmorou@state.gov', 'werveerms@state.gov', 'woodardew@state.gov', 'yeryeerms@state.gov']
DEFAULT_SUBJECT_LENGTH = 64
DEFAULT_NUMBER_OF_SENTENCES = 5


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
    date = datetime.strptime('{} {}'.format(random.randint(1, 365), random.randint(min_year, max_year)), '%j %Y')
    return date.strftime('%A, %B %d, %Y %I:%M %p')  # Saturday, September 15, 2012 2:20 PM


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
    message = _get_random_content(content_model, number_of_sentences=number_of_sentences)

    message['Subject'] = subject_model.make_short_sentence(subject_length)
    message['To'] = _get_random_recipient()
    message['From'] = _get_random_recipient()
    message['Sent'] = _get_random_datetime()

    return message

def generate_emails(number_of_emails, content_model_path, subject_model_path, email_output_dir,
                     number_of_sentences=DEFAULT_NUMBER_OF_SENTENCES, *kwargs):
    logger.debug('Loading two email models')
    subject_model = load_subject_model(subject_model_path)
    content_model = load_content_model(content_model_path)
    logger.debug('Generating {:,} emails'.format(number_of_emails))
    for _ in range(number_of_emails):
        with tempfile.NamedTemporaryFile(prefix='outlook-', suffix='.eml', dir=email_output_dir, delete=False) as email_output_file:
            email_generator = email.generator.Generator(email_output_file)
            msg = _generate_email(subject_model, content_model, number_of_sentences=number_of_sentences)
            email_generator.write(msg.as_string())

