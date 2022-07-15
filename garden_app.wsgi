#! /usr/bin/python3

import logging
import sys, os

logging.basicConfig(stream=sys.stderr)

sys.path.insert(0, '/var/www/html/garden/')
os.chdir(sys.path[0])

from garden_app import app as application

application.secret_key = 'secret_for_application'
