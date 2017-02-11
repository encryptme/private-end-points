from __future__ import absolute_import, division, print_function, unicode_literals

import sys

from .main import main


returncode = main()
if returncode != 0:
    sys.exit(returncode)
