import sys

from .main import main


returncode = main()
if returncode != 0:
    sys.exit(returncode)
