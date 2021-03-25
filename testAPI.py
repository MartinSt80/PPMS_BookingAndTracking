#!/usr/bin/env python
# -*- coding: utf-8

import datetime

from lib import Options, PPMSAPICalls, Errors

SYSTEM_OPTIONS = Options.OptionReader('SystemOptions.txt')

facility_id = SYSTEM_OPTIONS.getValue('PPMS_facilityid')
system_id = SYSTEM_OPTIONS.getValue('PPMS_systemid')
calling_mode = SYSTEM_OPTIONS.getValue('calling_mode')

get_systemname = PPMSAPICalls.NewCall(calling_mode)
try:
	system_name = get_systemname.getSystemName(system_id)
	print(system_name)
except Errors.APIError as e:
	print(e.msg)

get_booking = PPMSAPICalls.NewCall(calling_mode)
print(get_booking.getTodaysBookings(facility_id, system_name))

get_username = PPMSAPICalls.NewCall(calling_mode)
user_name = get_username.getUserFullName('martin.stoeckl')
print(user_name)

test_date = datetime.date(2019, 8, 25)

for _ in range(10):
	print(test_date)
	get_systembookings = PPMSAPICalls.NewCall(calling_mode)
	system_bookings = get_systembookings.getSystemBookings(facility_id, test_date)

	for booking in system_bookings:
		print(booking)
	test_date += datetime.timedelta(days=1)


exit()



get_userexp = PPMSAPICalls.NewCall(calling_mode)
try:
	print( get_userexp.getExperience('martin.stoeckl', system_id))
except Errors.APIError as e:
	print(e.msg)

get_userid = PPMSAPICalls.NewCall(calling_mode)
user_id = get_userid.getUserID(user_name, facility_id)
print(user_id)

make_booking = PPMSAPICalls.NewCall(calling_mode)

try:
	print(make_booking.makeBooking('2018-01-29T18:00:00', '2018-01-29T20:00:00', '2018-01-29T15:00:00', user_id, system_id, facility_id))
except Errors.APIError as e:
	print(e.msg)


# get_groups = PPMSAPICalls.NewCall(calling_mode)
# grouplist = get_groups.getGroupList()
# for group in grouplist:
# 	get_group = PPMSAPICalls.NewCall(calling_mode)
# 	print get_group.getGroupPI(group)
# 	get_user = PPMSAPICalls.NewCall(calling_mode)
# 	users = get_group.getGroupUsers(group)
# 	print users
