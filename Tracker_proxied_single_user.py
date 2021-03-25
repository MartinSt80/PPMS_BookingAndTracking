#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep

from ppms_lib import Options, TrackerCall

required_keys = ('PPMS_systemid', 'PPMS_systemcode', 'tracker_frequency', 'ignored_logins', 'proxy_address', 'tracker_port', 'user_login')

try:
	system_options = Options.OptionReader('SystemOptions.txt', required_keys)
except Exception as e:
	exit(str(e))

while True:
	TrackerCall.NewTrackeroverProxy(system_options.getValue('user_login'), system_options)
	sleep(60 * system_options.getValue(int('tracker_frequency')))