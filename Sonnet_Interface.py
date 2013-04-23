from subprocess import Popen, PIPE
import platform
import os
import warnings
import sys
import time
import tarfile

import paramiko
import getpass

#cur_dir = os.getcwd()
mysys = platform.system()
print('System is %s' % (mysys))

##############load hostname, username, port, etc.
execfile('Remote_Access.txt')
# remote access file must have these three lines
# hostname = _________
# username = _________
# port     = _________  #this is the SSH port, usually 22
##############

privatekeyfile = os.path.expanduser('~/.ssh/id_rsa')

try:
	mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile) #only works if  private rsa key has no passphrase. 
	#(dont specify passphrase for key when generating key with [ ssh-keygen -t rsa -C "your_email@example.com" ]. 
	#or use ssh-keygen to change existing passphrase to no passphrase) 
except:
	warnings.warn('use of RSA key file failed. will prompt for password...')


if mysys.startswith('Windows'): 
	EMPath = "C:/Program Files (x86)/Sonnet Software/13.56/bin" + os.sep
	#EMPath = "C:" + os.sep + "Program Files (x86)" + os.sep + "Sonnet Software" + os.sep + "13.56" + os.sep+ "bin" + os.sep
elif mysys.startswith('Linux'):
	EMPath = ""
elif mysys.startswith('Darwin'):
	EMPath = ""
else: 
	EMPath = ""


def mycall(command_list, Sonnet_Path, File_Name, Terminal_Output = False):
	output_message = None
	if mysys.startswith('Windows') or mysys.startswith('Linux'):
		if type(command_list) == list:
			command_list[0] = EMPath + command_list[0]
			if Terminal_Output == False: # catch output in output_message, dusplay count as process is running
				process = Popen(command_list, stdout = PIPE,stderr= PIPE, shell = True)

				if False:
					#This code to display a number count while EM is executing prevents EM from finishing. Dont execute it 
					
					i = 1
					# #str = ""
					#print(process.poll())
					while process.poll() == None:
						#str = str + ' . ' + str(i)
						#sys.stdout.write("\r" + str)
						sys.stdout.write("\r%d " % i)
						sys.stdout.flush()
						time.sleep(0.5)
						i += 1
					sys.stdout.write("\n") # move the cursor to the next line
				output_message = process.communicate() #output_message[0] is process output and output_message[1] is error
			else:
				#This command does not show as command is being executed
				process = Popen(command_list, stdout = None,stderr= PIPE, shell = True)
				output_message = process.communicate() # capture std_err in output_message
		else:
			raise Exception('mycall requires an argument of the type list')
	elif mysys.startswith('Darwin'):
		
		ssh = paramiko.SSHClient()
		ssh.load_system_host_keys()
		#Assuming that a Host key exists!
		#ssh.connect(username=username, password=password)
		ssh.connect(hostname, username = username)

		##Appempt to keep connection open
		transport = ssh.get_transport()
		transport.set_keepalive(60*60) #Send "Keepalive" packer every hour to keep connection open  
		#NOTE: Keepalive packets are ignored by the server. They are only for keeping network connections from timing out
		##

		ssh.exec_command('mkdir ' + Sonnet_Path)

		cmd = ''
		for word in command_list:
			cmd = cmd + word + ' '
		cmd = cmd.rstrip()

		chan  = ssh.exec_command(cmd) # Execute Sonnet Calculation

		output_message = chan[1].read() #NOTE: if you try to read channel 2 (the error channel) the calculate will hang for some reason. Maybe there is a timeout? dont do chan[2].read()

		# if 0: # If set to 0 this function returns the contents of 'log_response.log' as a string, if set to 0, this function copies output directory on to local system and return directory path

		# 	output_message = chan[1].read()
		# else: 
		# 	copy_from_remote(Sonnet_Path,File_Name,ssh) # Copy directory with sonnet output files to local computer
		# 	output_message = Sonnet_Path+File_Name #thus, this fuction returns the directory path with the sonnet output files

		ssh.close()	

	else:
		warnings.warn('cannot execute Sonnet commands on this system. ignoring attempt...')
		pass
	#To format the output use raw_input	
	#raw_input(out)  
	return output_message

def Copy_To_Remote(Sonnet_Path,File_Name):
	if mysys.startswith('Darwin'):

		transport = paramiko.Transport((hostname, port))

		try: #Try to authenticate vie RSA key
			transport.connect(username = username, pkey = mykey)
		except: #if this fails prompt for passowrd
			password = getpass.getpass('Password for %s@%s: ' % (username, hostname))
			transport.connect(username=username, password=password)

	
		sftp = paramiko.SFTPClient.from_transport(transport)


		sftp.put(Sonnet_Path+File_Name+'.son',Sonnet_Path+File_Name+'.son')

		
		sftp.close()
		transport.close()
	else: 
		pass

