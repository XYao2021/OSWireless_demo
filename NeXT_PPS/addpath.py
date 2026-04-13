import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# current folder
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# parent folder
PARENT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)
