import time

import datetime
import argparse
from pathlib import Path

from ppms_lib import PPMSAPICalls




class Session:

    session_number = 1

    def __init__(self, start, stop, fac_id, sys_id, user):
        self.start_time = start.strftime('%Y-%m-%dT%H:%M:00')
        self.stop_time = stop.strftime('%Y-%m-%dT%H:%M:00')
        self.session_length_in_min = (stop - start) / datetime.timedelta(minutes=1) + 1
        self.facility_id = fac_id
        self.system_id = sys_id
        self.user_login = user
        self.current_session_number = self.session_number
        Session.session_number += 1
        self.session_info = self._create_session_info()
        self.booking_id = None

    def _create_session_info(self):
        return (f'#{self.current_session_number} {self.user_login} from {self.start_time} to {self.stop_time}: {self.session_length_in_min} min')

    def create_tracker_call(self):
        ppms_api_call = PPMSAPICalls.NewCall('PPMS API')
        user_full_name = ppms_api_call.getUserFullName(self.user_login)
        user_id = ppms_api_call.getUserID(user_full_name, self.facility_id)
        current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:00')

        try:
            booking_response = ppms_api_call.makeBooking(self.start_time,
                                                         self.stop_time,
                                                         current_time,
                                                         user_id,
                                                         self.system_id,
                                                         self.facility_id)
            self.booking_id = booking_response['id']
        except Exception as e:
            print(f'Failed to book session: {self.session_info}')
            print(str(e))
        else:
            print(f'Session {self.booking_id} booked for {self.user_login} from {self.start_time} to {self.stop_time}')

    def print_session_info(self):
        print(self.session_info)
        if self.booking_id:
            print(f'Session booked with id: {self.booking_id}')

    def booking_info_for_stratocore(self):
        return (f'{self.booking_id}, {self.start_time}, {self.stop_time}, {self.session_length_in_min}\n')








    if arguments.call_ppms:
        create_session_overview_for_stratocore()


class LoggedSessions:

    def __init__(self, log_file_path):

        self.log_file_path = log_file_path
        # check if path is a dir --> open all .csv as log files
        if self.log_file_path.is_dir():
            log_file_list = [file_path for file_path in self.log_file_path.glob('*.csv')]
            log_file_list.sort()

        elif self.log_file_path.is_file():
            log_file_list = [self.log_file_path]

        else:
            exit("The log file path is invalid!")

        self.session_list = self._evaluate_log_file(log_file_list)

    def _evaluate_log_file(self, log_file_list):
        session_list = []
        for log_file_path in log_file_list:
            # read logfile and remove header line
            with log_file_path.open() as f:
                used_time = f.readlines()
            used_time = used_time[1:]
            print(f'Evaluating log file {log_file_path.name}')

            # set session counter
            session_counter = len(session_list)

            # parse lines, identify stretches in which time_stamps are <freq> minutes apart --> continuous sessions
            # sessions with 1 min in length are ignored, since the PPMS API needs two different time stamps for booking
            # create a call to the tracker API for each session
            last_datetime = None
            for line in used_time:
                facility_id, system_id, frequency, user_login, time_stamp = line.rstrip('\n').split(', ')
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
                if current_datetime - last_datetime == datetime.timedelta(minutes=int(frequency)):
                    last_datetime = current_datetime
                    continue

                # Larger steps are breaks in between sessions, report last session, reinitialize
                # Check if only a singular login has occured, ignore it
                if start_datetime != last_datetime:
                    ppms_session = Session(start_datetime, last_datetime, facility_id, system_id, user_login)
                    session_list.append(ppms_session)
                    if arguments.call_ppms:
                        ppms_session.create_tracker_call()
                    else:
                        ppms_session.print_session_info()
                last_datetime = current_datetime
                start_datetime = current_datetime

            # Report the final session
            if start_datetime != last_datetime:
                ppms_session = Session(start_datetime, last_datetime, facility_id, system_id, user_login)
                session_list.append(ppms_session)
                if arguments.call_ppms:
                    ppms_session.create_tracker_call()
                else:
                    ppms_session.print_session_info()
            print(f'{len(session_list) - session_counter} sessions have been found.')
            print('---------------------')
        print(f'In total {len(log_file_list)} files with {len(session_list)} sessions have been evaluated.')
        return session_list

    def create_session_overview_for_stratocore(self):

        session_file_name = 'booked_sessions.csv'

        if self.log_file_path.is_dir():
            session_file_path = self.log_file_path / session_file_name
        if self.log_file_path.is_file():
            session_file_path = self.log_file_path.with_name(session_file_name)

        with session_file_path.open(mode='w+') as f:
            f.write("'Booking ref', 'Real start time', 'Real end time', 'Time used(minutes)'\n")
            for session in self.session_list:
                if session.booking_id:
                    f.write(session.booking_info_for_stratocore())


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description='Read the logfile with the tracked usage, call Tracker API '
                                                          'to transfer them to PPMS.')
    argument_parser.add_argument("log_file_path", type=str, help='Log file or directory tracking the used time on the instrument')
    argument_parser.add_argument("--call_ppms", action="store_true", help='If set, data is written to PPMS database.')
    arguments = argument_parser.parse_args()
    log_path = Path(arguments.log_file_path)

    logged_sessions = LoggedSessions(log_path)

    session_list = logged_sessions.session_list