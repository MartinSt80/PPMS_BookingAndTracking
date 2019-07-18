import time

import datetime
import argparse

from lib import PPMSAPICalls


def transfer_log_to_ppms(log_file):

    def create_tracker_call(start, stop, fac_id, sys_id, user):

        ppms_api_call = PPMSAPICalls.NewCall('PPMS API')
        user_full_name = ppms_api_call.getUserFullName(user)
        user_id = ppms_api_call.getUserID(user_full_name, 2)
        start_time = start.strftime('%Y-%m-%dT%H:%M:00')
        stop_time = stop.strftime('%Y-%m-%dT%H:%M:00')
        current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:00')

        try:
            booking_response = ppms_api_call.makeBooking(start_time, stop_time, current_time, user_id, sys_id, fac_id)
        except Exception as e:
            pass


    # read logfile and remove header line
    with open(log_file, 'r') as f:
        used_time = f.readlines()
    used_time = used_time[1:]

    # parse lines, identify stretches in which time_stamps are <freq> minutes apart --> continuous sessions
    # create a call to the tracker API for each session
    last_datetime = None
    for line in used_time:
        facility_id, system_id, frequency, user_name, time_stamp = line.rstrip('\n').split(', ')
        # print(system_id, system_code, freq, user, time_stamp)
        current_time = time.strptime(time_stamp, '%Y-%m-%dT%H:%M:00')

        # Unpack the first five arguments of time.struct_time for datetime
        current_datetime = datetime.datetime(*current_time[:5])

        # First line, no previous time point
        if last_datetime is None:
            start_datetime = current_datetime
            last_datetime = current_datetime
            continue
        # If timestamps differ by tracker_frequency --> continuous session
        if int((current_datetime - last_datetime).total_seconds()) == int(frequency) * 60:
            last_datetime = current_datetime
            continue
        # Larger steps are breaks in between sessions, report last session, reinitialize
        if start_datetime != last_datetime:
            create_tracker_call(start_datetime, last_datetime, facility_id, system_id, user_name)
        last_datetime = current_datetime
        start_datetime = current_datetime
    # Report the final session
    if start_datetime != last_datetime:
        create_tracker_call(start_datetime, last_datetime, facility_id, system_id, user_name)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description='Read the logfile with the tracked usage, call Tracker API '
                                                          'to transfer them to PPMS.')
    argument_parser.add_argument("log_file_path", type=str, help='Log file tracking the used time on the instrument')
    arguments = argument_parser.parse_args()

    transfer_log_to_ppms(arguments.log_file_path)

