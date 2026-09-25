# vim: ts=4:sw=4:expandtab

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
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
Test case for module Chaff
"""

from unittest import mock
import errno
import hashlib
import os
from tempfile import mkdtemp
from shutil import rmtree
from urllib.parse import urlparse

from tests import common
from bleachbit.Chaff import download_models, generate_emails, generate_2600, have_models, MODEL_BASENAMES, MODEL_SHA512, DEFAULT_MODELS_DIR
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

        for _ in ('download', 'already downloaded'):
            ret = download_models(models_dir=models_dir)
            self.assertIsInstance(ret, bool)
            if not ret:
                rmtree(tmp_dir, ignore_errors=True)
                self.skipTest(
                    'download_models() failed, likely a transient network issue')

        self.assertExists(con_path)
        self.assertExists(sub_path)
        self.assertExists(ts_path)

        generated_file_names = generate_emails(5, tmp_dir, models_dir)

        self.assertEqual(len(generated_file_names), 5)

        for fn in generated_file_names:
            self.assertExists(fn)
            self.assertGreater(getsize(fn), 100)
            # Chaff wrote this file in the platform default encoding.
            # pylint: disable-next=unspecified-encoding
            with open(fn) as f:
                contents = f.read()
                self.assertIn('To: ', contents)
                self.assertIn('From: ', contents)
                self.assertIn('Sent: ', contents)
                self.assertIn('Subject: ', contents)
                self.assertNotIn('base64', contents)

        generate_2600(5, tmp_dir, models_dir)

        rmtree(tmp_dir)

    @mock.patch('bleachbit.Network.download_url_to_fn')
    def test_download_models_fallback(self, mock_download):
        """Test the fallback mechanism in download_models()"""
        tmp_dir = mkdtemp(prefix='bleachbit-chaff')

        # Test when primary download mirror fails but secondary succeeds.
        def succeed_on_second(*args, **_kwargs):
            host = urlparse(args[0]).hostname or ''
            if host == 'sourceforge.net':
                return False
            if host == 'download.bleachbit.org':
                return True
            return None
        mock_download.side_effect = succeed_on_second
        ret = download_models(models_dir=tmp_dir)
        self.assertTrue(
            ret, "download_models() return False, meaning a download error occurred")
        self.assertEqual(mock_download.call_count, 6)

        # Test when both primary and secondary download mirrors will fail.
        mock_download.reset_mock()
        mock_download.side_effect = None
        mock_download.return_value = False
        ret = download_models(models_dir=tmp_dir)
        self.assertFalse(
            ret, "download_models() should return False when any download fails")
        self.assertEqual(mock_download.call_count, 2)

        rmtree(tmp_dir)

    @mock.patch('bleachbit.Network.download_url_to_fn')
    def test_download_models_verifies_hash(self, mock_download):
        """download_models() must pass the expected SHA-512 for each model"""
        tmp_dir = mkdtemp(prefix='bleachbit-chaff')
        mock_download.return_value = True
        download_models(models_dir=tmp_dir)
        hashes_passed = {call.kwargs.get('expected_sha512')
                         for call in mock_download.call_args_list}
        self.assertEqual(hashes_passed, set(MODEL_SHA512.values()))

        rmtree(tmp_dir)

    def test_make_sentence_none(self):
        """Test that make_sentence() returning None does not cause TypeError"""
        from bleachbit.Chaff import _get_random_content, _generate_2600_file, _generate_email

        model = mock.MagicMock()
        model.make_sentence.return_value = None
        model.make_short_sentence.return_value = None

        result = _get_random_content(model, number_of_sentences=2)
        self.assertIsNotNone(result)

        result = _generate_2600_file(model, number_of_sentences=2)
        self.assertIsInstance(result, str)

        subject_model = mock.MagicMock()
        subject_model.make_short_sentence.return_value = None
        msg = _generate_email(subject_model, model, number_of_sentences=2)
        self.assertEqual(msg['Subject'], '')

    def test_random_datetime_time_of_day(self):
        """The Sent time must vary instead of always being midnight"""
        from bleachbit.Chaff import _get_random_datetime

        times = {_get_random_datetime().split(', ')[-1].split(' ', 1)[1]
                 for _i in range(100)}
        self.assertGreater(len(times), 1)

    @mock.patch('bleachbit.Chaff._load_model')
    def test_generate_2600_write_error(self, _mock_load_model):
        """The caller's list must name every file, including one whose write failed"""
        output_dir = self.mkdtemp()
        generated_file_names = []
        enospc = OSError(errno.ENOSPC, 'No space left on device')
        with mock.patch('bleachbit.Chaff._generate_2600_file',
                        side_effect=['a', 'b', enospc]):
            with self.assertRaises(OSError):
                generate_2600(5, output_dir,
                              generated_file_names=generated_file_names)
        self.assertEqual(len(generated_file_names), 3)
        self.assertEqual(sorted(generated_file_names),
                         sorted(os.path.join(output_dir, fn) for fn in os.listdir(output_dir)))

    @mock.patch('bleachbit.Network.download_url_to_fn')
    def test_have_models(self, mock_download):
        """Test for function have_models()"""
        def fake_download(_url, fn, **_kwargs):
            with open(fn, 'wb') as f:
                f.write(b'')
            return True
        mock_download.side_effect = fake_download
        empty_sha512 = dict.fromkeys(
            MODEL_BASENAMES, hashlib.sha512(b'').hexdigest())
        with mock.patch.dict(MODEL_SHA512, empty_sha512):
            download_models()
            rc = have_models()
            self.assertTrue(
                rc, "have_models() should return True when models are present")
            self.assertIsInstance(rc, bool)
            corrupt_fn = os.path.join(DEFAULT_MODELS_DIR, MODEL_BASENAMES[0])
            self.write_file(corrupt_fn, b'corrupt')
            self.assertFalse(
                have_models(), "have_models() should return False when a model is corrupt")
            mock_download.reset_mock()
            download_models()
            mock_download.assert_called_once()
            self.assertEqual(mock_download.call_args.args[1], corrupt_fn)
            self.assertTrue(have_models())
        for basename in MODEL_BASENAMES:
            fn = os.path.join(DEFAULT_MODELS_DIR, basename)
            self.assertExists(fn)
            os.remove(fn)
        self.assertFalse(
            have_models(), "have_models() should return False when any model is missing")
