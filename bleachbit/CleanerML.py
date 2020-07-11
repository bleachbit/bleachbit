# vim: ts=4:sw=4:expandtab

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


"""
Create cleaners from CleanerML (markup language)
"""

import bleachbit
from bleachbit.Action import ActionProvider
from bleachbit import _
from bleachbit.General import boolstr_to_bool, getText
from bleachbit.FileUtilities import expand_glob_join, listdir
from bleachbit import Cleaner

import logging
import os
import sys
import xml.dom.minidom

logger = logging.getLogger(__name__)


def default_vars():
    """Return default multi-value variables"""
    ret = {}
    if not os.name == 'nt':
        return ret
    # Expand ProgramFiles to also be ProgramW6432, etc.
    wowvars = (('ProgramFiles', 'ProgramW6432'),
               ('CommonProgramFiles', 'CommonProgramW6432'))
    for v1, v2 in wowvars:
        # Remove None, if variable is not found.
        # Make list unique.
        mylist = list(set([x for x in (os.getenv(v1), os.getenv(v2)) if x]))
        ret[v1] = mylist
    return ret


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
        self.vars = default_vars()
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

    def os_match(self, os_str, platform=sys.platform):
        """Return boolean whether operating system matches

        Keyword arguments:
        os_str -- the required operating system as written in XML
        platform -- used only for unit tests
        """
        # If blank or if in .pot-creation-mode, return true.
        if len(os_str) == 0 or self.xlate_mode:
            return True
        # Otherwise, check platform.
        # Define the current operating system.
        if platform == 'darwin':
            current_os = ('darwin', 'bsd', 'unix')
        elif platform.startswith('linux'):
            current_os = ('linux', 'unix')
        elif platform.startswith('openbsd'):
            current_os = ('bsd', 'openbsd', 'unix')
        elif platform.startswith('netbsd'):
            current_os = ('bsd', 'netbsd', 'unix')
        elif platform.startswith('freebsd'):
            current_os = ('bsd', 'freebsd', 'unix')
        elif platform == 'win32':
            current_os = ('windows')
        else:
            raise RuntimeError('Unknown operating system: %s ' % sys.platform)
        # Compare current OS against required OS.
        return os_str in current_os

    def handle_cleaner(self, cleaner):
        """<cleaner> element"""
        if not self.os_match(cleaner.getAttribute('os')):
            return
        self.cleaner.id = cleaner.getAttribute('id')
        self.handle_cleaner_label(cleaner.getElementsByTagName('label')[0])
        description = cleaner.getElementsByTagName('description')
        if description and description[0].parentNode == cleaner:
            self.handle_cleaner_description(description[0])
        for var in cleaner.getElementsByTagName('var'):
            self.handle_cleaner_var(var)
        for option in cleaner.getElementsByTagName('option'):
            try:
                self.handle_cleaner_option(option)
            except:
                exc_msg = _(
                    "Error in handle_cleaner_option() for cleaner id = {cleaner_id}, option XML={option_xml}")
                logger.exception(exc_msg.format(
                    cleaner_id=exc_dict, option_xml=option.toxml()))
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
            if not self.os_match(running.getAttribute('os')):
                continue
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
        if not self.os_match(action_node.getAttribute('os')):
            return
        command = action_node.getAttribute('command')
        provider = None
        for actionplugin in ActionProvider.plugins:
            if actionplugin.action_key == command:
                provider = actionplugin(action_node, self.vars)
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

    def handle_cleaner_var(self, var):
        """Handle one <var> element under <cleaner>.

        Example:

        <var name="basepath">
         <value search="glob">~/.config/f*</value>
         <value>~/.config/foo</value>
         <value>%AppData\foo</value>
         </var>
        """
        var_name = var.getAttribute('name')
        for value_element in var.getElementsByTagName('value'):
            if not self.os_match(value_element.getAttribute('os')):
                continue
            value_str = getText(value_element.childNodes)
            is_glob = value_element.getAttribute('search') == 'glob'
            if is_glob:
                value_list = expand_glob_join(value_str, '')
            else:
                value_list = [value_str, ]
            if var_name in self.vars:
                # append
                self.vars[var_name] = value_list + self.vars[var_name]
            else:
                # initialize
                self.vars[var_name] = value_list


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
            # TRANSLATORS: When BleachBit detects the file permissions are
            # insecure, it will not load the cleaner as if it did not exist.
            logger.warning(
                _("Ignoring cleaner because it is world writable: %s"), pathname)
            continue
        yield pathname


def load_cleaners(cb_progress=lambda x: None):
    """Scan for CleanerML and load them"""
    cleanerml_files = list(list_cleanerml_files())
    cleanerml_files.sort()
    if not cleanerml_files:
        logger.debug('No CleanerML files to load.')
        return
    total_files = len(cleanerml_files)
    cb_progress(0.0)
    files_done = 0
    for pathname in cleanerml_files:
        try:
            xmlcleaner = CleanerML(pathname)
        except:
            logger.exception(_("Error reading cleaner: %s"), pathname)
            continue
        cleaner = xmlcleaner.get_cleaner()
        if cleaner.is_usable():
            Cleaner.backends[cleaner.id] = cleaner
        else:
            logger.debug(
                # TRANSLATORS: An action is something like cleaning a specific file.
                # "Not usable" means the whole cleaner will be ignored.
                # The substituted variable is a pathname.
                _("Cleaner is not usable on this OS because it has no actions: %s"), pathname)
        files_done += 1
        cb_progress(1.0 * files_done / total_files)
        yield True


def pot_fragment(msgid, pathname, translators=None):
    """Create a string fragment for generating .pot files"""
    msgid = msgid.replace('"', '\\"')  # escape quotation mark
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
            logger.exception(_("Error reading cleaner: %s"), pathname)
            continue
        for (string, translators) in strings:
            f.write(pot_fragment(string, pathname, translators))

    f.close()
