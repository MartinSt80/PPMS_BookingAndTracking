# coding: utf-8

import requests
import time
import os
import math
from tkinter import *
from tkinter import ttk


from ppms_lib import Options, PPMSAPICalls, Errors


# Tracks messages of non-fatal Exceptions
class ErrorLog:

    def __init__(self):
        self.active_errors = False
        self.error_message = ''
        self.valid_user_info = True


# API calls to get full user name and user id from PPMS data base
class UserInfo:

    def __init__(self, login, system_options, error_log):

        self.user_id = None
        self.login = login

        name_call = PPMSAPICalls.NewCall(system_options.getValue('calling_mode'), system_options)
        try:
            self.user_name = name_call.getUserFullName(self.login)
        except Errors.APIError as e:
            self.user_name = {'lname': 'unknown user', 'fname': ''}
            error_log.error_message = 'User name call failed: ' + e.msg
            error_log.valid_user_info = False
            error_log.active_errors = True
        except Errors.FatalError as e:
            exit(e.msg)
        else:
            id_call = PPMSAPICalls.NewCall(system_options.getValue('calling_mode'), system_options)
            try:
                self.user_id = id_call.getUserID(self.user_name, system_options.getValue('PPMS_facilityid'), )
            except Errors.APIError as e:
                error_log.error_message = 'User ID call failed: ' + e.msg
                error_log.valid_user_info = False
                error_log.active_errors = True
            except Errors.FatalError as e:
                exit(e.msg)

            if self.user_name['lname'] == 'BIC':
                self.user_name['fname'] = ''


class PPMS_applet:

    def __init__(self, user_login):

        self.user_login = user_login

        # Initiate the error log
        self.error_log = ErrorLog()

        # Read systems options, and add system name
        self.system_options = self.__readSystemOptions()

        # Retrieve full user name and id from PPMS
        self.user_info = UserInfo(user_login, self.system_options, self.error_log)

        self.root = Tk()
        self.__configureRoot()

        self.__mainframeRefresher()

        self.root.mainloop()

    # Read SystemOptions.txt, add system name
    def __readSystemOptions(self):
        required_keys = (
            'calling_mode', 'PPMS_systemid', 'PPMS_facilityid', 'logo_image', 'image_URL', 'alternate_temp_image')
        try:
            system_options = Options.OptionReader('SystemOptions.txt', required_keys)
        except Errors.FatalError as e:
            exit('Required keys not found in SystemOptions.txt: ' + e.msg)
        else:
            systemname_call = PPMSAPICalls.NewCall(system_options.getValue('calling_mode'), system_options)
            try:
                system_name = systemname_call.getSystemName(system_options.getValue('PPMS_systemid'))
            except (Errors.APIError, Errors.FatalError) as e:
                exit('System name couldn\'t be determined: ' + e.msg)
            else:
                system_options.setValue('PPMS_systemname', system_name)
                return system_options

    # setup the root title, include Bic logo
    def __configureRoot(self):
        self.root.title('Info on your session at the ' + self.system_options.getValue('PPMS_systemname'))
        icon_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 self.system_options.getValue('logo_image'))
        self.root.iconbitmap(default=icon_file)

    # refreshes the mainframe
    def __mainframeRefresher(self, frame=None):


        frame = self.__updateMainframe(frame)
        frame.after(60000, self.__mainframeRefresher, frame)

    # refreshes the mainframe, separate function needed for frame.after in mainframeRefresher()
    def __updateMainframe(self, oldframe=None):
        self.__handleErrors()
        frame = MainFrame(self.root, self.system_options, self.user_info, self.error_log)
        if oldframe is not None:
            oldframe.destroy()
        return frame

    # Error handling: Release old errors
    def __handleErrors(self):
        if self.error_log.active_errors:
            self.error_log.error_message = ''
            self.error_log.active_errors = False

            if not self.error_log.valid_user_info:
                self.user_info = UserInfo(self.user_login, self.system_options, self.error_log)


