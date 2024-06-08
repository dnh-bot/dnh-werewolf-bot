# pylint: disable=anomalous-backslash-in-string
"""
Module containing constants used throughout the wrapper
"""

import re


API_URL = "https://api.github.com"

TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ %z"

GIST_URL_REGEX = re.compile(
    "(?:https:\/\/)?gist\.github\.com\/(?P<username>.+)\/(?P<gist_id>[\d\w]+)|(?:https:\/\/)?gist\.github\.com\/(?P<gist_id2>[\d\w]+)"
)
