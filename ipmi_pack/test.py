#import subprocess
#import time
#import re
#from ipmi_pack.config import *
#from ipmi_pack.ipmi import *
#from config import *

#import ipmi_pack.config
#import ipmi_pack.ipmi

from config import *
from ipmi import *

#PIPE = subprocess.PIPE

r710=server_ipmi(IPMI_server_IP, IPMI_username, IPMI_password)

x= r710.useIPMI(" sdr | grep -i 'ambient \| rpm \| watts'")
#print ('tipe of useIPMI IS ', type(x))

print ('This is a test')

results = r710.getIPMIdata()

#print ("type of get getIPMIdata is ", type(r710.getIPMIdata()))

print ("query results are here:")
print results

print ("type of quick check is ", type(r710.quickCheck()))

check_result = r710.quickCheck()

if check_result == True:
	print ("Quick Check Status is:  OK")
else:
	print ("NOT OK", check_result)

#print ("quick ckeck result ===> ",check_result)

y = r710.getAmbientTemp()
##z = r710.queryFilter("System")
print ("Ambient temp is       {} ".format(y))


#xyz = r710.getFanSpeed()
#print ("fan speed is xyz", xyz)
print ("Fan speeds are:       {}".format(r710.getFanSpeed()))

print ("Power Consumption is: {}\n".format(r710.getPowerConsumption()))

zzz = r710.getFanSpeedChange()

if zzz:
	print("need for increased speed, because getFanSpeedChange is {}".format(zzz))
else:
	print("no need to increase, because getFanSpeedChange is {}".format(zzz))
