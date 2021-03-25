#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib import Options, TrackerCall

required_keys = ('PPMS_systemid', 'PPMS_systemcode', 'tracker_frequency', 'ignored_logins', 'proxy_address', 'tracker_port', 'user_login')

try:
	system_options = Options.OptionReader('SystemOptions.txt', required_keys)
except Exception as e:
	exit(str(e))

TrackerCall.NewTrackeroverProxy(system_options.getValue('user_login'), system_options)

