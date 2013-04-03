import io
import cStringIO
import warnings
import numpy as np
import SimStruc
#import pickle
#import sqlite3

#from cStringIO import StringIO
#src = StringIO()

def Parse_Sonnet_Response(File_Name_or_String):
	"""File_Name_or_String can be:
		a) the file name (with path) of the sonnet log_composite.log or log_response.log files
		b) a string containing the response data
	"""

	if File_Name_or_String.find('ELECTROMAGNETIC ANALYSIS OF 3-D PLANAR CIRCUITS') == -1: #Case where File_Name_or_String is a file name
		f = io.open(File_Name_or_String, mode='r')
	else: #Case where File_Name_or_String is a string containing the response data
		f = cStringIO.StringIO(File_Name_or_String)

	f.seek(0,0)
	line = f.readline().strip().lower()
	prev_line = ''


	try:
		del Sim
		#print("%s Sim was previously defined" % (' '*5))
	except:
		pass#print('%s No Sim previously defined' % (' '*5))


	#Parameter_Combinations = False
	mag_angle = False
	#Current_Impedance_Normalization = 0
	Frequency = 0
	#Eeff = 0
	#Z0 = 0
	#Port = 0
	#Port_Capacitance = 0
	Parameter = ['null', 0]
	Proceed = 1
	Name_Found = 0

	count =20
	while Proceed and count >= 0:
		#if line.startswith('parameter combination'):
		#	Parameter_Combinations = True
		if line.startswith('project:'):
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

		if line.startswith('independent parameter values:'):
			 line = f.next().strip().lower()
			 line = str(line)
			 Parameter = line.split(' = ')

		if line.endswith('ohm port terminations.'):
			line_list = line.rstrip(' ohm port terminations.').split(' ')
			Current_Impedance_Normalization = float(line_list[-1]) 
			#count = count - 1

		if line.startswith('magnitude/angle'):
			mag_angle = True
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
		#print("here")
		if line.startswith('!< p'):
			Eeff = np.zeros((length/2),dtype=complex)
			Z0 = np.zeros((length/2),dtype=complex)
			Port_Resistance = np.zeros((length/2))
			Port_Capacitance = np.zeros((length/2))

			for i in xrange(length/2):
				# Extract Port Number
				#Port = int(line[line.find('p')+len('p'):line.find('f')].strip())

				# Extract Complex Eeff
				start = line.find('eeff=(')+len('eeff=(')
				end = line.find(')', start)
				_Eeff = line[start:end].split(' ')
				Eeff[i] = np.complex(float(_Eeff[0]),float(_Eeff[1]))

				#Extract complex Z0
				start = line.find('z0=(')+len('z0=(')
				end = line.find(')', start)
				_Z0 = line[start:end].split(' ')
				Z0[i] = np.complex(float(_Z0[0]),float(_Z0[1]))

				#Extract Port R
				start = line.find('r=')+len('r=')
				end = line.find('c=')
				Port_Resistance[i] = float(line[start:end].strip())		

				#Extract C
				start = line.find('c=')+len('c=')
				Port_Capacitance[i] = float(line[start::].strip())*pow(10,-12)

				line = f.next().strip().lower()

				#warnings.warn('No Z0 found for F = ' + str(Frequency) + 'GHz')
				#pass

			#Create Array out of Normalization Impedance Value
			Norm_Z0 = float(Current_Impedance_Normalization) * np.ones(length/2,dtype=complex)
			
			
			try: 
				Sim.add(S,Z0,Norm_Z0,Eeff,Port_Resistance,Port_Capacitance,Frequency, float(Parameter[1]))
			except:	
			 	Sim  = SimStruc.Simulation(S,Z0,Norm_Z0,Eeff,Port_Resistance,Port_Capacitance,Frequency, Name ,{Parameter[0]:float(Parameter[1])})


			#print(str(Frequency) + ' | '+ str(S) + ' | '+ str(Eeff) +' | '+ str(Z0) +' | '+ str(Port_Capacitance))
		try:
			line = f.next().strip().lower()
		except:
			Proceed = 0

	
	f.close()

	return Sim




