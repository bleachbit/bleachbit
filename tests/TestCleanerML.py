# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2008-2026 Andrew Ziem.
#
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

"""
Test cases for module CleanerML
"""

# standard imports
import json
import os
import shutil
import sys
from unittest import mock

# first party imports
import bleachbit
from tests import common
from bleachbit import Cleaner, Command
from bleachbit.CleanerML import (
    CleanerML,
    boolstr_to_bool,
    create_pot,
    default_vars,
    list_cleanerml_files,
    load_cleaners,
    pot_fragment)
from bleachbit.General import os_match
from bleachbit.Process import ProcessInfo, process_cache


class CleanerMLTestCase(common.BleachbitTestCase):
    """Test cases for CleanerML"""

    def run_all(self, xmlcleaner, really_delete):
        """Helper function to execute all options in a cleaner"""
        for (option_id, __name) in xmlcleaner.cleaner.get_options():
            for cmd in xmlcleaner.cleaner.get_commands(option_id):
                for result in cmd.execute(really_delete):
                    common.validate_result(self, result, really_delete)

    def _get_xmlcleaner(self):
        """Helper for CleanerML*()"""
        xmlcleaner = CleanerML("doc/example_cleaner.xml")
        self.assertIsInstance(xmlcleaner, CleanerML)
        self.assertIsInstance(xmlcleaner.cleaner, Cleaner.Cleaner)
        return xmlcleaner

    def test_CleanerML(self):
        """Unit test for class CleanerML"""
        xmlcleaner = self._get_xmlcleaner()
        # preview
        self.run_all(xmlcleaner, False)

    @common.skipUnlessDestructive
    def test_CleanerML_destructive(self):
        """Unit test the destructive parts of class CleanerML"""
        xmlcleaner = self._get_xmlcleaner()
        # really delete
        self.run_all(xmlcleaner, True)

    def _bundled_cleaner(self, cleaner_id, platform=sys.platform):
        """Load a bundled cleaner as if running on platform"""
        with mock.patch('bleachbit.CleanerML.general_os_match',
                        lambda os_str, _platform: os_match(os_str, platform)):
            return CleanerML(f'cleaners/{cleaner_id}.xml').get_cleaner()

    def _bundled_option_paths(self, cleaner_id, option_id, platform=sys.platform):
        """Return the paths an option of a bundled cleaner would touch"""
        cleaner = self._bundled_cleaner(cleaner_id, platform)
        # glob values end in a separator, so a path can hold '//'
        return [os.path.normpath(cmd.path)
                for cmd in cleaner.get_commands(option_id)]

    def _bundled_cleaner_detects(self, cleaner_id, platform, exename):
        """Return whether a bundled cleaner treats exename as its app running"""
        cleaner = self._bundled_cleaner(cleaner_id, platform)
        procs = (ProcessInfo(1234, exename, True),)
        with mock.patch.object(process_cache, 'get', return_value=procs), \
                mock.patch('bleachbit.Process.IS_WINDOWS', platform == 'win32'):
            return cleaner.is_process_running()

    def test_boolstr_to_bool(self):
        """Unit test for boolstr_to_bool()"""
        tests = [('True', True),
                 ('False', False)]

        for (arg, output) in tests:
            self.assertEqual(boolstr_to_bool(arg), output)
            self.assertEqual(boolstr_to_bool(arg.lower()), output)
            self.assertEqual(boolstr_to_bool(arg.upper()), output)

    def test_create_pot(self):
        """Unit test for create_pot()"""
        os.chdir('po')
        try:
            create_pot()
        finally:
            os.chdir('..')

    def test_default_vars_windows_system(self):
        """Unit test WindowsSystem in default_vars()"""
        env = {
            'WinDir': r'C:\Windows',
            'ProgramFiles': r'C:\Program Files (x86)',
            'ProgramW6432': r'C:\Program Files',
        }
        with mock.patch('bleachbit.CleanerML.IS_WINDOWS', True), \
                mock.patch.dict(os.environ, env, clear=True), \
                mock.patch('bleachbit.Windows.ARCH_BITS', 32):
            variables = default_vars()
        self.assertEqual(
            [r'C:\Windows\Sysnative', r'C:\Windows\SysWOW64'],
            variables['WindowsSystem'])

    def test_list_cleanerml_files(self):
        """Unit test for list_cleanerml_files()"""
        for pathname in list_cleanerml_files():
            self.assertExists(pathname)

    @common.skipIfWindows
    def test_list_cleanerml_files_vanished(self):
        """list_cleanerml_files() skips a cleaner deleted after listdir()

        The world-writable check is POSIX only, so this race does not exist
        on Windows.
        """
        dirname = self.mkdtemp(prefix='bleachbit-cleanerml-vanished')
        real_fn = os.path.join(dirname, 'real.xml')
        self.write_file(real_fn, contents=b'<cleaner id="test"/>')
        os.chmod(real_fn, 0o600)
        ghost_fn = os.path.join(dirname, 'ghost.xml')
        with mock.patch('bleachbit.CleanerML.listdir',
                        return_value=iter([ghost_fn, real_fn])):
            self.assertEqual(list(list_cleanerml_files()), [real_fn])

    def test_load_cleaners(self):
        """Unit test for load_cleaners()"""
        # normal
        list(load_cleaners())

        # should catch exception with invalid XML
        pcd = bleachbit.personal_cleaners_dir
        bleachbit.personal_cleaners_dir = self.mkdtemp(
            prefix='bleachbit-cleanerml-load')
        self.write_file(os.path.join(bleachbit.personal_cleaners_dir, 'invalid.xml'),
                        contents=b'<xml><broken>')
        list(load_cleaners())
        shutil.rmtree(bleachbit.personal_cleaners_dir)
        bleachbit.personal_cleaners_dir = pcd

    def test_load_cleaners_invalid_utf8(self):
        """Unit test for load_cleaners() with invalid UTF-8 encoding"""
        pcd = bleachbit.personal_cleaners_dir
        bleachbit.personal_cleaners_dir = self.mkdtemp(
            prefix='bleachbit-cleanerml-utf8')
        self.write_file(os.path.join(bleachbit.personal_cleaners_dir, 'broken_encoding.xml'),
                        contents=b'<cleaner id="poison">\n\xff\xfe\xfd Broken\n')
        list(load_cleaners())
        shutil.rmtree(bleachbit.personal_cleaners_dir)
        bleachbit.personal_cleaners_dir = pcd

    def test_untrusted_process_action(self):
        """A process action is ignored for an untrusted cleaner"""
        xml_str = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<cleaner id="test_untrusted">\n'
            '  <label>Test</label>\n'
            '  <description>Test</description>\n'
            '  <option id="opt">\n'
            '    <label>Opt</label>\n'
            '    <description>Opt</description>\n'
            '    <action command="delete" search="file" path="test-does-not-exist"/>\n'
            '    <action command="process" cmd="calc.exe"/>\n'
            '  </option>\n'
            '</cleaner>\n')
        fn = os.path.join(self.mkdtemp(prefix='bleachbit-cleanerml-trust'),
                          'planted.xml')
        self.write_file(fn, text=xml_str)

        def action_classes(cleaner):
            return [a.__class__.__name__ for (_option_id, a) in cleaner.actions]

        self.assertIn('Process', action_classes(
            CleanerML(fn, trusted=True).cleaner))

        # The delete action stays; only the process action is dropped
        untrusted = action_classes(CleanerML(fn, trusted=False).cleaner)
        self.assertNotIn('Process', untrusted)
        self.assertIn('Delete', untrusted)

    def test_untrusted_winreg_action_allowed(self):
        """A winreg action is kept even for an untrusted cleaner"""
        xml_str = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<cleaner id="test_untrusted_winreg">\n'
            '  <label>Test</label>\n'
            '  <description>Test</description>\n'
            '  <option id="opt">\n'
            '    <label>Opt</label>\n'
            '    <description>Opt</description>\n'
            '    <action command="delete" search="file" path="test-does-not-exist"/>\n'
            '    <action command="winreg" path="HKCU\\Software\\BleachBitTest"/>\n'
            '  </option>\n'
            '</cleaner>\n')
        fn = os.path.join(self.mkdtemp(prefix='bleachbit-cleanerml-trust'),
                          'planted_winreg.xml')
        self.write_file(fn, text=xml_str)

        def action_classes(cleaner):
            return [a.__class__.__name__ for (_option_id, a) in cleaner.actions]

        for trusted in (True, False):
            actions = action_classes(CleanerML(fn, trusted=trusted).cleaner)
            self.assertIn('Winreg', actions)
            self.assertIn('Delete', actions)

    def test_untrusted_actions_warn_once_per_file(self):
        """Ignored actions are summarized in one warning, not one per action"""
        actions = '\n'.join(
            f'    <action command="process" cmd="calc{i}.exe"/>'
            for i in range(10))
        xml_str = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<cleaner id="test_untrusted_many">\n'
            '  <label>Test</label>\n'
            '  <description>Test</description>\n'
            '  <option id="opt">\n'
            '    <label>Opt</label>\n'
            '    <description>Opt</description>\n'
            f'{actions}\n'
            '  </option>\n'
            '</cleaner>\n')
        fn = os.path.join(self.mkdtemp(prefix='bleachbit-cleanerml-trust-log'),
                          'planted_many.xml')
        self.write_file(fn, text=xml_str)

        with self.assertLogs('bleachbit.CleanerML', level='WARNING') as cm:
            CleanerML(fn, trusted=False)
        self.assertEqual(len(cm.output), 1)
        self.assertIn("'process'", cm.output[0])

    def test_is_trusted_cleaner(self):
        """Files shipped next to the application are trusted"""
        from bleachbit.CleanerML import is_trusted_cleaner
        system_dir = bleachbit.system_cleaners_dir
        self.assertTrue(is_trusted_cleaner(
            os.path.join(system_dir, 'example.xml')))
        self.assertFalse(is_trusted_cleaner(
            os.path.join(bleachbit.personal_cleaners_dir, 'example.xml')))

    def test_is_trusted_cleaner_portable(self):
        """In portable mode the personal cleaners dir is the local one"""
        from bleachbit.CleanerML import is_trusted_cleaner
        app_dir = self.mkdtemp(prefix='bleachbit-portable')
        cleaners_dir = os.path.join(app_dir, 'cleaners')
        with mock.patch.multiple(
                'bleachbit',
                local_cleaners_dir=cleaners_dir,
                personal_cleaners_dir=cleaners_dir,
                system_cleaners_dir=os.path.join(app_dir, 'share', 'cleaners')):
            self.assertTrue(is_trusted_cleaner(
                os.path.join(cleaners_dir, 'winapp2.ini')))
            self.assertFalse(is_trusted_cleaner(
                os.path.join(app_dir, 'elsewhere', 'winapp2.ini')))

    def test_rejects_dtd(self):
        """A CleanerML file with a DTD is rejected (entity-expansion defense)"""
        xml_str = (
            '<?xml version="1.0"?>\n'
            '<!DOCTYPE cleaner [ <!ENTITY x "y"> ]>\n'
            '<cleaner id="dtd_test">\n'
            '  <label>Test</label>\n'
            '  <description>Test</description>\n'
            '</cleaner>\n')
        fn = os.path.join(self.mkdtemp(prefix='bleachbit-cleanerml-dtd'),
                          'dtd.xml')
        self.write_file(fn, text=xml_str)
        xmlcleaner = CleanerML(fn)
        self.assertFalse(xmlcleaner.cleaner.is_usable())

    def test_nvalid_utf8(self):
        """Test CleanerML() with invalid UTF-8 encoding

        It should fail gracefully.
        """
        fn = os.path.join(self.mkdtemp(prefix='bleachbit-cleanerml-utf8'),
                          'broken.xml')
        self.write_file(fn, contents=b'<cleaner id="poison">\n\xff\xfe\xfd\n')
        xmlcleaner = CleanerML(fn)
        self.assertIsInstance(xmlcleaner, CleanerML)
        self.assertFalse(xmlcleaner.cleaner.is_usable())

    def test_utf8_non_ascii(self):
        """Test CleanerML() with UTF-8 non-ASCII text

        It should load successfully.
        """
        xml_str = """<?xml version="1.0" encoding="UTF-8"?>
<cleaner id="test_utf8">
    <label>Test</label>
    <!-- 中文注释 -->
    <option id="opt">
        <label>测试标签</label>
        <description>测试描述</description>
        <action search="file" command="delete" path="C:\\中文路径\\file.txt"/>
    </option>
</cleaner>
"""
        fn = os.path.join(self.mkdtemp(prefix='bleachbit-cleanerml-utf8'),
                          'utf8.xml')
        self.write_file(fn, contents=xml_str.encode('utf-8'))
        xmlcleaner = CleanerML(fn)
        self.assertIsInstance(xmlcleaner, CleanerML)
        self.assertTrue(xmlcleaner.cleaner.is_usable())
        self.assertEqual('测试标签', xmlcleaner.cleaner.options['opt'][0])
        self.assertEqual('测试描述',
                         xmlcleaner.cleaner.options['opt'][1])
        commands = list(xmlcleaner.cleaner.get_commands('opt'))
        self.assertEqual(0, len(commands))

    def test_os_match(self):
        """Unit test for os_match"""
        xmlcleaner = CleanerML("doc/example_cleaner.xml")

        # blank always matches
        self.assertTrue(xmlcleaner.os_match(""))

        # as Linux
        self.assertFalse(xmlcleaner.os_match('windows', 'linux'))
        self.assertTrue(xmlcleaner.os_match('linux', 'linux'))
        self.assertTrue(xmlcleaner.os_match('unix', 'linux'))

        # as Windows
        self.assertFalse(xmlcleaner.os_match('linux', 'win32'))
        self.assertFalse(xmlcleaner.os_match('unix', 'win32'))
        self.assertTrue(xmlcleaner.os_match('windows', 'win32'))

        # as macOS (canonical name)
        self.assertTrue(xmlcleaner.os_match('macos', 'darwin'))
        self.assertTrue(xmlcleaner.os_match('bsd', 'darwin'))
        self.assertTrue(xmlcleaner.os_match('unix', 'darwin'))
        self.assertFalse(xmlcleaner.os_match('linux', 'darwin'))
        self.assertFalse(xmlcleaner.os_match('windows', 'darwin'))

        # as FreeBSD
        self.assertTrue(xmlcleaner.os_match('unix', 'freebsd'))
        self.assertTrue(xmlcleaner.os_match('bsd', 'freebsd'))
        self.assertTrue(xmlcleaner.os_match('freebsd', 'freebsd'))
        self.assertFalse(xmlcleaner.os_match('linux', 'freebsd'))
        self.assertFalse(xmlcleaner.os_match('windows', 'freebsd'))

        # "darwin" is accepted as a deprecated alias for "macos"
        with self.assertLogs('bleachbit.General', level='WARNING'):
            self.assertTrue(xmlcleaner.os_match('darwin', 'darwin'))

        # comma-separated list with negation (positive tokens OR'd, negative tokens excluded)
        cases = [
            ('unix,!macos', 'linux', True),
            ('unix,!macos', 'freebsd', True),
            ('unix,!macos', 'darwin', False),
            ('unix,!macos', 'win32', False),
            ('!macos', 'win32', True),
            ('linux , unix', 'linux', True),
            ('!macos', 'darwin', False),
            ('linux,freebsd', 'linux', True),
            ('linux,freebsd', 'freebsd', True),
            ('linux,freebsd', 'darwin', False),
            ('linux,freebsd', 'win32', False),
            ('!macos,!windows', 'linux', True),
            ('!macos,!windows', 'darwin', False),
            ('!macos,!windows', 'win32', False),
        ]
        for os_attr, platform, expected in cases:
            with self.subTest(os=os_attr, platform=platform):
                self.assertEqual(expected,
                                 xmlcleaner.os_match(os_attr, platform))

        # as unknown operating system
        with self.assertRaisesRegex(RuntimeError, 'Unknown operating system: hal9000'):
            xmlcleaner.os_match('linux', 'hal9000')
        with self.assertRaisesRegex(RuntimeError, 'Unknown operating system: hal9000'):
            xmlcleaner.os_match('!macos', 'hal9000')

    def test_option_os_filter(self):
        """Unit test for <option os="..."> filtering

        An option with an os attribute that does not match the current
        platform should not be registered on the cleaner.
        """
        xml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
