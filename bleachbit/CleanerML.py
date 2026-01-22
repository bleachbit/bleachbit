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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Create cleaners from CleanerML (markup language)
"""

# standard library
import logging
import os
import stat
import sys
import xml.etree.ElementTree
import xml.parsers.expat

# local import
import bleachbit
from bleachbit.Action import ActionProvider
from bleachbit.FileUtilities import expand_glob_join, listdir
from bleachbit.General import boolstr_to_bool
from bleachbit.General import os_match as general_os_match
from bleachbit.Language import get_text as _
from bleachbit import Cleaner
if 'win32' == sys.platform:
    from bleachbit.Windows import read_registry_key

logger = logging.getLogger(__name__)


class _ETSimpleTextNode:

    ELEMENT_NODE = 1
    TEXT_NODE = 3

    def __init__(self, data):
        self.nodeType = self.TEXT_NODE
        self.data = data


class _ETSimpleElementNode:

    ELEMENT_NODE = 1
    TEXT_NODE = 3

    def __init__(self, element):
        self._element = element
        self.nodeType = self.ELEMENT_NODE
        self.nodeName = element.tag

    def getAttribute(self, name):
        return self._element.attrib.get(name, '')

    def hasAttribute(self, name):
        return name in self._element.attrib

    @property
    def childNodes(self):
        nodes = []
        if self._element.text:
            nodes.append(_ETSimpleTextNode(self._element.text))
        for child in list(self._element):
            nodes.append(_ETSimpleElementNode(child))
            if child.tail:
                nodes.append(_ETSimpleTextNode(child.tail))
        return nodes


class _ETActionElementAdapter:

    def __init__(self, element):
        self._element = element

    def getAttribute(self, name):
        return self._element.attrib.get(name, '')

    def toxml(self):
        return xml.etree.ElementTree.tostring(self._element, encoding='unicode')


def _gettext_etree(element):
    """Return text like General.getText() would for minidom nodes."""
    if element is None:
        return ''
    rc = element.text or ''
    for child in list(element):
        rc += child.tail or ''
    return rc


def _toxml_etree(element):
    return xml.etree.ElementTree.tostring(element, encoding='unicode')


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
        mylist = list({x for x in (os.getenv(v1), os.getenv(v2)) if x})
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

        try:
            tree = xml.etree.ElementTree.parse(pathname)
            root_element = tree.getroot()
        except (xml.etree.ElementTree.ParseError, xml.parsers.expat.ExpatError) as e:
            logger.error(
                "Error parsing CleanerML file %s with error %s", pathname, e)
            return

        if root_element.tag == 'cleaner':
            cleaner_element = root_element
        else:
            cleaner_element = root_element.find('.//cleaner')
            if cleaner_element is None:
                logger.error(
                    "Error parsing CleanerML file %s: missing <cleaner> element", pathname)
                return

        self.handle_cleaner(cleaner_element)

    def get_cleaner(self):
        """Return the created cleaner"""
        return self.cleaner

    def os_match(self, os_str, platform=sys.platform):
        """Return boolean whether operating system matches

        Keyword arguments:
        os_str -- the required operating system as written in XML
        platform -- used only for unit tests
        """
        # If in .pot-creation-mode, return true.
        if self.xlate_mode:
            return True

        return general_os_match(os_str, platform)

    def handle_cleaner(self, cleaner):
        """<cleaner> element"""
        self.cleaner.id = cleaner.attrib.get('id', '')
        if not self.os_match(cleaner.attrib.get('os', '')):
            return

        label = cleaner.find('label')
        if label is None:
            raise IndexError('missing <label> element')
        self.handle_cleaner_label(label)

        description = cleaner.find('description')
        if description is not None:
            self.handle_cleaner_description(description)

        for var in cleaner.findall('var'):
            self.handle_cleaner_var(var)

        for option in cleaner.findall('option'):
            try:
                self.handle_cleaner_option(option)
            except Exception:
                exc_msg = _(
                    "Error in handle_cleaner_option() for cleaner id = {cleaner_id}, option XML={option_xml}")
                logger.exception(exc_msg.format(
                    cleaner_id=self.cleaner.id, option_xml=_toxml_etree(option)))
        self.handle_cleaner_running(cleaner.findall('running'))
        self.handle_localizations(cleaner.findall('localizations'))

    def handle_cleaner_label(self, label):
        """<label> element under <cleaner>"""
        self.cleaner.name = _(_gettext_etree(label))
        translate = label.attrib.get('translate', '')
        if translate and boolstr_to_bool(translate):
            self.xlate_cb(self.cleaner.name)

    def handle_cleaner_description(self, description):
        """<description> element under <cleaner>"""
        self.cleaner.description = _(_gettext_etree(description))
        translators = description.attrib.get('translators', '')
        self.xlate_cb(self.cleaner.description, translators)

    def handle_cleaner_running(self, running_elements):
        """<running> element under <cleaner>"""
        # example: <running type="command">opera</running>
        for running in running_elements:
            if not self.os_match(running.attrib.get('os', '')):
                continue
            detection_type = running.attrib.get('type', '')
            value = _gettext_etree(running)
            same_user = running.attrib.get('same_user') or False
            self.cleaner.add_running(detection_type, value, same_user)

    def handle_cleaner_option(self, option):
        """<option> element"""
        self.option_id = option.attrib.get('id', '')
        self.option_description = None
        self.option_name = None

        label = option.find('label')
        if label is None:
            raise IndexError('missing <label> under <option>')
        self.handle_cleaner_option_label(label)

        description = option.find('description')
        if description is None:
            raise IndexError('missing <description> under <option>')
        self.handle_cleaner_option_description(description)

        warning = option.find('warning')
        if warning is not None:
            self.handle_cleaner_option_warning(warning)
            if self.option_warning:
                self.cleaner.set_warning(self.option_id, self.option_warning)

        for action in option.findall('action'):
            self.handle_cleaner_option_action(action)

        self.cleaner.add_option(
            self.option_id, self.option_name, self.option_description)

    def handle_cleaner_option_label(self, label):
        """<label> element under <option>"""
        self.option_name = _(_gettext_etree(label))
        translate = label.attrib.get('translate', '')
        translators = label.attrib.get('translators', '')
        if not translate or boolstr_to_bool(translate):
            self.xlate_cb(self.option_name, translators)

    def handle_cleaner_option_description(self, description):
        """<description> element under <option>"""
        self.option_description = _(_gettext_etree(description))
        translators = description.attrib.get('translators', '')
        self.xlate_cb(self.option_description, translators)

    def handle_cleaner_option_warning(self, warning):
        """<warning> element under <option>"""
        self.option_warning = _(_gettext_etree(warning))
        self.xlate_cb(self.option_warning)

    def handle_cleaner_option_action(self, action_node):
        """<action> element under <option>"""
        if not self.os_match(action_node.attrib.get('os', '')):
            return
        command = action_node.attrib.get('command', '')
        provider = None
        for actionplugin in ActionProvider.plugins:
            if actionplugin.action_key == command:
                provider = actionplugin(
                    _ETActionElementAdapter(action_node), self.vars)
        if provider is None:
            raise RuntimeError(f"Invalid command '{command}'")
        self.cleaner.add_action(self.option_id, provider)

    def handle_localizations(self, localization_nodes):
        """<localizations> element under <cleaner>"""
        if not 'posix' == os.name:
            return
        # pylint: disable=import-outside-toplevel
        from bleachbit import Unix
        for localization_node in localization_nodes:
            for child_element in list(localization_node):
                Unix.locales.add_xml(_ETSimpleElementNode(child_element))
        # Add a dummy action so the file isn't reported as unusable
        self.cleaner.add_action('localization', ActionProvider(None))

    def handle_cleaner_var(self, var):
        r"""Handle one <var> element under <cleaner>.

        Example:

        <var name="basepath">
         <value search="glob">~/.config/f*</value>
         <value>~/.config/foo</value>
         <value>%AppData\foo</value>
         <value search="winreg" path="HKCU\Software\Valve\Steam" name="SteamPath"></value>
         </var>
        """
        var_name = var.attrib.get('name', '')
        for value_element in var.findall('value'):
            if not self.os_match(value_element.attrib.get('os', '')):
                continue
            value_str = _gettext_etree(value_element)
            search_type = value_element.attrib.get('search', '')
            if search_type == 'glob':
                value_list = expand_glob_join(value_str, '')
            elif search_type == 'winreg':
                if 'win32' != sys.platform:
                    continue
                value_list = read_registry_key(value_element.attrib.get(
                    'path', ''), value_element.attrib.get('name', ''))
                if value_list == None:
                    continue
                else:
                    value_list = [value_list, ]
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
        # If the application is installed, locale_cleaners_dir is None.
        # If portable mode, local_cleaners_dir is under the directory of
        # `bleachbit.py`.
        cleanerdirs += (bleachbit.local_cleaners_dir, )
    if not local_only and bleachbit.system_cleaners_dir:
        cleanerdirs += (bleachbit.system_cleaners_dir, )
    for pathname in listdir(cleanerdirs):
        if not pathname.lower().endswith('.xml'):
            continue
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
    not_usable = []
    for pathname in cleanerml_files:
        try:
            xmlcleaner = CleanerML(pathname)
        except Exception:
            logger.exception(_("Error reading cleaner: %s"), pathname)
            continue
        cleaner = xmlcleaner.get_cleaner()
        if cleaner.is_usable():
            Cleaner.backends[cleaner.id] = cleaner
        else:
            if cleaner.id:
                not_usable.append(cleaner.id)
            else:
                not_usable.append(os.path.basename(pathname))
        files_done += 1
        cb_progress(1.0 * files_done / total_files)
        yield True
    if not_usable:
        logger.debug(
            "%d cleaners are not usable on this OS because they have no actions: %s", len(not_usable), ', '.join(not_usable))


def pot_fragment(msgid, pathname, translators=None):
    """Create a string fragment for generating .pot files"""
    msgid = msgid.replace('"', '\\"')  # escape quotation mark
    if translators:
        translators = f"#. {translators}\n"
    else:
        translators = ""
    pathname = pathname.replace('\\', '/')
    ret = f'''{translators}#: {pathname}
msgid "{msgid}"
msgstr ""

'''
    return ret


def create_pot():
    """Create a .pot for translation using gettext

    This function is called from the Makefile.

    Paths and newlines are normalized to Unix style.
    """

    with open('../po/cleanerml.pot', 'w', encoding='utf-8', newline='\n') as f:
        for pathname in listdir('../cleaners'):
            if not pathname.lower().endswith(".xml"):
                continue
            strings = []
            try:
                CleanerML(pathname,
                          lambda newstr, translators=None, current_strings=strings:
                          current_strings.append([newstr, translators]))
            except Exception:
                logger.exception(_("Error reading cleaner: %s"), pathname)
                continue
            for (string, translators) in strings:
                f.write(pot_fragment(string, pathname, translators))
