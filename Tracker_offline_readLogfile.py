import time

import datetime
import argparse
from pathlib import Path

from ppms_lib import PPMSAPICalls


class Session:

    session_number = 1

    def __init__(self, start, stop, fac_id, sys_id, sys_name, user):
        self.start_time = start.strftime('%Y-%m-%dT%H:%M:00')
        self.stop_time = stop.strftime('%Y-%m-%dT%H:%M:00')
        self.session_length_in_min = (stop - start) / datetime.timedelta(minutes=1) + 1
        self.facility_id = fac_id
        self.system_id = sys_id
        self.system_name = sys_name
        self.user_login = user
        self.booking_id = None

        # Enumerate each session created
        self.current_session_number = self.session_number
        Session.session_number += 1

    def get_session_info(self):

        if self.booking_id:
            return f'#{self.current_session_number} {self.user_login} from {self.start_time} to {self.stop_time}: {self.session_length_in_min} min. Linked booked session id: {self.booking_id}'
        return f'#{self.current_session_number} {self.user_login} from {self.start_time} to {self.stop_time}: {self.session_length_in_min} min'

    def booking_info_for_stratocore(self):
        return (f'{self.booking_id}, {self.start_time}, {self.stop_time}, {self.session_length_in_min}\n')

class LoggedSessions:

    def __init__(self, log_file_path):

        session_file_name = 'booked_sessions.csv'
        self.log_file_path = log_file_path

        # check if path is a dir --> open all .csv as log files
        if self.log_file_path.is_dir():
            log_file_list = [file_path for file_path in self.log_file_path.glob('*.csv')]
            log_file_list.sort()
            self.session_file_path = self.log_file_path / session_file_name

        elif self.log_file_path.is_file():
            log_file_list = [self.log_file_path]
            self.session_file_path = self.log_file_path.with_name(session_file_name)

        else:
            exit("The log file path is invalid!")


        # Generate the list of session from the log file list and store the facility parameters
        self.session_list, self.system_parameters = self._evaluate_log_file_list(log_file_list)

    def _evaluate_log_file_list(self, log_file_list):

        session_list = []

        # Retrieve the facility_id, system id, get the instrument name from PPMS
        with log_file_list[0].open() as f:
            first_log_file = f.readlines()

        facility_id, system_id, _, _, _ = first_log_file[1].rstrip('\n').split(', ')
        system_name = PPMSAPICalls.NewCall('PPMS API').getSystemName(system_id)

        system_parameters = {'facility_id': facility_id,
                             'system_id': system_id,
                             'system_name': system_name,
                             }

        for log_file_path in log_file_list:

            # read logfile and remove header line
            with log_file_path.open() as f:
                used_time = f.readlines()
            used_time = used_time[1:]
            print(f'Evaluating log file {log_file_path.name}')

            # Reset the session counter
            session_counter = len(session_list)

            # parse lines, identify stretches in which time_stamps are <freq> minutes apart --> continuous sessions
            # sessions with 1 min in length are ignored, since the PPMS API needs two different time stamps for booking
            # create a call to the tracker API for each session
            last_datetime = None
            for line in used_time:

                facility_id, system_id, frequency, user_login, time_stamp = line.rstrip('\n').split(', ')
                current_datetime = datetime.datetime.strptime(time_stamp, '%Y-%m-%dT%H:%M:00')

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
                    ppms_session = Session(start_datetime, last_datetime, facility_id, system_id, system_name, user_login)
                    session_list.append(ppms_session)
                    print(ppms_session.get_session_info())
                last_datetime = current_datetime
                start_datetime = current_datetime

            # Report the final session
            if start_datetime != last_datetime:
                ppms_session = Session(start_datetime, last_datetime, facility_id, system_id, system_name, user_login)
                session_list.append(ppms_session)
                print(ppms_session.get_session_info())
            print(f'{len(session_list) - session_counter} sessions have been found.')
            print('---------------------')

        print(f'In total {len(log_file_list)} files with {len(session_list)} sessions have been evaluated.')
        return session_list, system_parameters



    def create_session_overview_for_stratocore(self):

         with self.session_file_path.open(mode='w+') as f:
            f.write("'Booking ref', 'Real start time', 'Real end time', 'Time used(minutes)'\n")
            for session in self.session_list:
                if session.booking_id:
                    f.write(session.booking_info_for_stratocore())

    def log_used_time(self):


        current_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:00')

        for used_session in self.session_list:

            # Try to book the session, succeeds if there is noc conflicting session (e.g. User has not used PPMS to book the session
            try:
                user_full_name = PPMSAPICalls.NewCall('PPMS API').getUserFullName(used_session.user_login)
                user_id = PPMSAPICalls.NewCall('PPMS API').getUserID(user_full_name, used_session.facility_id)

                booking_response = PPMSAPICalls.NewCall('PPMS API').makeBooking(used_session.start_time,
                                                             used_session.stop_time,
                                                             current_time,
                                                             user_id,
                                                             used_session.system_id,
                                                             used_session.facility_id)
                self.booking_id = booking_response['id']
            except Exception as e:
                print(f'Failed to book session: {self.session_info}')
                try:
                    pass
                except Exception as e:
                    print(e.msg)
            else:
                print(f'Session {self.booking_id} booked for {self.user_login} from {self.start_time} to {self.stop_time}')


class CachedBookedSessions:

    def __int__(self, ):

        self.cached_day_list = []
        self.cached_session_list = []

        self.ppms_call = PPMSAPICalls.NewCall('PPMS API')


    def getSessionsofDay(self, day: datetime.date) -> list:
        try:
            day_index = self.cached_day_list.index(day)
        except IndexError:
            self.cached_day_list.append(day)
            self.cached_session_list.append(self.ppms_call.getBookedSessionsPeriod())


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description='Read the logfile with the tracked usage, call Tracker API '
                                                          'to transfer them to PPMS.')
    argument_parser.add_argument("log_file_path", type=str, help='Log file or directory tracking the used time on the instrument')
    argument_parser.add_argument("--call_ppms", action="store_true", help='If set, data is written to PPMS database.')
    arguments = argument_parser.parse_args()

    # bookings = PPMSAPICalls.NewCall('PPMS API').getBookedSessionsPeriod('2', datetime.date(2020, 6, 1), datetime.date(2020, 7, 31))
    # # 'Instrument': 'L930 - Zeiss LSM 880'
    # lsm880_bookings = [b for b in bookings if b['Instrument'] == 'L930 - Zeiss LSM 880']
    # for lsm880 in lsm880_bookings:
    #     print(lsm880)
    #
    # print(PPMSAPICalls.NewCall('PPMS API').setSessionTimeUsed('95', '2', '59509', '35'))


    # bookings2 = PPMSAPICalls.NewCall('PPMS API').getTodaysBookings(2, filter=False, day='2021-07-07')
    # for b in bookings2:
    #     print(b)


    logged_sessions = LoggedSessions(Path(arguments.log_file_path))


    # for session in logged_sessions.session_list:
    #     print(session.booking_info_for_stratocore())
    #     if arguments.call_ppms:
    #         session.create_tracker_call()