def Copy_From_Remote(Sonnet_Path,File_Name):
	if mysys.startswith('Darwin'):
		""" This funtion makes a .tar.gz file of the output director of the Sonnet simulation and then transfers the .tar.gz file this local computer and finally untars it""" 
		ssh = paramiko.SSHClient()
		ssh.load_system_host_keys()
		#Assuming that a Host key exists!
		#ssh.connect(username=username, password=password)
		ssh.connect(hostname, username = username)

		# tar_file = Sonnet_Path + File_Name + '.tar.gz'

		# chan = ssh.exec_command('tar cvzf ' + tar_file + ' ' + Sonnet_Path + File_Name + os.sep) # this tars the enitre director path e.g.
		# #Sonnet_Files/20130408/CouplerSweep_TLW395TLG000RW256SG03ST500E1120_20130408_122907.tar.gz is tarred
		# #not just CouplerSweep_TLW395TLG000RW256SG03ST500E1120_20130408_122907.tar.gz

		# output_message = chan[1].read() # raw string. read with raw_input()

		# sftp = ssh.open_sftp()

		# sftp.get(tar_file,tar_file)

		# tar = tarfile.open(tar_file)
		# tar.extractall(path='.', members=None)

		# sftp.close()

		output_message = copy_from_remote(Sonnet_Path,File_Name,ssh)

		ssh.close()

		return output_message
	else: 
		pass

def copy_from_remote(Sonnet_Path,File_Name,SSHClient):
	""" SSHClient must be open """

	ssh = SSHClient
	#note: can see if ssh is active by seeing is underlying transport is active: T = ssh.get_transport(), T.is_active()
	tar_file = Sonnet_Path + File_Name + '.tar.gz'

	chan = ssh.exec_command('tar cvzf ' + tar_file + ' ' + Sonnet_Path + File_Name + os.sep) # this tars the enitre director path e.g.
	#Sonnet_Files/20130408/CouplerSweep_TLW395TLG000RW256SG03ST500E1120_20130408_122907.tar.gz is tarred
	#not just CouplerSweep_TLW395TLG000RW256SG03ST500E1120_20130408_122907.tar.gz

	output_message = chan[1].read() # raw string. read with raw_input()

	sftp = ssh.open_sftp()

	sftp.get(tar_file,tar_file)

	tar = tarfile.open(tar_file)
	tar.extractall(path='.', members=None)

	sftp.close()
	return output_message



def Run_EM(Sonnet_Path, File_Name):

	Sonnet_File = Sonnet_Path+File_Name+'.son'
	Log_File = Sonnet_Path+File_Name+'.log'

	SysCallEM = ['emstatus', '-Run',  Sonnet_File , '-LogFile', Log_File]
	#SysCallEM = ['emstatus -Run ' + Sonnet_File + ' -LogFile ' + Log_File + ' &']
	mycall(SysCallEM, Sonnet_Path, File_Name)


def New_Proj(Sonnet_Path,File_Name):
	Sonnet_File = Sonnet_Path+File_Name+'.son'
	SysCall=['soncmd',  '-NewProject',  Sonnet_File]
	mysys.startswith('Darwin') == False
	out = mycall(SysCall,Sonnet_Path, File_Name)
	return out
 
def Unlock_Proj(Sonnet_Path,File_Name):
	Sonnet_File = Sonnet_Path+File_Name+'.son'
	SysCall=['soncmd',  '-unlock',  Sonnet_File]
	out = mycall(SysCall, Sonnet_Path, File_Name)
	return out

def Clean_Proj(Sonnet_Path,File_Name):
	Sonnet_File = Sonnet_Path+File_Name+'.son'
	SysCall=['soncmd',  '-clean',  Sonnet_File]
	out = mycall(SysCall, Sonnet_Path, File_Name)
	return out

#Need to implement batch mode processing...
def Run_EM_nogui(Sonnet_Path,File_Name, Terminal_Output = True):
	#terminal_output = true means that output is displayed in terminal
	print("Simulating " + File_Name)
	Sonnet_File = Sonnet_Path+File_Name+'.son'
	SysCall=['em',  '-v',  Sonnet_File]
	out = mycall(SysCall,Sonnet_Path, File_Name, Terminal_Output = Terminal_Output)
	out = Copy_From_Remote(Sonnet_Path,File_Name)
	out = Sonnet_Path+File_Name
	return out







