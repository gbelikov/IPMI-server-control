import os, re, time, subprocess as subp

class server_ipmi(object):

	def __init__(self, IPMI_server_IP, IPMI_username, IPMI_password):
		#instance-wide variables
		self.IPMI_server_IP = IPMI_server_IP
		self.IPMI_username = IPMI_username
		self.IPMI_password = IPMI_password
		self.query_results = ''


	def useIPMI(self, IPMI_command):
		''' Executes IPMI commands.

			Checks if there is an error in a command and prints both.
			If there are errors/exceptions returns None.
			If not returns output of the query (if there is one).
			'''
		try:
			execute_command = ("ipmitool -I lanplus -H {} -U {} -P {} {}"
						.format(self.IPMI_server_IP, self.IPMI_username, self.IPMI_password, IPMI_command))
			subp.check_output(execute_command, shell=True, stderr=subp.STDOUT)
		except subp.CalledProcessError as e:
				print ("something is wrong here: \n")
				print ("the error is: \n {} \n".format(e.output))
				print ("the text of exception is: \n {}".format(e))
				results = None
		except:
				print ("unexpected exception occured")
				results = None
		else:
				results = subp.Popen(execute_command, shell=True, stdout=subp.PIPE).stdout.readlines()
				if results[1].find('no reading') != -1:
					results = None
		return results

	def getIPMIdata(self):
		'''This one returns ambient temperature, fan speeds, and power consumpion.

		Other functions use it's output.
		'''
		IPMI_command = " sdr | grep -i 'ambient \| rpm \| watts'"
		self.query_results = self.useIPMI(IPMI_command)
		return self.query_results #it will return the value, not variable/value pair


	def queryFilter(self, keyword):
		'''Returns value of corresponding server parameter.

		Takes keyword from other functions and filters out needed values.
		'''
