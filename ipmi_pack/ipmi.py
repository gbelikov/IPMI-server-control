import subprocess, os, re, time
PIPE = subprocess.PIPE

class server_ipmi(object):

	def __init__(self, IPMI_server_IP, IPMI_username, IPMI_password):
		self.IPMI_server_IP = IPMI_server_IP
		self.IPMI_username = IPMI_username
		self.IPMI_password = IPMI_password
		#self.IPMI_command = IPMI_command
		self.query_results = ''
		#self.fan_speed = list()


		
	def useIPMI(self, IPMI_command):
#   we use only one parameter IPMI_command, since others are
#	obtained from the instanse of the class: IPMI_password, IPMI_username etc
#		try:
		#IPMI_command = IPMI_command
		return subprocess.Popen("ipmitool -I lanplus -H {} -U {} -P {} {}"
		.format(self.IPMI_server_IP, self.IPMI_username, self.IPMI_password, IPMI_command), 
		shell=True, stdout=PIPE).stdout.readlines()
		#return ipmi_data
		#except:
		
#	print ("Could not connect")
#			query_results = None
			
	
	def getIPMIdata(self):
		#query_results = list()
#		try:
		IPMI_command = " sdr | grep -i 'ambient \| rpm \| watts'"
		#global query_results 
		self.query_results = self.useIPMI(IPMI_command)			
		#getIPMIdata_log = open('./ipmidata.txt', 'w')
		#for item in query_results:	
		#	getIPMIdata_log.write(str(item))
		#getIPMIdata_log.close()

		
		#except:
#			print ("Could not connect")
#			query_results = None
		return self.query_results #it will return the value, not variable/value pair
		
	def queryFilter(self, keyword):

# using list index (e.g. numerical_value = int(line_words[X]))instead of for loop 
# to retrive corresponding values would be more complex since list length is not constant
# could use pandas for that, but it seems to be overkill, or does it?
		#fan_speed = list()
		if self.query_results != None:
			pattern_digits = re.compile(r"\d{2,4}")
			filter_result = 0
			fan_speed=list()
			if keyword == "FAN":					  # special case since FAN rpm could vary
				#iteration = 0
				#fan_speed = list() ##seems to be the wrong place
				for line in self.query_results:
					if line.find(keyword) != -1:   # returns index if keyword is found in string
						line_words = line.split() # turning str into list to perform search
						#print ("the line is >>>", line)
						for word in line_words:
							if pattern_digits.match(word) != None: # though 'match' checks only beginning of the string, we can use either here
								fan_speed.append(int(word)) 		# means that we found number (word consisting of digits) and adding its value
								#print("THE SPEED IS >>>: ", word, fan_speed)
								
					#iteration += iterationn
				return fan_speed
			else:
				for line in self.query_results:
					#print("printing first line >>>>>>", line)
					if line.find(keyword) != -1: #return index if found and -1 othewise
						line_words = line.split()
						for word in line_words:
							if pattern_digits.match(word) != None:
								filter_result=int(word)
								#print ("WORD IS ", word)
								break
						break
					else:
						filter_result = "no fucking result for {} is here: {} and the type is {}".format(keyword, line, type(line) )
						
				return filter_result
			
		else:
			print ("Nothing to filter, query_results == None")
			return None
			


# Check if everything is ok and return list of errors if not. 
	
	def quickCheck(self): 
		quick_check_result = False
		#check_errors = list()
		for line in self.query_results:
			line_words = line.strip('\n').split()
			if line_words[-1] == "ok":
				#print (line)
				quick_check_result = True
			else:
				#print (line_words[-1])
