#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import win32api
import win32con

from lib import Options
from lib import PPMSAPICalls


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

		self.URL = SYSTEM_OPTIONS.getValue('tracker_URL')

		self.url = self.URL + '?i=' + self.data['id'] + '&f=' + self.data['freq'] + '&u=' + self.data['user']
		requests.post(self.url, headers=self.header, data=self.data['code'])

def getUserLogin():
	return win32api.GetUserNameEx(win32con.NameUserPrincipal).split('@')[0]

required_keys = ('PPMS_systemid', 'PPMS_systemcode', 'tracker_frequency', 'ignored_logins', 'tracker_URL')
SYSTEM_OPTIONS = Options.OptionReader('SystemOptions.txt')
tracker_call = NewTrackerCall(getUserLogin())
