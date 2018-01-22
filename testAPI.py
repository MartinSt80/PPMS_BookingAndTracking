#!/usr/bin/env python
# -*- coding: utf-8

from lib import Options, PPMSAPICalls

SYSTEM_OPTIONS = Options.OptionReader('SystemOptions.txt')

facility_id = SYSTEM_OPTIONS.getValue('PPMS_facilityid')
system_id = SYSTEM_OPTIONS.getValue('PPMS_systemid')
calling_mode = SYSTEM_OPTIONS.getValue('calling_mode')

get_systemname = PPMSAPICalls.NewCall(calling_mode)
system_name = get_systemname.getSystemName(system_id)
print system_name

get_booking = PPMSAPICalls.NewCall(calling_mode)
print get_booking.getTodaysBookings(facility_id, system_name)

get_username = PPMSAPICalls.NewCall(calling_mode)
user_name = get_username.getUserFullName('martin.stoeckl')
print user_name

get_userexp = PPMSAPICalls.NewCall(calling_mode)
print get_userexp.getExperience('martin.stoeckl', system_id)

get_userid = PPMSAPICalls.NewCall(calling_mode)
user_id = get_userid.getUserID(user_name, facility_id)
print user_id

# make_booking = PPMSAPICalls.NewCall(calling_mode)
# make_booking.makeBooking('2017-08-22T18:00:00', '2017-08-22T20:00:00', '2017-08-04T17:00:00', user_id, system_id, facility_id)

get_groups = PPMSAPICalls.NewCall(calling_mode)
grouplist = get_groups.getGroupList()
for group in grouplist:
	get_group = PPMSAPICalls.NewCall(calling_mode)
	print get_group.getGroupPI(group)
	get_user = PPMSAPICalls.NewCall(calling_mode)
	users = get_group.getGroupUsers(group)
	print users



