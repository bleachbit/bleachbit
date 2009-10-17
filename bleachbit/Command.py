# vim: ts=4:sw=4:expandtab

## BleachBit
## Copyright (C) 2009 Andrew Ziem
## http://bleachbit.sourceforge.net
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.



"""
Command design pattern implementation for cleaning
"""



import os
import types
import FileUtilities

if 'nt' == os.name:
    import Windows
else:
    from General import WindowsError



class Delete:
    """Delete a single file or directory.  Obey the user
    preference regarding shredding."""


    def __init__(self, path):
        """Create a Delete instance to delete 'path'"""
        self.path = path
        self.shred = False


    def execute(self, really_delete):
        """Make changes and return results"""
        ret = { \
            # TRANSLATORS: This is the label in the log indicating will be
            # deleted (for previews) or was actually deleted
            'label' : _('Delete'),
            'n_deleted' : 1,
            'n_special' : 0,
            'path' : self.path,
            'size' : FileUtilities.getsize(self.path) }
        if really_delete:
            try:
                FileUtilities.delete(self.path, self.shred)
            except WindowsError, e:
                # WindowsError: [Error 32] The process cannot access the file because it is being
                # used by another process: u'C:\\Documents and Settings\\username\\Cookies\\index.dat'
                if 32 != e.winerror:
                    raise
                try:
                    Windows.delete_locked_file(self.path)
                except:
                    raise
                else:
                    # TRANSLATORS: The file will be deleted when the
                    # system reboots
                    ret['label'] = _('Mark for deletion')
        yield ret


class Function:
    """Execute a simple Python function"""

    def __init__(self, path, func, label):
        """Path is a pathname that exists or None.  If
        it exists, func takes the pathname.  Otherwise,
        function returns the size."""
        self.path = path
        self.func = func
        self.label = label
        try:
            assert(isinstance(func, types.FunctionType))
        except AssertionError:
            raise AssertionError('Expected MethodType but got %s' % type(func))

    def execute(self, really_delete):
        ret = { \
            'label' : self.label,
            'n_deleted' : 0,
            'n_special' : 1,
            'path' : self.path,
            'size' : None }

        if really_delete:
            if None == self.path:
                # Function takes no path.  It returns the size.
                func_ret = self.func()
                if isinstance(func_ret, types.GeneratorType):
                    # function returned generator
                    for func_ret in self.func():
                        if True == func_ret:
                            # return control to GTK idle loop
                            yield True
                # either way, func_ret should be an integer
                assert(isinstance(func_ret, (int, long)))
                ret['size'] = func_ret
            else:
                # Function takes a path.  We check the size.
                oldsize = FileUtilities.getsize(self.path)
                self.func(self.path)
                try:
                    newsize = FileUtilities.getsize(self.path)
                except OSError, e:
                    if 2 == e.errno:
                        # file does not exist
                        newsize = 0
                    else:
                        raise
                ret['size'] = oldsize - newsize
        yield ret



class Shred(Delete):
    """Shred a single file"""

    def __init__(self, path):
        """Create an instance to shred 'path'"""
        self.shred = True
        Delete.__init__(self, path)



class Truncate(Delete):
    """Truncate a single file"""


    def execute(self, really_delete):
        """Make changes and return results"""
        ret = { \
            # TRANSLATORS: The file will be truncated to 0 bytes in length
            'label' : _('Truncate'),
            'n_deleted' : 1,
            'n_special' : 0,
            'path' : self.path,
            'size' : FileUtilities.getsize(self.path) }
        if really_delete:
            f = open(self.path, 'wb')
            f.truncate(0)
        yield ret


class Winreg:
    """Clean Windows registry"""

    def __init__(self, keyname, valuename):
        """Create the Windows registry cleaner"""
        self.keyname = keyname
        self.valuename = valuename


    def execute(self, really_delete):
        """Execute the Windows registry cleaner"""
        if 'nt' != os.name:
            raise StopIteration
        _str = None # string representation
        ret = None # return value meaning 'deleted' or 'delete-able'
        if self.valuename:
            _str = '%s<%s>' % (self.keyname, self.valuename)
            ret = Windows.delete_registry_value(self.keyname, \
                self.valuename, really_delete)
        else:
            ret = Windows.delete_registry_key(self.keyname, really_delete)
            _str = self.keyname
        if not ret:
            # Nothing to delete or nothing was deleted.  This return
            # makes the auto-hide feature work nicely.
            raise StopIteration

        ret = { \
            'label' : _('Delete registry key'),
            'n_deleted' : 0,
            'n_special' : 1,
            'path' : _str,
            'size' : 0 }

        yield ret


import unittest

class TestCommand(unittest.TestCase):
    """Test cases for commands"""


    def test_Delete(self, cls = Delete):
        """Unit test for Delete"""
        import tempfile
        (fd, path) = tempfile.mkstemp('bleachbit-test')
        os.write(fd, "foo")
        os.close(fd)
        cmd = cls(path)
        self.assert_(os.path.exists(path))

        # preview
        ret = cmd.execute(really_delete = False).next()
        self.assert_(ret['size'] > 0)
        self.assertEqual(ret['path'], path)
        self.assert_(os.path.exists(path))

        # delete
        ret = cmd.execute(really_delete = True).next()
        self.assert_(ret['size'] > 0)
        self.assertEqual(ret['path'], path)
        self.assert_(not os.path.exists(path))


    def test_Function(self):
        """Unit test for Function"""
        import tempfile
        (fd, path) = tempfile.mkstemp('bleachbit-test')
        os.write(fd, "foo")
        os.close(fd)
        cmd = Function(path, FileUtilities.delete, 'bar')
        self.assert_(os.path.exists(path))

        # preview
        ret = cmd.execute(False).next()
        self.assert_(os.path.exists(path))

        # delete
        ret = cmd.execute(True).next()
        self.assert_(ret['size'] > 0)
        self.assertEqual(ret['path'], path)
        self.assert_(not os.path.exists(path))


    def test_Shred(self):
        """Unit test for Shred"""
        self.test_Delete(Shred)


if __name__ == '__main__':
    unittest.main()

