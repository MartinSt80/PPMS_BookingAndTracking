#!/usr/bin/env python
# -*- coding: utf-8 -*-

import win32api, win32con
from lib import Options, TrackerCall

required_keys = ('PPMS_systemid', 'PPMS_systemcode', 'tracker_frequency', 'ignored_logins', 'proxy_address', 'tracker_port')
try:
	system_options = Options.OptionReader('SystemOptions.txt', required_keys)
except Exception as e:
	exit(str(e))

# Authentication is based on UKN domain server, login is resolved as popXXXXXX, thus requires resolving UPN
TrackerCall.NewTrackeroverProxy(win32api.GetUserNameEx(win32con.NameUserPrincipal).split('@')[0], system_options)
