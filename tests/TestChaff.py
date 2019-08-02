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


"""
Test case for module Chaff
"""

from __future__ import absolute_import

import os
import unittest
from tempfile import mkdtemp
from shutil import rmtree

from tests import common
from bleachbit.Chaff import download_models, generate_emails, generate_2600, have_models
from bleachbit.FileUtilities import getsize


class ChaffTestCase(common.BleachbitTestCase):
    """Test case for module Chaff"""

    def test_Chaff(self):
        """Unit test for class Chaff"""
        tmp_dir = mkdtemp(prefix='bleachbit-chaff')
        # con=Clinton content
        con_path = os.path.join(tmp_dir, 'content.json.bz2')
        # sub=Clinton subject
        sub_path = os.path.join(tmp_dir, 'subject.json.bz2')
        ts_path = os.path.join(tmp_dir, 'ts.json.bz2')  # ts = 2600 Magazine

        for i in ('download', 'already downloaded'):
            ret = download_models(
                content_model_path=con_path, subject_model_path=sub_path,
                twentysixhundred_model_path=ts_path)
            self.assertIsInstance(ret, bool)
            self.assertTrue(ret)

        self.assertExists(con_path)
        self.assertExists(sub_path)
        self.assertExists(ts_path)

        generated_file_names = generate_emails(5, tmp_dir, con_path, sub_path)

        self.assertEqual(len(generated_file_names), 5)

        for fn in generated_file_names:
            self.assertExists(fn)
            self.assertGreater(getsize(fn), 100)

        generated_file_names = generate_2600(5, tmp_dir, ts_path)

        rmtree(tmp_dir)

    def test_have_models(self):
        rc = have_models()
        self.assertIsInstance(rc, bool)
