#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import win32api
import win32con

from lib import Options


class NewTrackerCall:

	def __init__(self, login):
		self.id = SYSTEM_OPTIONS.getValue('PPMS_systemid')
		self.code = SYSTEM_OPTIONS.getValue('PPMS_systemcode')
		self.freq = SYSTEM_OPTIONS.getValue('tracker_frequency')
		self.login = login

		if self.login not in SYSTEM_OPTIONS.getValue('ignored_logins').split(','):
			self.data = {
				'id': self.id,
				'freq': self.freq,
				'user': self.login,
				'code': self.code,
				}
			self.sendtoPPMSAPI(self.data)

	def sendtoPPMSAPI(self, parameters):

		self.header = {
			'Content-Type': 'application/x-www-form-urlencoded',
			}
		self.URL = PROXY_OPTIONS.getValue('tracker_URL')

		self.url = self.URL + '?i=' + self.data['id'] + '&f=' + self.data['freq'] + '&u=' + self.data['user']
		requests.post(self.url, headers=self.header, data=self.data['code'])

def getUserLogin():
	return win32api.GetUserNameEx(win32con.NameUserPrincipal).split('@')[0]

required_system_keys = ('PPMS_systemid', 'PPMS_systemcode', 'tracker_frequency', 'ignored_logins')
required_proxy_keys = ('tracker_URL')
try:
	SYSTEM_OPTIONS = Options.OptionReader('SystemOptions.txt', required_system_keys)
	PROXY_OPTIONS = Options.OptionReader('ProxyOptions.txt', required_proxy_keys)
except Exception as e:
	exit(str(e))
else:
	tracker_call = NewTrackerCall(getUserLogin())
