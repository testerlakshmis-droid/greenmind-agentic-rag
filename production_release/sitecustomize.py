"""Runtime tweaks loaded automatically by Python's site module.

For Python 3.14 on Streamlit Cloud, protobuf's compiled upb path can crash
at import time. Force the pure-Python implementation to avoid startup failure.
"""

import os

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
