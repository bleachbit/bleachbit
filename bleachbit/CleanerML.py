# vim: ts=4:sw=4:expandtab

# BleachBit
# Copyright (C) 2008-2017 Andrew Ziem
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
Create cleaners from CleanerML (markup language)
"""

from __future__ import absolute_import, print_function

import bleachbit
from bleachbit.Action import ActionProvider
from bleachbit import _
from bleachbit.General import boolstr_to_bool, getText
from bleachbit.FileUtilities import listdir
from bleachbit import Cleaner

import logging
import os
import sys
import xml.dom.minidom

logger = logging.getLogger(__name__)


class CleanerML:

    """Create a cleaner from CleanerML"""

    def __init__(self, pathname, xlate_cb=None):
        """Create cleaner from XML in pathname.

        If xlate_cb is set, use it as a callback for each
        translate-able string.
        """

        self.action = None
        self.cleaner = Cleaner.Cleaner()
        self.option_id = None
        self.option_name = None
        self.option_description = None
        self.option_warning = None
        self.xlate_cb = xlate_cb
        if self.xlate_cb is None:
            self.xlate_mode = False
            self.xlate_cb = lambda x, y=None: None  # do nothing
        else:
            self.xlate_mode = True

        dom = xml.dom.minidom.parse(pathname)

        self.handle_cleaner(dom.getElementsByTagName('cleaner')[0])

    def get_cleaner(self):
        """Return the created cleaner"""
        return self.cleaner

    def os_match(self, os_str):
        """Return boolean whether operating system matches"""
        # If blank or if in .pot-creation-mode, return true.
        if len(os_str) == 0 or self.xlate_mode:
            return True
        # Otherwise, check platform.
        if os_str == 'linux' and sys.platform.startswith('linux'):
            return True
        if os_str == 'windows' and sys.platform == 'win32':
            return True
        return False

    def handle_cleaner(self, cleaner):
        """<cleaner> element"""
        if not self.os_match(cleaner.getAttribute('os')):
            return
        self.cleaner.id = cleaner.getAttribute('id')
        self.handle_cleaner_label(cleaner.getElementsByTagName('label')[0])
        description = cleaner.getElementsByTagName('description')
        if description and description[0].parentNode == cleaner:
            self.handle_cleaner_description(description[0])
        for option in cleaner.getElementsByTagName('option'):
            try:
                self.handle_cleaner_option(option)
            except:
                logger.exception('error in handle_cleaner_option() for cleaner id = %s, option XML=%s',
                                 self.cleaner.id, option.toxml())
        self.handle_cleaner_running(cleaner.getElementsByTagName('running'))
        self.handle_localizations(
            cleaner.getElementsByTagName('localizations'))

    def handle_cleaner_label(self, label):
        """<label> element under <cleaner>"""
        self.cleaner.name = _(getText(label.childNodes))
        translate = label.getAttribute('translate')
        if translate and boolstr_to_bool(translate):
            self.xlate_cb(self.cleaner.name)

    def handle_cleaner_description(self, description):
        """<description> element under <cleaner>"""
        self.cleaner.description = _(getText(description.childNodes))
        translators = description.getAttribute('translators')
        self.xlate_cb(self.cleaner.description, translators)

    def handle_cleaner_running(self, running_elements):
        """<running> element under <cleaner>"""
        # example: <running type="command">opera</running>
        for running in running_elements:
            detection_type = running.getAttribute('type')
            value = getText(running.childNodes)
            self.cleaner.add_running(detection_type, value)

    def handle_cleaner_option(self, option):
        """<option> element"""
        self.option_id = option.getAttribute('id')
        self.option_description = None
        self.option_name = None

        self.handle_cleaner_option_label(
            option.getElementsByTagName('label')[0])
        description = option.getElementsByTagName('description')
        self.handle_cleaner_option_description(description[0])
        warning = option.getElementsByTagName('warning')
        if warning:
            self.handle_cleaner_option_warning(warning[0])
            if self.option_warning:
                self.cleaner.set_warning(self.option_id, self.option_warning)

        for action in option.getElementsByTagName('action'):
            self.handle_cleaner_option_action(action)

        self.cleaner.add_option(
            self.option_id, self.option_name, self.option_description)

    def handle_cleaner_option_label(self, label):
        """<label> element under <option>"""
        self.option_name = _(getText(label.childNodes))
        translate = label.getAttribute('translate')
        translators = label.getAttribute('translators')
        if not translate or boolstr_to_bool(translate):
            self.xlate_cb(self.option_name, translators)

    def handle_cleaner_option_description(self, description):
        """<description> element under <option>"""
        self.option_description = _(getText(description.childNodes))
        translators = description.getAttribute('translators')
        self.xlate_cb(self.option_description, translators)

    def handle_cleaner_option_warning(self, warning):
        """<warning> element under <option>"""
        self.option_warning = _(getText(warning.childNodes))
        self.xlate_cb(self.option_warning)

    def handle_cleaner_option_action(self, action_node):
        """<action> element under <option>"""
        command = action_node.getAttribute('command')
        provider = None
        for actionplugin in ActionProvider.plugins:
            if actionplugin.action_key == command:
                provider = actionplugin(action_node)
        if provider is None:
            raise RuntimeError("Invalid command '%s'" % command)
        self.cleaner.add_action(self.option_id, provider)

    def handle_localizations(self, localization_nodes):
        """<localizations> element under <cleaner>"""
        if not 'posix' == os.name:
            return
        from bleachbit import Unix
        for localization_node in localization_nodes:
            for child_node in localization_node.childNodes:
                Unix.locales.add_xml(child_node)
        # Add a dummy action so the file isn't reported as unusable
        self.cleaner.add_action('localization', ActionProvider(None))


def list_cleanerml_files(local_only=False):
    """List CleanerML files"""
    cleanerdirs = (bleachbit.personal_cleaners_dir, )
    if bleachbit.local_cleaners_dir:
        # If the application is installed, locale_cleaners_dir is None
        cleanerdirs = (bleachbit.local_cleaners_dir, )
    if not local_only and bleachbit.system_cleaners_dir:
        cleanerdirs += (bleachbit.system_cleaners_dir, )
    for pathname in listdir(cleanerdirs):
        if not pathname.lower().endswith('.xml'):
            continue
        import stat
        st = os.stat(pathname)
        if sys.platform != 'win32' and stat.S_IMODE(st[stat.ST_MODE]) & 2:
            logger.warning("ignoring cleaner because it is world writable: %s", pathname)
            continue
        yield pathname


def load_cleaners():
    """Scan for CleanerML and load them"""
    for pathname in list_cleanerml_files():
        try:
            xmlcleaner = CleanerML(pathname)
        except:
            logger.exception('error reading cleaner: %s', pathname)
            continue
        cleaner = xmlcleaner.get_cleaner()
        if cleaner.is_usable():
            Cleaner.backends[cleaner.id] = cleaner
        else:
            logger.debug('cleaner is not usable on this OS because it has no actions: %s', pathname)


def pot_fragment(msgid, pathname, translators=None):
    """Create a string fragment for generating .pot files"""
    msgid = msgid.replace('"', '\\"') # escape quotation mark
    if translators:
        translators = "#. %s\n" % translators
    else:
        translators = ""
    ret = '''%s#: %s
msgid "%s"
msgstr ""

''' % (translators, pathname, msgid)
    return ret


def create_pot():
    """Create a .pot for translation using gettext"""

    f = open('../po/cleanerml.pot', 'w')

    for pathname in listdir('../cleaners'):
        if not pathname.lower().endswith(".xml"):
            continue
        strings = []
        try:
            CleanerML(pathname,
                      lambda newstr, translators=None:
                      strings.append([newstr, translators]))
        except:
            logger.exception('error reading: %s', pathname)
            continue
        for (string, translators) in strings:
            f.write(pot_fragment(string, pathname, translators))

    f.close()
