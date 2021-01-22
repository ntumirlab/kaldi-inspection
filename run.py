# -*- coding: UTF-8 -*-
import os
from app import create_app
app = create_app()
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(host='0.0.0.0', debug=True)  # , ssl_context='adhoc')
