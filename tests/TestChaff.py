# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2025 Andrew Ziem
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

import mock
import os
from tempfile import mkdtemp
from shutil import rmtree

from tests import common
from bleachbit.Chaff import download_models, generate_emails, generate_2600, have_models, MODEL_BASENAMES, DEFAULT_MODELS_DIR
from bleachbit.FileUtilities import getsize


class ChaffTestCase(common.BleachbitTestCase):
    """Test case for module Chaff"""

    def test_Chaff(self):
        """Unit test for class Chaff"""
        tmp_dir = mkdtemp(prefix='bleachbit-chaff')
        models_dir = os.path.join(tmp_dir, 'model')
        os.mkdir(models_dir)
        # con=Clinton content
        con_path = os.path.join(models_dir, 'clinton_content_model.json.bz2')
        # sub=Clinton subject
        sub_path = os.path.join(models_dir, 'clinton_subject_model.json.bz2')
        # ts = 2600 Magazine
        ts_path = os.path.join(models_dir, '2600_model.json.bz2')

        for _i in ('download', 'already downloaded'):
            ret = download_models(models_dir=models_dir)
            self.assertIsInstance(ret, bool)
            self.assertTrue(ret)

        self.assertExists(con_path)
        self.assertExists(sub_path)
        self.assertExists(ts_path)

        generated_file_names = generate_emails(5, tmp_dir, models_dir)

        self.assertEqual(len(generated_file_names), 5)

        for fn in generated_file_names:
            self.assertExists(fn)
            self.assertGreater(getsize(fn), 100)
            with open(fn) as f:
                contents = f.read()
                self.assertIn('To: ', contents)
                self.assertIn('From: ', contents)
                self.assertIn('Sent: ', contents)
                self.assertIn('Subject: ', contents)
                self.assertNotIn('base64', contents)

        generated_file_names = generate_2600(5, tmp_dir, models_dir)

        rmtree(tmp_dir)

    @mock.patch('bleachbit.Network.download_url_to_fn')
    def test_download_models_fallback(self, mock_download):
        """Test the fallback mechanism in download_models()"""
        tmp_dir = mkdtemp(prefix='bleachbit-chaff')

        # Test when primary download mirror fails but secondary succeeds.
        def succeed_on_second(*args, **kwargs):
            url = args[0]
            if 'sourceforge' in url:
                return False
            if 'bleachbit.org' in url:
                return True
        mock_download.side_effect = succeed_on_second
        ret = download_models(models_dir=tmp_dir)
        self.assertTrue(ret)
        self.assertEqual(mock_download.call_count, 6)

        # Test when both primary and secondary download mirrors will fail.
        mock_download.reset_mock()
        mock_download.side_effect = None
        mock_download.return_value = False
        ret = download_models(models_dir=tmp_dir)
        self.assertFalse(ret)
        self.assertEqual(mock_download.call_count, 2)

        rmtree(tmp_dir)

    def test_have_models(self):
        """Test for function have_models()"""
        download_models()
        rc = have_models()
        self.assertTrue(rc)
        self.assertIsInstance(rc, bool)
        for basename in MODEL_BASENAMES:
            fn = os.path.join(DEFAULT_MODELS_DIR, basename)
            self.assertExists(fn)
            os.remove(fn)
        self.assertFalse(have_models())
