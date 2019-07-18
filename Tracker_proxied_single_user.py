#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import socket

from lib import Options


class NewTrackeroverProxy:

	def __init__(self, login):
		self.id = SYSTEM_OPTIONS.getValue('PPMS_systemid')
		self.code = SYSTEM_OPTIONS.getValue('PPMS_systemcode')
		self.freq = SYSTEM_OPTIONS.getValue('tracker_frequency')
		self.login = login

		if self.login not in SYSTEM_OPTIONS.getValue('ignored_logins').split(','):
			self.tracker_parameters = self.createTrackerCallDict()
			self.sendtoTracker(self.tracker_parameters)

	# dict is pickled and sent to proxy
	def	sendtoTracker(self, param_dict):
		self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.proxy_socket.connect((SYSTEM_OPTIONS.getValue('proxy_address'), int(SYSTEM_OPTIONS.getValue('tracker_port'))))
		pickled_dict = pickle.dumps(param_dict)
		self.proxy_socket.sendall(pickled_dict)
		self.proxy_socket.close()

	def createTrackerCallDict(self):
		parameters = {
			'id': self.id,
			'freq': self.freq,
			'user': self.login,
			'code': self.code,
		}

		return parameters


required_keys = ('PPMS_systemid', 'PPMS_systemcode', 'tracker_frequency', 'ignored_logins', 'proxy_address', 'tracker_port', 'user_login')
SYSTEM_OPTIONS = Options.OptionReader('SystemOptions.txt')
NewTrackeroverProxy(SYSTEM_OPTIONS.getValue('user_login'))