<cleaner id="test_option_os">
    <label>Test</label>
    <option id="always">
        <label>Always</label>
        <description>Delete the files</description>
        <action search="file" command="delete" path="{self.tempdir}/always.log"/>
    </option>
    <option id="windows_only" os="windows">
        <label>Windows only</label>
        <description>Delete the files</description>
        <action search="file" command="delete" path="{self.tempdir}/windows.log"/>
    </option>
    <option id="linux_only" os="linux">
        <label>Linux only</label>
        <description>Delete the files</description>
        <action search="file" command="delete" path="{self.tempdir}/linux.log"/>
    </option>
    <option id="mac_only" os="macos">
        <label>macOS only</label>
        <description>Delete the files</description>
        <action search="file" command="delete" path="{self.tempdir}/mac.log"/>
    </option>
</cleaner>
"""
        cml_path = os.path.join(self.tempdir, 'test_option_os.xml')
        self.write_file(cml_path, xml_str.encode(sys.getdefaultencoding()))

        xmlc = CleanerML(cml_path)
        # The unfiltered option is always present.
        self.assertIn('always', xmlc.cleaner.options)
        # The remaining options are conditionally available.
        if bleachbit.IS_LINUX:
            self.assertNotIn('mac_only', xmlc.cleaner.options)
            self.assertNotIn('windows_only', xmlc.cleaner.options)
            self.assertIn('linux_only', xmlc.cleaner.options)
        elif bleachbit.IS_WINDOWS:
            self.assertIn('windows_only', xmlc.cleaner.options)
            self.assertNotIn('linux_only', xmlc.cleaner.options)
            self.assertNotIn('mac_only', xmlc.cleaner.options)
        elif bleachbit.IS_MAC:
            self.assertNotIn('windows_only', xmlc.cleaner.options)
            self.assertNotIn('linux_only', xmlc.cleaner.options)
            self.assertIn('mac_only', xmlc.cleaner.options)

    def test_pot_fragment(self):
        """Unit test for pot_fragment()"""
        self.assertIsString(pot_fragment("Foo", 'bar.xml'))

    def test_var(self):
        """Test the <var> element"""
        xml_str = r"""
