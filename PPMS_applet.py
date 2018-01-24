# coding: utf-8

import requests
from StringIO import StringIO
import time
import os
import psutil
import math
from Tkinter import *
import ttk
from PIL import Image, ImageTk

from lib import Options, PPMSAPICalls, Errors



# API calls to get full user name and user id from PPMS data base
class UserInfo:

	def __init__(self, facility_id):
		for self.p in psutil.process_iter():
			if 'explorer.exe' == self.p.name():
				self.login = self.p.username().split('\\')[1]
				break
		else:
			raise NameError('Login could not be determined; No owner of process: explorer.exe')
		self.login = 'martin.stoeckl' 												#TODO: remove
		name_call = PPMSAPICalls.NewCall(SYSTEM_OPTIONS.getValue('calling_mode'))

		try:
			self.user_name = name_call.getUserFullName(self.login)
			id_call = PPMSAPICalls.NewCall(SYSTEM_OPTIONS.getValue('calling_mode'))
			self.user_id = id_call.getUserID(self.user_name, facility_id)
			if self.user_name['lname'] == 'BIC':
				self.user_name['fname'] = ''
		except Errors.APIError:
			self.user_name = ('unknown user', '')
			self.user_id = None


# wrapper function, read options, get Info on User, start Tk, refresh the Mainframe
def runIt():

	global SYSTEM_OPTIONS

	SYSTEM_OPTIONS = Options.OptionReader('SystemOptions.txt')
	systemname_call = PPMSAPICalls.NewCall(SYSTEM_OPTIONS.getValue('calling_mode'))
	SYSTEM_OPTIONS.setValue('PPMS_systemname', systemname_call.getSystemName(SYSTEM_OPTIONS.getValue('PPMS_systemid')))

	global USERINFO
	USERINFO = UserInfo(SYSTEM_OPTIONS.getValue('PPMS_facilityid'))

	global root
	root = Tk()

	configureRoot()
	mainframeRefresher()
	root.mainloop()

# setup the root title, include Bic logo
def configureRoot():

	root.title('Info on your session at the ' + SYSTEM_OPTIONS.getValue('PPMS_systemname'))
	icon_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), SYSTEM_OPTIONS.getValue('logo_image'))
	root.iconbitmap(default=icon_file)

# refreshes the mainframe, own function needed for frame.after in mainframeRefresher()
def updateMainframe(oldframe=None):
	# try to create the Applet content, if an error occurs (network connection is lost, ...) do not update
	frame = createMainFrame()

	if oldframe is not None:
		oldframe.destroy()
	return frame


def mainframeRefresher(frame=None):

	frame = updateMainframe(frame)

	# if no mainframe could be created at start, exit
	if frame is None:
		quit()
	frame.after(60000, mainframeRefresher, frame)

