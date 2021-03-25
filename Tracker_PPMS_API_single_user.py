#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep
from ppms_lib import Options, TrackerCall

required_keys = ('PPMS_systemid', 'PPMS_systemcode', 'tracker_frequency', 'ignored_logins', 'user_login')
try:
	system_options = Options.OptionReader('SystemOptions.txt', required_keys)
except Exception as e:
	exit(str(e))

required_keys = ('tracker_URL',)
try:
	proxy_options = Options.OptionReader('ProxyOptions.txt', required_keys)
except Exception as e:
	exit(str(e))

while True:
	TrackerCall.NewTrackerCall(system_options.getValue('user_login'), system_options, proxy_options)
	sleep(60 * system_options.getValue(int('tracker_frequency')))