#				print ("NOT OK!")
				quick_check_result = False
				#check_errors.append(line)
				## ADD LOG FILE FOR ERRORS
		return quick_check_result#, check_errors
		
		
	def getAmbientTemp(self):
		return self.queryFilter("Ambient")
		
	
	def getPowerConsumption(self):
		return self.queryFilter("System Level")
	
	
	def getFanSpeed(self):
		Fan_Speed = self.queryFilter("FAN")
		return Fan_Speed
		
	def setFanSpeedAuto(self):
		IPMI_command = " raw 0x30 0x30 0x01 0x01"
		self.useIPMI(IPMI_command)	
	
	def setFanSpeedManual(self):
		IPMI_command = " raw 0x30 0x30 0x01 0x00"
		self.useIPMI(IPMI_command)	
	
	
	def setFanSpeed_Low(self):#
		IPMI_command = " raw 0x30 0x30 0x02 0xff 0x06"
		self.useIPMI(IPMI_command)	
	
	
	def setFanSpeed_Medium(self): #Lowest noise level without annoying whinning of Low.	
		# raw 0x30 0x30 0x02 0xff 0x08 - FANS_1_4: 2040 RPM, FAN5:2160 RPM
		IPMI_command = " raw 0x30 0x30 0x02 0xff 0x08"
		self.useIPMI(IPMI_command)

		
	def setFanSpeed_High(self):
		# raw 0x30 0x30 0x02 0xff 0x11 - FANS_1_4: 3000 RPM, FAN5:3000 RPM	
		IPMI_command = " raw 0x30 0x30 0x02 0xff 0x11"
		self.useIPMI(IPMI_command)

	
	def getFanSpeedChange(self):
	
		def write_ambient(temperature_reading):
			to_string = str(temperature_reading)
			ambient_temp_log = open('./ambient_temp_log.txt', 'w')		
			ambient_temp_log.write(to_string)
			ambient_temp_log.close()
	
		#current_reading = ''
		#previous_reading = ''
		fan_speed_increase = False 

		if os.path.exists('./ambient_temp_log.txt'):
			ambient_temp_log = open('./ambient_temp_log.txt', 'r')		
			previous_reading = ambient_temp_log.readline()
			print ("previous reading is ", previous_reading, len(previous_reading))
			current_reading = self.getAmbientTemp()
			print ("CURRENT READING", current_reading, type(current_reading))
			ambient_temp_log.close()
			# if temperature is not encreasing, no need for speed increase as well:
			if len(previous_reading) == 0: #could be empty file
				print ("TYPE CURRENT IS ", type(current_reading))
				write_ambient(current_reading)
				print ('current reading is (sedond if) ', current_reading, type(current_reading))
			else:
				if int(current_reading) <= int(previous_reading) + 1:
					fan_speed_increase = False
				else:
					fan_speed_increase = True	
					write_ambient(current_reading)
					print ("written ELIF")		
		else:
			write_ambient(current_reading)
			fan_speed_increase = False
			print ("writted ELSE")
			
		return fan_speed_increase
			
		
	def fanControl(self):
	
		def write_fan(value):
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
		
	
		if self.quickCheck():
			ambient_temp = self.getAmbientTemp()
			
			normal_temp_range = xrange(9, 30) # xrange is better than range here. 30 is max temp 29+1, since range is non inclusive - does not include first and last values
			high_temp_range = xrange(30, 36)
			
			if ambient_temp in normal_temp_range:
				if self.getFanSpeedChange():
					if not os.path.exists('./fan_log'):
						self.setFanSpeedManual()
						self.setFanSpeed_Medium()
						#record increase="Medium" of speed in separate file.
						fan_log = open('./fan_log', 'w')
						write_fan('Medium')				
					else:
						fan_log = open('./fan_log', 'r')
						self.speed_increase = fan_log.readline()
						self.setFanSpeedManual()						
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
				
			if ambient_temp > 35:
				SHUTDOWN_and_cleanup()

				if os.path.exists('./overheating_log_file.txt'):
					write_overheating(ambient_temp)
					print ('^ ^ ^ appening to existing file ^ ^ ^')
				else:
					write_overheating(ambient_temp)
					print ('created new file')
	
				

				
	def SHUTDOWN_and_cleanup(self):
		IPMI_command = " chassis power off"
		self.useIPMI(IPMI_server_IP, IPMI_username, IPMI_password, IPMI_command)		
		#delete created files (except overheating_log_file).
		subp.Popen("rm ./ambient_temp_log && rm ./fan_log", shell=True)
				

# do not really need subclasses yet