# creates the content of the Applet
def createMainFrame():

	# get the times, make sure schedule starts with 7 and ends 24
	def calculateTimes():
		current_time = time.strftime('%H %M', time.localtime()).split()
		current_hour = int(current_time[0])
		current_time = current_hour + float(current_time[1]) / 60
		if current_hour > 16:
			first_hour = 16
		elif current_hour < 8:
			first_hour = 7
		else:
			first_hour = current_hour
		return current_time, current_hour, first_hour


	# creates the content in the Image frame, temperature figure is loaded from PI@BIC
	def createImageFrame(parent):

		imageframe = ttk.Frame(parent)
		open_temperature_image = requests.get(SYSTEM_OPTIONS.getValue('image_URL'))
		raw_temperature_image = Image.open(StringIO(open_temperature_image.content))
		open_temperature_image.close()
		temperature_image = ImageTk.PhotoImage(raw_temperature_image)
		temp_label = Label(imageframe, image=temperature_image, bg='white')
		temp_label.image = temperature_image
		temp_label.grid(column=0, row=0)
		return imageframe


	def createSessionandCommunication(mainframe):

		# creates the Session frame
		def createSessionFrame(mainframe):

			# creates the single Session subframes for the hour labels and the session indicators or booking buttons
			def createSessionSubframes(sessionframe):
				session_subframes = []
				for i in range(8):
					subframe = ttk.Frame(sessionframe, height=50, width=130, borderwidth='2')
					subframe.grid(column=0, row=i)
					session_subframes.append(subframe)
					textframe = ttk.Frame(sessionframe, height=50, width=70, borderwidth='2')
					textframe.grid(column=1, row=i)
					textcanvas = Canvas(textframe, width=70, height=50, highlightthickness='0',
										borderwidth='0', background='white')
					textcanvas.grid()
					#textcanvas.create_rectangle(0, 0, 70, 50, outline='red', width='1')
					textcanvas.create_text(10, 24, anchor=W, text=str(first_hour + i) + ' - ' + str(first_hour + i + 1),
										   font=("Calibri", 12))
				return session_subframes

			# creates the session indicator or booking buttons in each session frame
			def createSessions(session_frames, session_frame):

				class NoBookedSessionError(Exception):
					pass

				def fuseSuccessiveSessions(bookedhours, users):
					if len(bookedhours) > 0:
						session_list = sorted(zip(bookedhours, users))
						old_start, old_stop, old_user = None, None, None
						fused_sessions = []
						for session in session_list:
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

				def sessioninProgress(booked_hours):
					booked_hours = [n - first_hour for n in booked_hours]
					negative_zero_present = False
					positive_present = False

					for n in booked_hours:
						if n < 0:
							negative_zero_present = True
						if n >= 0:
							positive_present = True
					return negative_zero_present and positive_present

				def bookThisSession(clicked_button):

					def bookIt():
						booking_call = PPMSAPICalls.NewCall(SYSTEM_OPTIONS.getValue('calling_mode'))
						booking_call.makeBooking(booking_start, booking_stop, booking_time, USERINFO.user_id, SYSTEM_OPTIONS.getValue('PPMS_systemid'), SYSTEM_OPTIONS.getValue('PPMS_facilityid'))
						session_frame.destroy()
						createSessionandCommunication(mainframe)
						confirmation_window.destroy()

					def cancelIt():
						confirmation_window.destroy()

					# if user login is not known, no booking is possible
					if USERINFO.user_id is None:
						return

					#find the start hour for the clicked button
					for button in button_list:
						if button[0] == clicked_button:
							booking_start = button[1] + first_hour
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
					booking_message = 'You are about to book a session from ' + booking_start[11:16] + ' to ' + booking_stop[11:16] + '.'
					msg = ttk.Label(confirmation_window, text=booking_message, font=("Calibri", 12), anchor='w',
								 background='white', borderwidth='0', padding=(10, 10, 10, 10))
					msg.grid(row=0, column=0)
					buttons = ttk.Frame(confirmation_window, padding=6, style='T.TFrame')
					buttons.grid(row=1, column=0)
					ok_button = Button(buttons, text="Confirm", font=("Calibri", 12),
												padx=2, command=bookIt)
					ok_button.grid(row=0, column=0)
					cancel_button = Button(buttons, text="Cancel", font=("Calibri", 12),
												padx=2, command=cancelIt)
					cancel_button.grid(row=0, column=1)


				booked_hours = []
				users = []
				new_call = PPMSAPICalls.NewCall(SYSTEM_OPTIONS.getValue('calling_mode'))
				for session in new_call.getTodaysBookings(SYSTEM_OPTIONS.getValue('PPMS_facilityid'), SYSTEM_OPTIONS.getValue('PPMS_systemname')):
					booked_hours.append((range(session['start'], session['stop'])))
					users.append(session['user'])

				booked_sessions = []
				start_sessions = []
				start_sessions_users = []
				try:
					fused_sessions = fuseSuccessiveSessions(booked_hours, users)
					for single_bookings, user in fused_sessions:
						if sessioninProgress(single_bookings):
							start_sessions.append(0)
							start_sessions_users.append(user)
						else:
							start_sessions.append(single_bookings[0] - first_hour)
							start_sessions_users.append(user)
						for hours in single_bookings:
							booked_sessions.append(hours - first_hour)
				except NoBookedSessionError:
					pass

				button_list = []
				for i in range(8):
					try:
						booked_sessions.index(i)
						sessioncanvas = Canvas(session_frames[i], width=130, height=50, highlightthickness='0',
											   borderwidth='0', background='#32ad3e')
						#sessioncanvas.create_rectangle(0, 0, 130, 50, outline='red', width='1')
						if math.floor(current_time - first_hour) == i:
							sessioncanvas.create_line(0, int(45 * (current_time - math.floor(current_time))),
													  130, int(45 * (current_time - math.floor(current_time))),
													  fill='blue', width='2.0')
						sessioncanvas.grid()
						try:
							session_index = start_sessions.index(i)
							sessioncanvas.create_text(65, 23, text=start_sessions_users[session_index],
													  font=("Calibri", 12))
						except ValueError:
							pass
					except ValueError:
						booking_button = Button(session_frames[i], text="Book this session", font=("Calibri", 12),
												padx=2, pady=6, background='#ffda26')
						booking_button.config(command=lambda button=booking_button: bookThisSession(button))
						booking_button.grid(sticky=(W))
						button_list.append((booking_button, i))
				return start_sessions, start_sessions_users


			sessionframe = ttk.Frame(mainframe, style='T.TFrame')
			session_subframes = createSessionSubframes(sessionframe)
			start_sessions, startsession_users = createSessions(session_subframes, sessionframe)
			return sessionframe, start_sessions, startsession_users


		# creates the greeting content in the communication frame
		def createCommunication(parent_frame, start_sessions, startsession_users):

			def timeofDay(time):
				if time < 12:
					return 'Good morning '
				if time < 18:
					return 'Good afternoon '
				if time < 24:
					return 'Good evening '

			def nextSession(start_sessions, users):
				elapsed_time = current_time - first_hour
				for i in range(len(start_sessions)):
					if start_sessions[i] > elapsed_time:
						return users[i], int((start_sessions[i] + first_hour - current_time) * 60)
				return (None, None)

			def shutdownOptions(name, minutes):
				# if now future booking, or next session is only tomorrow
				if  minutes == None:
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

			exp_call = PPMSAPICalls.NewCall(SYSTEM_OPTIONS.getValue('calling_mode'))
			exp_value = int(exp_call.getExperience(USERINFO.login, SYSTEM_OPTIONS.getValue('PPMS_systemid')))
			greeting_text = timeofDay(current_hour) + USERINFO.user_name['fname'] + '! Welcome back at the ' + SYSTEM_OPTIONS.getValue('PPMS_systemname') + \
				' on which you have already worked for ' + str(exp_value)
			if exp_value == 1:
				greeting_text += ' hour.'
			else:
				greeting_text += ' hours.'

			greeting = ttk.Label(parent_frame, text=greeting_text, font=("Calibri", 12), width=126, anchor='w',
								 background='#edffee', borderwidth='0')
			greeting.grid(column=0, row=0)
			shutdown = ttk.Label(parent_frame, text=shutdownOptions(*nextSession(start_sessions, startsession_users)),
								 width=126, anchor='w', font=("Calibri", 12), background='#edffee')
			shutdown.grid(column=0, row=1)


		sessionframe, start_sessions, startsession_users = createSessionFrame(mainframe)
		sessionframe.configure(style='T.TFrame')
		sessionframe.grid(column=1, row=0)

		communication_frame = ttk.Frame(mainframe, style='T.TFrame')
		communication_frame.grid(column=0, row=1, columnspan=2)
		createCommunication(communication_frame, start_sessions, startsession_users)


	current_time, current_hour, first_hour = calculateTimes()

	session_style = ttk.Style()
	session_style.configure('T.TFrame', background='white')

	mainframe = ttk.Frame(root, style='T.TFrame')
	mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
	mainframe.columnconfigure(0, weight=1)
	mainframe.rowconfigure(0, weight=1)

	imageframe = createImageFrame(mainframe)
	imageframe.configure(style='T.TFrame')
	imageframe.grid(column=0, row=0)

	createSessionandCommunication(mainframe)

	return mainframe

if __name__ == "__main__":
	runIt()