<cleaner id="testvar">
    <label>cleaner label</label>
    <description>cleaner description</description>
    <var name="basepath">
        <value>%%LocalAppData%%\FooDoesNotExist</value>
        <value>~/.config/FooDoesNotExist</value>
        <value>{tempdir}/a</value>
        <value>{tempdir}/b</value>
    </var>
    <option id="option1">
        <label>option1 label</label>
        <description>option1 description</description>
        <action search="file" command="delete" path="$$basepath$$/test.log" />
    </option>
</cleaner>
""".format(**{'tempdir': self.tempdir})
        # write XML cleaner
        cml_path = os.path.join(self.tempdir, 'test.xml')
        self.write_file(cml_path, xml_str.encode(sys.getdefaultencoding()))

        # create two canaries
        test_log_path_a = os.path.join(self.tempdir, 'a', 'test.log')
        test_log_path_b = os.path.join(self.tempdir, 'b', 'test.log')
        common.touch_file(test_log_path_a)
        common.touch_file(test_log_path_b)
        self.assertExists(test_log_path_a)
        self.assertExists(test_log_path_b)

        # parse XML to XML cleaner instance
        xmlc = CleanerML(cml_path)
        self.assertIsInstance(xmlc, CleanerML)
        self.assertIsInstance(xmlc.cleaner, Cleaner.Cleaner)
        self.assertTrue(xmlc.cleaner.is_usable())

        # run preview
        self.run_all(xmlc, False)
        self.assertExists(test_log_path_a)
        self.assertExists(test_log_path_b)

        # really delete
        self.run_all(xmlc, True)
        self.assertNotExists(test_log_path_a)
        self.assertNotExists(test_log_path_b)

    @common.skipIfWindows
    def test_safari_cookies_skip_other_apps(self):
        """Safari cookies leave other apps' jars in ~/Library/HTTPStorages"""
        home = self.mkdtemp(prefix='bleachbit-safari-home')
        storages = os.path.join(home, 'Library', 'HTTPStorages')
        safari_jar = os.path.join(storages, 'com.apple.Safari.binarycookies')
        other_jar = os.path.join(storages, 'us.zoom.xos.binarycookies')
        common.touch_file(safari_jar)
        common.touch_file(other_jar)
        with common.set_temporary_env('HOME', home):
            paths = self._bundled_option_paths('safari', 'cookies', 'darwin')
        self.assertIn(safari_jar, paths)
        self.assertNotIn(other_jar, paths)

    @common.skipIfWindows
    def test_vivaldi_cookies_network(self):
        """Vivaldi cookies cover the Network/ subdirectory used on Windows"""
        config = self.mkdtemp(prefix='bleachbit-vivaldi-config')
        cookies = os.path.join(
            config, 'vivaldi', 'Default', 'Network', 'Cookies')
        common.touch_file(cookies)
        with common.set_temporary_env('XDG_CONFIG_HOME', config):
            self.assertIn(cookies, self._bundled_option_paths(
                'vivaldi', 'cookies', 'linux'))
            self.assertIn(cookies, self._bundled_option_paths(
                'vivaldi', 'vacuum', 'linux'))

    @common.skipIfWindows
    def test_vivaldi_cache_disk_cache(self):
        """Vivaldi cache covers the HTTP disk cache"""
        cache_home = self.mkdtemp(prefix='bleachbit-vivaldi-cache')
        entry = os.path.join(cache_home, 'vivaldi', 'Default', 'Cache',
                             'Cache_Data', 'f_000001')
        common.touch_file(entry)
        with common.set_temporary_env('XDG_CACHE_HOME', cache_home):
            self.assertIn(entry, self._bundled_option_paths(
                'vivaldi', 'cache', 'linux'))

    @common.skipIfWindows
    def test_site_data_keeps_extension_state(self):
        """Chromium-based site data leaves the extension StateStore alone"""
        config = self.mkdtemp(prefix='bleachbit-extension-state')
        profiles = {
            'brave': 'BraveSoftware/Brave-Browser/Default',
            'chromium': 'chromium/Default',
            'microsoft_edge': 'microsoft-edge/Default',
            'opera': 'opera',
        }
        with common.set_temporary_env('XDG_CONFIG_HOME', config):
            for cleaner_id, profile in profiles.items():
                with self.subTest(cleaner_id=cleaner_id):
                    local_storage = os.path.join(
                        config, profile, 'Local Storage', '000003.log')
                    state = os.path.join(
                        config, profile, 'Extension State', '000003.log')
                    common.touch_file(local_storage)
                    common.touch_file(state)
                    paths = self._bundled_option_paths(
                        cleaner_id, 'site_data', 'linux')
                    self.assertIn(local_storage, paths)
                    self.assertNotIn(state, paths)

    @common.skipIfWindows
    def test_chrome_sync_keeps_profile_list(self):
        """Signing out of Chrome keeps every profile in Local State"""
        config = self.mkdtemp(prefix='bleachbit-chrome-sync')
        local_state = os.path.join(config, 'google-chrome', 'Local State')
        os.makedirs(os.path.dirname(local_state))
        info_cache = {
            'Default': {'name': 'Personal', 'user_name': 'me@example.com',
                        'is_consented_primary_account': True},
            'Profile 1': {'name': 'Work'},
        }
        self.write_file(local_state, text=json.dumps(
            {'profile': {'info_cache': info_cache, 'last_used': 'Profile 1'}}))
        with common.set_temporary_env('XDG_CONFIG_HOME', config):
            cleaner = self._bundled_cleaner('google_chrome', 'linux')
            for cmd in cleaner.get_commands('sync'):
                if cmd.path == local_state:
                    list(cmd.execute(True))
        with open(local_state, encoding='utf-8') as f:
            profile = json.load(f)['profile']
        self.assertEqual(['Default', 'Profile 1'],
                         sorted(profile['info_cache']))
        self.assertEqual('Profile 1', profile['last_used'])
        self.assertEqual({'name': 'Personal'},
                         profile['info_cache']['Default'])

    @common.skipIfWindows
    def test_chromium_network_hsts_nel(self):
        """HSTS and NEL are cleaned from the Network/ subdirectory"""
        config = self.mkdtemp(prefix='bleachbit-network-hsts')
        profiles = {
            'brave': 'BraveSoftware/Brave-Browser/Default',
            'chromium': 'chromium/Default',
            'google_chrome': 'google-chrome/Default',
            'microsoft_edge': 'microsoft-edge/Default',
            'opera': 'opera',
            'vivaldi': 'vivaldi/Default',
        }
        with common.set_temporary_env('XDG_CONFIG_HOME', config):
            for cleaner_id, profile in profiles.items():
                with self.subTest(cleaner_id=cleaner_id):
                    network = os.path.join(config, profile, 'Network')
                    hsts = os.path.join(network, 'TransportSecurity')
                    nel = os.path.join(network, 'Reporting and NEL')
                    common.touch_file(hsts)
                    common.touch_file(nel)
                    self.assertIn(hsts, self._bundled_option_paths(
                        cleaner_id, 'cookies', 'linux'))
                    if cleaner_id != 'vivaldi':
                        self.assertIn(nel, self._bundled_option_paths(
                            cleaner_id, 'history', 'linux'))

    def test_ie_history_keeps_feature_control(self):
        """IE history leaves the Internet Feature Control settings alone"""
        cleaner = self._bundled_cleaner('internet_explorer', 'win32')
        with mock.patch('bleachbit.Action.IS_WINDOWS', True):
            keys = [cmd.keyname for cmd in cleaner.get_commands('history')
                    if isinstance(cmd, Command.Winreg)]
        self.assertIn(
            r'HKCU\Software\Microsoft\Internet Explorer\TypedURLs', keys)
        self.assertNotIn(
            r'HKCU\Software\Microsoft\Internet Explorer\Main\FeatureControl', keys)

    def test_chromium_running_debian(self):
        """Chromium is detected under the name Debian and Arch run it as"""
        self.assertTrue(self._bundled_cleaner_detects(
            'chromium', 'linux', 'chromium'))

    def test_firefox_running_esr(self):
        """Debian's Firefox ESR is detected as a running Firefox"""
        self.assertTrue(self._bundled_cleaner_detects(
            'firefox', 'linux', 'firefox-esr'))

    def test_librewolf_running_windows(self):
        """LibreWolf is detected as running on Windows"""
        self.assertTrue(self._bundled_cleaner_detects(
            'librewolf', 'win32', 'librewolf.exe'))

    def test_zen_running(self):
        """Zen is detected under the names its builds run as"""
        for platform, exename in (('linux', 'zen'), ('linux', 'zen-bin'),
                                  ('win32', 'zen.exe')):
            with self.subTest(platform=platform, exename=exename):
                self.assertTrue(self._bundled_cleaner_detects(
                    'zen', platform, exename))

    @common.skipIfWindows
    def test_chromium_brave_every_profile(self):
        """Chromium and Brave clean profiles other than Default"""
        config = self.mkdtemp(prefix='bleachbit-chromium-profiles')
        bases = {
            'brave': 'BraveSoftware/Brave-Browser',
            'chromium': 'chromium',
        }
        with common.set_temporary_env('XDG_CONFIG_HOME', config):
            for cleaner_id, base in bases.items():
                with self.subTest(cleaner_id=cleaner_id):
                    history = os.path.join(
                        config, base, 'Profile 1', 'History')
                    common.touch_file(history)
                    self.assertIn(history, self._bundled_option_paths(
                        cleaner_id, 'history', 'linux'))

    @common.skipIfWindows
    def test_passwords_login_data_for_account(self):
        """Passwords delete the account password store too"""
        config = self.mkdtemp(prefix='bleachbit-login-data')
        profiles = {
            'brave': 'BraveSoftware/Brave-Browser/Default',
            'chromium': 'chromium/Default',
            'google_chrome': 'google-chrome/Default',
            'microsoft_edge': 'microsoft-edge/Default',
            'opera': 'opera',
            'vivaldi': 'vivaldi/Default',
        }
        with common.set_temporary_env('XDG_CONFIG_HOME', config):
            for cleaner_id, profile in profiles.items():
                with self.subTest(cleaner_id=cleaner_id):
                    login_data = os.path.join(
                        config, profile, 'Login Data For Account')
                    common.touch_file(login_data)
                    self.assertIn(login_data, self._bundled_option_paths(
                        cleaner_id, 'passwords', 'linux'))

    @common.skipIfWindows
    def test_chrome_vacuum_skips_journal(self):
        """Chrome vacuum does not open a rollback journal as a database"""
        config = self.mkdtemp(prefix='bleachbit-chrome-vacuum')
        profile = os.path.join(config, 'google-chrome', 'Default')
        favicons = os.path.join(profile, 'Favicons')
        journal = os.path.join(profile, 'Favicons-journal')
        common.touch_file(favicons)
        common.touch_file(journal)
        with common.set_temporary_env('XDG_CONFIG_HOME', config):
            paths = self._bundled_option_paths(
                'google_chrome', 'vacuum', 'linux')
        self.assertIn(favicons, paths)
        self.assertNotIn(journal, paths)

    @common.skipIfWindows
    def test_vivaldi_opera_paths_once(self):
        """Vivaldi and snap Opera list each file once"""
        home = self.mkdtemp(prefix='bleachbit-duplicate-paths')
        config = os.path.join(home, '.config')
        vivaldi_history = os.path.join(config, 'vivaldi', 'Default', 'History')
        opera_history = os.path.join(
            home, 'snap', 'opera', '420', '.config', 'opera', 'History')
        common.touch_file(vivaldi_history)
        common.touch_file(opera_history)
        os.symlink('420', os.path.join(home, 'snap', 'opera', 'current'))
        # Bootstrap points XDG_CONFIG_HOME at ~/.config when it is unset
        with common.set_temporary_env('HOME', home), \
                common.set_temporary_env('XDG_CONFIG_HOME', config):
            vivaldi_paths = self._bundled_option_paths(
                'vivaldi', 'history', 'linux')
            opera_paths = self._bundled_option_paths(
                'opera', 'history', 'linux')
        self.assertEqual(1, vivaldi_paths.count(vivaldi_history))
        opera_real = [os.path.realpath(path) for path in opera_paths]
        self.assertEqual(1, opera_real.count(os.path.realpath(opera_history)))