class MainFrame(ttk.Frame):

    def __init__(self, root, system_options, user_info, error_log):
        super().__init__(root)

        style = ttk.Style()
        style.configure('T.TFrame', background='white')

        self.configure(style='T.TFrame')
        self.grid(column=0, row=0, sticky=(N, W, E, S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        image_frame = ImageFrame(self, system_options)
        image_frame.configure(style='T.TFrame')
        image_frame.grid(column=0, row=0)

        session_frame = SessionFrame(self, system_options, user_info, error_log)
        session_frame.configure(style='T.TFrame')
        session_frame.grid(column=1, row=0)

        communication_frame = CommunicationFrame(self, system_options, user_info, error_log,
                                                 session_frame.start_sessions, session_frame.startsession_users)
        communication_frame.configure(style='T.TFrame')
        communication_frame.grid(column=0, row=1, columnspan=2)


class ImageFrame(ttk.Frame):

    def __init__(self, parent, system_options):

        super().__init__(parent)

        # temperature figure is loaded from PI@BIC or alternate image is used
        self.temperature_image = PhotoImage(file=system_options.getValue('alternate_temp_image'))

        temperature_image_download = requests.get(system_options.getValue('image_URL'))

        if temperature_image_download.status_code == 200:
            self.temperature_image = PhotoImage(data=temperature_image_download.content)

        temp_label = Label(self, image=self.temperature_image, bg='white')
        temp_label.grid(column=0, row=0)


class SessionFrame(ttk.Frame):

    def __init__(self, parent, system_options, user_info, error_log):

        super().__init__(parent)

        self.parent = parent
        self.system_options = system_options
        self.user_info = user_info
        self.error_log = error_log

        self.session_subframes = self.__createSessionSubframes()
        self.start_sessions, self.startsession_users = self.__createSessions()

    # creates the single Session subframes for the hour labels and the session indicators or booking buttons
    def __createSessionSubframes(self):

        session_subframes = []
        for i in range(8):
            subframe = ttk.Frame(self, height=50, width=130, borderwidth='2')
            subframe.grid(column=0, row=i)
            session_subframes.append(subframe)
            textframe = ttk.Frame(self, height=50, width=70, borderwidth='2')
            textframe.grid(column=1, row=i)
            textcanvas = Canvas(textframe, width=70, height=50, highlightthickness='0',
                                borderwidth='0', background='white')
            textcanvas.grid()
            # textcanvas.create_rectangle(0, 0, 70, 50, outline='red', width='1')
            textcanvas.create_text(10, 24, anchor=W,
                                   text=str(Times.getFirstHour() + i) + ' - ' + str(Times.getFirstHour() + i + 1),
                                   font=("Calibri", 12))
        return session_subframes

    # creates the session indicator or booking buttons in each session frame
    def __createSessions(self):

        class NoBookedSessionError(Exception):
            pass

        def __fuseSuccessiveSessions(bookedhours, users):
            if len(bookedhours) > 0:
                session_list = sorted(zip(bookedhours, users))
                old_start, old_stop, old_user = None, None, None
                fused_sessions = []

                for session in session_list:
                    if len(session[0]) == 0:
                        continue
                    if old_user is not None:
                        temp_start, temp_stop, temp_user = session[0][0], session[0][-1], session[1]

                        if old_user == temp_user and old_stop + 1 == temp_start:
                            old_stop = temp_stop
                        else:
                            fused_sessions.append((range(old_start, old_stop + 1), old_user))
                            old_start, old_stop, old_user = session[0][0], session[0][-1], session[1]

                    else:
                        old_start, old_stop, old_user = session[0][0], session[0][-1], session[1]
                fused_sessions.append((range(old_start, old_stop + 1), old_user))
                return fused_sessions

            raise NoBookedSessionError

        def __sessioninProgress(booked_hours):
            booked_hours = [n - Times.getFirstHour() for n in booked_hours]
            negative_zero_present = False
            positive_present = False

            for n in booked_hours:
                if n < 0:
                    negative_zero_present = True
                if n >= 0:
                    positive_present = True
            return negative_zero_present and positive_present

        def __bookThisSession(clicked_button):

            def __bookIt():
                booking_call = PPMSAPICalls.NewCall(self.system_options.getValue('calling_mode'), self.system_options)
                try:
                    booking_call.makeBooking(booking_start, booking_stop, booking_time, self.user_info.user_id,
                                             self.system_options.getValue('PPMS_systemid'),
                                             self.system_options.getValue('PPMS_facilityid'))
                except Errors.APIError as e:
                    self.error_log.error_message = 'Session booking failed: ' + e.msg
                    self.error_log.active_errors = True
                else:
                    self.destroy()
                    new_sessionframe = SessionFrame(self.parent, self.system_options, self.user_info, self.error_log)
                    new_sessionframe.configure(style='T.TFrame')
                    new_sessionframe.grid(column=1, row=0)
                finally:
                    confirmation_window.destroy()

            def __cancelIt():
                confirmation_window.destroy()

            # if user login is not known, no booking is possible
            if self.user_info.user_id is None:
                return

            # find the start hour for the clicked button
            for button in button_list:
                if button[0] == clicked_button:
                    booking_start = button[1] + Times.getFirstHour()
                    break
            else:
                return

            todays_date = time.strftime('%Y-%m-%dT', time.localtime())
            booking_stop = todays_date + str(booking_start + 1) + ':00:00'
            booking_start = todays_date + str(booking_start) + ':00:00'
            booking_time = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime())

            confirmation_window = Toplevel()
            confirmation_window.title('Confirm your booking')
            confirmation_window.configure(background='white')
            booking_message = 'You are about to book a session from ' + booking_start[
                                                                        11:16] + ' to ' + booking_stop[
                                                                                          11:16] + '.'
            msg = ttk.Label(confirmation_window, text=booking_message, font=("Calibri", 12), anchor='w',
                            background='white', borderwidth='0', padding=(10, 10, 10, 10))
            msg.grid(row=0, column=0)
            buttons = ttk.Frame(confirmation_window, padding=6, style='T.TFrame')
            buttons.grid(row=1, column=0)
            ok_button = Button(buttons, text="Confirm", font=("Calibri", 12),
                               padx=2, command=__bookIt)
            ok_button.grid(row=0, column=0)
            cancel_button = Button(buttons, text="Cancel", font=("Calibri", 12),
                                   padx=2, command=__cancelIt)
            cancel_button.grid(row=0, column=1)

        booked_hours = []
        users = []

        todays_sessions_call = PPMSAPICalls.NewCall(self.system_options.getValue('calling_mode'), self.system_options)

        try:
            todays_sessions = todays_sessions_call.getTodaysBookings(
                self.system_options.getValue('PPMS_facilityid'), self.system_options.getValue('PPMS_systemname'))
        except Errors.APIError as e:
            self.error_log.error_message = 'Retrieving booking information failed: ' + e.msg
            self.error_log.active_errors = True
        else:
            for session in todays_sessions:
                booked_hours.append((range(session['start'], session['stop'])))
                users.append(session['user'])

        booked_sessions = []
        start_sessions = []
        start_sessions_users = []
        try:
            fused_sessions = __fuseSuccessiveSessions(booked_hours, users)
        except NoBookedSessionError:
            pass
        else:
            for single_bookings, user in fused_sessions:
                if __sessioninProgress(single_bookings):
                    start_sessions.append(0)
                    start_sessions_users.append(user)
                else:
                    start_sessions.append(single_bookings[0] - Times.getFirstHour())
                    start_sessions_users.append(user)
                for hours in single_bookings:
                    booked_sessions.append(hours - Times.getFirstHour())

        button_list = []
        if not self.error_log.active_errors:
            button_state = 'normal'
        else:
            button_state = 'disabled'
        for i in range(8):
            try:
                booked_sessions.index(i)
                sessioncanvas = Canvas(self.session_subframes[i], width=130, height=50, highlightthickness='0',
                                       borderwidth='0', background='#32ad3e')
                # sessioncanvas.create_rectangle(0, 0, 130, 50, outline='red', width='1')
                if math.floor(Times.getCurrentTime() - Times.getFirstHour()) == i:
                    sessioncanvas.create_line(0, int(45 * (Times.getCurrentTime() - math.floor(Times.getCurrentTime()))),
                                              130, int(45 * (Times.getCurrentTime() - math.floor(Times.getCurrentTime()))),
                                              fill='blue', width='2.0')
                sessioncanvas.grid()
                try:
                    session_index = start_sessions.index(i)
                    sessioncanvas.create_text(65, 23, text=start_sessions_users[session_index],
                                              font=("Calibri", 12))
                except ValueError:
                    pass
            except ValueError:
                booking_button = Button(self.session_subframes[i], text="Book this session", font=("Calibri", 12),
                                        padx=2, pady=6, background='#ffda26', state=button_state)
                booking_button.config(command=lambda button=booking_button: __bookThisSession(button))
                booking_button.grid(sticky=(W))
                button_list.append((booking_button, i))
        return start_sessions, start_sessions_users


class CommunicationFrame(ttk.Frame):

    def __init__(self, parent, system_options, user_info, error_log, start_sessions, startsession_users):

        super().__init__(parent)

        self.parent = parent
        self.system_options = system_options
        self.user_info = user_info
        self.error_log = error_log

        if self.error_log.active_errors:
            logged_error = ttk.Label(self, text=self.error_log.error_message, font=("Calibri", 12),
                                     width=126, anchor='w',
                                     background='#ffb3b3', borderwidth='0')
            logged_error.grid(column=0, row=0)

        else:
            greeting = ttk.Label(self, text=self.__greetingText(), font=("Calibri", 12), width=126,
                                 anchor='w',
                                 background='#edffee', borderwidth='0')
            greeting.grid(column=0, row=0)

            shutdown = ttk.Label(self,
                                 text=self.__shutdownOptions(*self.__nextSession(start_sessions, startsession_users)),
                                 width=126, anchor='w', font=("Calibri", 12), background='#edffee')
            shutdown.grid(column=0, row=1)

    def __timeofDay(self, time):
        if time < 12:
            return 'Good morning '
        if time < 18:
            return 'Good afternoon '
        if time < 24:
            return 'Good evening '

    def __nextSession(self, start_sessions, users):
        elapsed_time = Times.getCurrentTime() - Times.getFirstHour()
        for i in range(len(start_sessions)):
            if start_sessions[i] > elapsed_time:
                return users[i], int((start_sessions[i] + Times.getFirstHour() - Times.getCurrentTime()) * 60)

        return None, None

    def __shutdownOptions(self, name, minutes):
        # if now future booking, or next session is only tomorrow
        if minutes == None:
            return 'You are the last user for today, please make sure to switch off the microscope!'

        # Info about next session, if the session is more than 90 minutes in the future, switch off
        snippet = 'The session of ' + name + ' will start in ' + str(minutes) + ' minute'

        if 1 == minutes:
            snippet = snippet + '. '
        else:
            snippet = snippet + 's. '

        if minutes < 90:
            return snippet + 'Please leave everything switched on!'
        return snippet + 'Please switch the lasers and the UV-lamp off!'

    def __greetingText(self):
        exp_call = PPMSAPICalls.NewCall(self.system_options.getValue('calling_mode'), self.system_options)
        try:
            exp_value = int(
                exp_call.getExperience(self.user_info.login, self.system_options.getValue('PPMS_systemid')))
        except Errors.APIError as e:
            if e.empty_response:
                exp_value = 0
            else:
                exp_value = 'some'

        greeting_text = self.__timeofDay(Times.getCurrentHour()) + self.user_info.user_name[
            'fname'] + '! Welcome back at the ' + self.system_options.getValue('PPMS_systemname') + \
                        ' on which you have already worked for ' + str(exp_value)
        if exp_value == 1:
            greeting_text += ' hour.'
        else:
            greeting_text += ' hours.'

        return greeting_text


class Times:

    # get the times, make sure schedule starts with earliest 7 and ends latest 24
    @staticmethod
    def getCurrentTime():
        current_time = time.strftime('%H %M', time.localtime()).split()
        current_hour = int(current_time[0])
        return current_hour + float(current_time[1]) / 60

    @staticmethod
    def getCurrentHour():
        current_time = time.strftime('%H %M', time.localtime()).split()
        return int(current_time[0])

    @staticmethod
    def getFirstHour():
        current_hour = Times.getCurrentHour()
        if current_hour > 16:
            first_hour = 16
        elif current_hour < 8:
            first_hour = 7
        else:
            first_hour = current_hour
            return first_hour


if __name__ == "__main__":
    user_login = 'martin.stoeckl'
    PPMS_applet(user_login)
