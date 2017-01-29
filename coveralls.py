#!/usr/bin/env python
# coding=utf-8

import os
from subprocess import call

if __name__ == '__main__':

    # create a report from the coverage data
    if 'CI' in os.environ:
        rc = call('coveralls')
        raise SystemExit(rc)
