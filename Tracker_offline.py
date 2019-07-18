#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os

from lib import Options

required_keys = ('PPMS_facilityid', 'PPMS_systemid', 'tracker_frequency', 'user_login')

try:
    system_options = Options.OptionReader('SystemOptions.txt', required_keys)
except Exception as e:
    exit(str(e))

logfile_dir = (os.path.dirname(os.path.realpath(__file__)))
logfile_name = time.strftime('%m_%Y', time.localtime()) + '.csv'
logfile_path = os.path.join(logfile_dir, logfile_name)

if not os.path.isfile(logfile_path):
    with open(logfile_path, 'w') as f:
        logfile_header = ', '.join(('PPMS_facilityid',
                                    'PPMS_systemid',
                                    'Frequency / min',
                                    'User login',
                                    'Timestamp')) + '\n'
        f.write(logfile_header)

with open(logfile_path, 'a') as f:
    time_stamp = time.strftime('%Y-%m-%dT%H:%M:00', time.localtime())
    logfile_entry = ', '.join((system_options.getValue('PPMS_facilityid'),
                               system_options.getValue('PPMS_systemid'),
                               system_options.getValue('tracker_frequency'),
                               system_options.getValue('user_login'),
                               time_stamp,
                               )
                              ) + '\n'
    f.write(logfile_entry)
