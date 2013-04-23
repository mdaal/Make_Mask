import io
import cStringIO
import warnings
import numpy as np
import SimStruc

import os
#import pickle
#import sqlite3

#from cStringIO import StringIO
#src = StringIO()

def Parse_Sonnet_Response(File_Name_or_String_or_Dir):
	"""File_Name_or_String_or_Dir can be:
		a) the file name (with path) of the sonnet log_composite.log or log_response.log files
		b) a string containing the response data
		c) a director of output files. Directory must have an overview file which names  the .s3p files names in the direcotry.  This fuctions aggregates these files into one and then parses that file.
	"""

	if os.path.isfile(File_Name_or_String_or_Dir): #Case where File_Name_or_String_or_Dir is a file name
		f = io.open(File_Name_or_String_or_Dir, mode='r')
	elif os.path.isdir(File_Name_or_String_or_Dir): #Case where File_Name_or_String_or_Dir is a Directory of .s3p output files
		summary_file = ''
		for files in os.listdir(File_Name_or_String_or_Dir):
			if files.endswith("files.txt"):
				summary_file = files
				break
		if summary_file == '':
			raise RuntimeError('No summary file found for simulation data')
		f = io.open(File_Name_or_String_or_Dir+ os.sep +summary_file , mode='r')
		line = f.next()
		Agg_File_Set = False
		while 1:
			if line.startswith('USER_FILE') and Agg_File_Set == False:
				Agg_File = line.split(' ')[1].strip('\n').strip('.s3p')+'_Aggregated.s3p'
				Agg_File_Path = File_Name_or_String_or_Dir+ os.sep +Agg_File 
				Agg_File = io.open(Agg_File_Path , mode='w')
				Agg_File_Set = True
			if line.startswith('OUTPUT_FILE'):
				s3p_file = line.split(' ')[1].strip('\n')
				s3p_file = io.open(File_Name_or_String_or_Dir+ os.sep +s3p_file , mode='r')
				Agg_File.write(s3p_file.read())
				Agg_File.write(unicode('\n%%\n\n'))
				s3p_file.close()
			try:
				line = f.next()
			except:
				Agg_File.close()
				f.close()
				break
		f = io.open(Agg_File_Path, mode='r')
	else: #Case where File_Name_or_String_or_Dir is a string containing the response data
		f = cStringIO.StringIO(File_Name_or_String_or_Dir)

	f.seek(0,0)
	line = f.readline().strip().lower()
	prev_line = ''


	try:
		del Sim
		#print("%s Sim was previously defined" % (' '*5))
	except:
		pass#print('%s No Sim previously defined' % (' '*5))


	#Parameter_Combinations = False
	
	#Current_Impedance_Normalization = 0
	Frequency = 0
	#Eeff = 0
	#Z0 = 0
	#Port = 0
	#Port_Capacitance = 0

	Read_Block = False # Gets set to true for reading *.s3p files
	RI = False # Gets set to true if data is real-imaginary
	MA = False # Gets set to true if data is magnitude-phase
	Parameter = ['null', 0]
	Proceed = 1
	Name_Found = 0

	count =20
	while Proceed and count >= 0:
		if line.startswith('%%'):
			Read_Block = False
		#if line.startswith('parameter combination'):
		#	Parameter_Combinations = True
		if line.startswith('project:') or line.startswith('! from project:'):
			line = line.rstrip('.son')

			try:
				pos = line.rindex('couplersweep')
				Name_Found = 1
			except:	
				pass

			try:
				pos = line.rindex('portcalc')
				Name_Found = 1
			except:
				pass

			try:
				pos = line.rindex('auxcouplersweep')
				Name_Found = 1
			except:
				pass

			if Name_Found == 0:
				warnings.warn('Unknown Simulation Name')
				pos = line.rindex(':')
				pos = pos+1

			Name = str(line[pos:].upper())

		if line.startswith('independent parameter values:') or line.startswith('!< params'): #if multiple parameters, only extractes first listed
			 line = f.next().strip('!< ').strip().lower()
			 line = str(line)
			 Parameter = line.split(' = ')

		if line.endswith('ohm port terminations.'):
			line_list = line.rstrip(' ohm port terminations.').split(' ')
			Current_Impedance_Normalization = float(line_list[-1]) 
			#count = count - 1

		if line.startswith('magnitude/angle'):
			MA = True
			line = f.next().strip().lower()
			line_array = line.strip().split(' ')
			Frequency = float(line_array[0])*pow(10,9)
			line_array.remove(line_array[0]) # or line_array.pop(0) 
			length = len(line_array)
			S = np.zeros((length/2,length/2), dtype=complex)
			for i in xrange(length/2):
				for j in xrange(length/2):
					#S[i,j] = np.complex(float(line_array[2*j]),float(line_array[2*j+1]))
					S[i,j] = float(line_array[2*j])*np.complex(np.cos(np.deg2rad(float(line_array[2*j+1]))),np.sin(np.deg2rad(float(line_array[2*j+1])))) #need to convert deg to rad
				line = f.next().strip().lower()
				line_array = line.strip().split(' ')


		if line.startswith('# ghz'):
			Read_Block = True
			line = line.strip('# ghz')
			
			if line.lower().find('ri') != -1: #case for real/imaginary data
				RI = True
			elif line.lower().find('ma') != -1: #case for real/imaginary data
				MA = True
			line_list = line.split(' ')
			Current_Impedance_Normalization = np.float64(line_list[-1])
			line = f.next().strip().lower()

		if Read_Block == True and not line.startswith('!< p') and line != '':
			line_array = line.strip().split(' ')
			Frequency = np.float64(line_array[0])*pow(10,9)
			line_array.remove(line_array[0]) # or line_array.pop(0) 
			length = len(line_array)

			S = np.zeros((length/2,length/2), dtype=np.complex128)
			for i in xrange(length/2):
				for j in xrange(length/2):
					if MA == True:
						S[i,j] = np.float64(line_array[2*j])*np.complex(np.cos(np.deg2rad(np.float64(line_array[2*j+1]))),np.sin(np.deg2rad(np.float64(line_array[2*j+1])))) #need to convert deg to rad
					elif RI == True:
						S[i,j] = np.complex(np.float64(line_array[2*j]),np.float64(line_array[2*j+1]))
				line = f.next().strip().lower()
				line_array = line.strip().split(' ')


		if line.startswith('!< p'):
			Eeff = np.zeros((length/2),dtype=np.complex128)
			Z0 = np.zeros((length/2),dtype=np.complex128)
			Port_Resistance = np.zeros((length/2))
			Port_Capacitance = np.zeros((length/2))

			index = xrange(length/2)
			for i in index:
				# Extract Port Number
				#Port = int(line[line.find('p')+len('p'):line.find('f')].strip())

				# Extract Complex Eeff
				start = line.find('eeff=(')+len('eeff=(')
				end = line.find(')', start)
				_Eeff = line[start:end].split(' ')
				Eeff[i] = np.complex(np.float64(_Eeff[0]),np.float64(_Eeff[1]))

				#Extract complex Z0
				start = line.find('z0=(')+len('z0=(')
				end = line.find(')', start)
				_Z0 = line[start:end].split(' ')
				Z0[i] = np.complex(np.float64(_Z0[0]),np.float64(_Z0[1]))

				#Extract Port R
				start = line.find('r=')+len('r=')
				end = line.find('c=')
				Port_Resistance[i] = np.float64(line[start:end].strip())		

				#Extract C
				start = line.find('c=')+len('c=')
				Port_Capacitance[i] = np.float64(line[start::].strip())*pow(10,-12)

				#line = f.next().strip().lower()
				if i < max(index):
					line = f.next().strip().lower()


				#warnings.warn('No Z0 found for F = ' + str(Frequency) + 'GHz')
				#pass

			#Create Array out of Normalization Impedance Value
			Norm_Z0 = np.float64(Current_Impedance_Normalization) * np.ones(length/2,dtype=np.complex128)
			
			
			try: 
				Sim.add(S,Z0,Norm_Z0,Eeff,Port_Resistance,Port_Capacitance,Frequency, float(Parameter[1]))
			except:	
			 	Sim  = SimStruc.Simulation(S,Z0,Norm_Z0,Eeff,Port_Resistance,Port_Capacitance,Frequency, Name ,{Parameter[0]:np.float64(Parameter[1])})


			#print(str(Frequency) + ' | '+ str(S) + ' | '+ str(Eeff) +' | '+ str(Z0) +' | '+ str(Port_Capacitance))
		try:
			line = f.next().strip().lower()
		except:
			Proceed = 0

	
	f.close()

	return Sim




