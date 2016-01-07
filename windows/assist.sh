#!/bin/bash

# Copyright (C) 2008-2016 Andrew Ziem.  All rights reserved.
# License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
# This is free software: you are free to change and redistribute it.
# There is NO WARRANTY, to the extent permitted by law.
#
# Assist with the Windows build using tools commonly found on Linux.
#


echo "Removing Linux-specific cleaners"
grep -l os=.linux. dist/share/cleaners/*xml | xargs rm -f

echo "Shrinking translations"
# Windows typically does not have msgunfmt
python setup.py clean-dist
