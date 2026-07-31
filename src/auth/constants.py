import re

# Compile regex once for performance
BASE64URL_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
