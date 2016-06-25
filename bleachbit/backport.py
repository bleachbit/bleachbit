
# from Python 2.7
# https://github.com/python/cpython/blob/75891384fae8e4c564b7d8ca9c16a58922d2f7c0/Lib/ntpath.py

# because the Python 2.5 version used on Windows has bugs such as removing
# "$foo" where foo is unknown. This is a problem because it can be a legitimate
# filename.

import os
import sys

_unicode = unicode


def expandvars(path):
    """Expand shell variables of the forms $var, ${var} and %var%.

    Unknown variables are left unchanged."""
    if '$' not in path and '%' not in path:
        return path
    import string
    varchars = string.ascii_letters + string.digits + '_-'
    if isinstance(path, _unicode):
        encoding = sys.getfilesystemencoding()

        def getenv(var):
            return os.environ[var.encode(encoding)].decode(encoding)
    else:
        def getenv(var):
            return os.environ[var]
    res = ''
    index = 0
    pathlen = len(path)
    while index < pathlen:
        c = path[index]
        if c == '\'':   # no expansion within single quotes
            path = path[index + 1:]
            pathlen = len(path)
            try:
                index = path.index('\'')
                res = res + '\'' + path[:index + 1]
            except ValueError:
                res = res + c + path
                index = pathlen - 1
        elif c == '%':  # variable or '%'
            if path[index + 1:index + 2] == '%':
                res = res + c
                index = index + 1
            else:
                path = path[index + 1:]
                pathlen = len(path)
                try:
                    index = path.index('%')
                except ValueError:
                    res = res + '%' + path
                    index = pathlen - 1
                else:
                    var = path[:index]
                    try:
                        res = res + getenv(var)
                    except KeyError:
                        res = res + '%' + var + '%'
        elif c == '$':  # variable or '$$'
            if path[index + 1:index + 2] == '$':
                res = res + c
                index = index + 1
            elif path[index + 1:index + 2] == '{':
                path = path[index + 2:]
                pathlen = len(path)
                try:
                    index = path.index('}')
                    var = path[:index]
                    try:
                        res = res + getenv(var)
                    except KeyError:
                        res = res + '${' + var + '}'
                except ValueError:
                    res = res + '${' + path
                    index = pathlen - 1
            else:
                var = ''
                index = index + 1
                c = path[index:index + 1]
                while c != '' and c in varchars:
                    var = var + c
                    index = index + 1
                    c = path[index:index + 1]
                try:
                    res = res + getenv(var)
                except KeyError:
                    res = res + '$' + var
                if c != '':
                    index = index - 1
        else:
            res = res + c
        index = index + 1
    return res
