#!/usr/bin/env python
# -*- coding: utf-8 -*-

import win32api, win32con
from time import sleep
from ppms_lib import Options, TrackerCall

required_keys = ('PPMS_systemid', 'PPMS_systemcode', 'tracker_frequency', 'ignored_logins')
try:
	system_options = Options.OptionReader('SystemOptions.txt', required_keys)
except Exception as e:
	exit(str(e))

required_keys = ('tracker_URL',)
try:
	proxy_options = Options.OptionReader('ProxyOptions.txt', required_keys)
except Exception as e:
	exit(str(e))

# Authentication is based on UKN domain server, login is resolved as popXXXXXX, thus requires resolving UPN
user_login = win32api.GetUserNameEx(win32con.NameUserPrincipal).split('@')[0]

while True:
	TrackerCall.NewTrackerCall(user_login, system_options, proxy_options)
	sleep(60 * system_options.getValue(int('tracker_frequency')))
