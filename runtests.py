#!/usr/bin/env python
import logging
import sys

import pytest

# No logging
logging.disable(logging.CRITICAL)


if __name__ == '__main__':
    args = sys.argv[1:]
    result_code = pytest.main(args)
    sys.exit(result_code)