#		self.getIPMIdata()
		if self.query_results != None:
			pattern_digits = re.compile(r"\d{2,4}")
			filter_result = 0
			fan_speed=list()
			if keyword == "FAN":					  # special case since FAN rpm could vary
				for line in self.query_results:
					if line.find(keyword) != -1:   # when not found returns -1, returns index if keyword is found in string
						line_words = line.split()  # turning str into list to perform search
						for word in line_words:
							if pattern_digits.match(word) != None: # though 'match' checks only beginning of the string, we can use either here
								fan_speed.append(int(word)) 		# means that we found number (word consisting of digits) and adding its value
				return fan_speed
			else:
				for line in self.query_results:
					if line.find(keyword) != -1: #return index if found and -1 othewise
						line_words = line.split()
						for word in line_words:
							if pattern_digits.match(word) != None:
								filter_result=int(word)
								break
						break
				return filter_result
		else:
			print ("Nothing to filter, query_results = None")
			return None


	def quickCheck(self):
		'''Checks if everything is ok and return list of errors if not.

		Otherwise logs the error.
		'''
		quick_check_result = False
		for line in self.query_results:
			line_words = line.strip('\n').split()
			if line_words[-1] == "ok":
				quick_check_result = True
			else:
				quick_check_result = False
				quick_check_log = open('./quick_check_error_log.txt', 'w')
				quick_check_log.write('{} {}'.format(time.strftime("%c"), line))
				quick_check_log.close()
		return quick_check_result#, check_errors


	def getAmbientTemp(self):
		return self.queryFilter("Ambient")


	def getPowerConsumption(self):
		return self.queryFilter("System Level")


	def getFanSpeed(self):
		'''For fans 1 to 5 returns a list with corresponding speeds.

		'''
		Fan_Speed = self.queryFilter("FAN")
		return Fan_Speed

	def setFanSpeedAuto(self):
		IPMI_command = " raw 0x30 0x30 0x01 0x01"
		self.useIPMI(IPMI_command)

	def setFanSpeedManual(self):
		IPMI_command = " raw 0x30 0x30 0x01 0x00"
		self.useIPMI(IPMI_command)


	def setFanSpeed_Low(self):
		''' Sets fan speed to 8%.

		FANS 1 to 4: 2040 RPM, FAN 5:2160 RPM
		'''
		IPMI_command = " raw 0x30 0x30 0x02 0xff 0x08"
		self.useIPMI(IPMI_command)


	def setFanSpeed_Medium(self):
		''' Sets fan speed to 17%.

		FANS 1 to 5 :3000 RPM
		'''
		IPMI_command = " raw 0x30 0x30 0x02 0xff 0x11"
		self.useIPMI(IPMI_command)

	def setFanSpeed_High(self):
		''' Sets fan speed to 50%.

		FANS 1 to 4: 6720 RPM, FAN 5:6840 RPM
		'''
		IPMI_command = " raw 0x30 0x30 0x02 0xff 0x32"
		self.useIPMI(IPMI_command)


	def getFanSpeedChange(self):
		'''Checks if fan speed change is required.

		Writes and compares current and previous temperature readings
		to determine if system temperature is increasing. If yes,
		returns True. Otherwise returns False.
		'''
		def write_ambient(temperature_reading):
			to_string = str(temperature_reading)
			ambient_temp_log = open('./ambient_temp_log.txt', 'w')
			ambient_temp_log.write(to_string)
			ambient_temp_log.close()

		fan_speed_increase = False

		if os.path.exists('./ambient_temp_log.txt'):
			ambient_temp_log = open('./ambient_temp_log.txt', 'r')
			previous_reading = ambient_temp_log.readline()
			current_reading = self.getAmbientTemp()
			ambient_temp_log.close()
			if len(previous_reading) == 0: #could be empty file
				write_ambient(current_reading)
			else:
				if int(current_reading) > int(previous_reading) + 1:
					fan_speed_increase = True
					write_ambient(current_reading)
				else:
					write_ambient(current_reading)
		else:
			write_ambient(current_reading)

		return fan_speed_increase


	def fanControl(self):

		def write_fan(value):
			fan_log = open('./fan_log', 'w')
			fan_log.write(str(value))
			fan_log.close()

		def write_overheating(ambient_temp):
			overheating_log_file = open('./overheating_log_file.txt', 'a')
			overheating_log_file.write(
			'{} ambient temperature is: {},'
			'fan speed is set to Auto by fanControl \n'
			.format(time.strftime("%c"), ambient_temp) # %c is locale's appropriate date and time representation
			)
			overheating_log_file.close()

		self.getIPMIdata()			# refresh readings

		if self.quickCheck():
			ambient_temp = self.getAmbientTemp()
			normal_temp_range = xrange(9, 31) # xrange is better than range here. 30 is max temp 29+1, since range is non inclusive - does not include first and last values
			high_temp_range = xrange(30, 36)
			if ambient_temp in normal_temp_range:
				if self.getFanSpeedChange():
					if not os.path.exists('./fan_log'):
						self.setFanSpeedManual()
						self.setFanSpeed_Medium()
						write_fan('Medium')
					else:
						fan_log = open('./fan_log', 'r')
						speed_increase = fan_log.readline()
						fan_log.close()
						self.setFanSpeedManual()
						if len(speed_increase) == 0:    # in case the file is empty
							self.setFanSpeed_Medium()
							write_fan('Medium')
						else:
							if speed_increase == "Medium":
								self.setFanSpeed_High()
								write_fan('High')
							# check if I need timeout in case temperature stabilizes with time.
							if speed_increase == "High":
								self.setFanSpeedAuto()
								write_overheating(ambient_temp)

			if ambient_temp in high_temp_range:
				self.setFanSpeedAuto()
				write_overheating(ambient_temp)

			if ambient_temp >= 35:
				SHUTDOWN_and_cleanup()

				if os.path.exists('./overheating_log_file.txt'):
					write_overheating(ambient_temp)
					print ('^ ^ ^ appening to existing file ^ ^ ^')
				else:
					write_overheating(ambient_temp)
					print ('created new file')
		else:
			print("Quick check is not okay. See the quick_check_error_log.txt file")

	def SHUTDOWN_and_cleanup(self):
		''' Powers down the server and deletes temporary log files.

		'''
		IPMI_command = " chassis power off"
		self.useIPMI(IPMI_command)
		#delete created files (except overheating_log_file).
		subp.Popen("rm ./ambient_temp_log && rm ./fan_log", shell=True)

	def powerOn(self):
		IPMI_command = " chassis power on"
		self.useIPMI(IPMI_command)


if __name__ == '__main__':
	from config import *

	r710 = server_ipmi(IPMI_server_IP, IPMI_username, IPMI_password)
	r710.powerOn()
	time.sleep(10)
	r710.getIPMIdata()
	timer_fanControl = 300

	if r710.quickCheck():
		print("Quick check: OK")
	else:
		print("Quick check: Failure, check log")

	r710.setFanSpeedManual()
	r710.setFanSpeed_Low()

	while True:
		r710.fanControl()
		print ("Scripted fan control: Temperature is {}, Fan rpm is {}, Power Consumption is{}. \n"
			.format(r710.getAmbientTemp(), r710.getFanSpeed()[0], r710.getPowerConsumption()))
		print ("Sleeping for {} seconds \n".format(timer_fanControl))
		time.sleep(timer_fanControl)
