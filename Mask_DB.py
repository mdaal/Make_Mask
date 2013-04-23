import sqlite3
from numpy import loadtxt
import cPickle as pickle
import warnings
import os
#from SimStruc import Simulation

print(__name__ + ' Module Initialized!')

warnings.filterwarnings('always')
#data_connection = 0
#data_cursor = 0

#connection = 0
#cursor = 0

Mask_DB_Global = ''
Simulation_DB_Global = ''
Is_Initialized = 0
num_resonators = 0

def Init_DB(Folder_Name,File_Name = ":memory:"):
	""" Initializes the Wafer, Sensors, Resonators, Computed_Parameyerts, Simulation_Data and Simulation_Geometries Tables.
	grabs the data from the Resonators.csv, Sensors.csv, and Wafer.csv files in the current directory

	THIS FUNCTION MUST BE RUN BEFORE USE OF ANY OTHER FUNCTION IN THIS MODULE!

	Creates the a Database for Wafer, Sensors, Resonators, Computed_Parameters, and Simulation_Geometries in Folder_Name+os.sep+File_Name (if ":memory:" is not specified)
	Creates Simulation_Data Table in a SEPARATE DB inside of Folder_Name, whcih is not  ":memory:".

	returns num_simulation  (the number of simulations required to make the mask, an integer) """
	
	global Is_Initialized
	Is_Initialized = 1

	global Mask_DB_Global

	#global connection
	#global cursor

	# Open bd of mask parameters
	if File_Name == ":memory:":
		connection = sqlite3.connect(File_Name)
		Mask_DB_Global = File_Name
	else: 
		connection = sqlite3.connect(Folder_Name+os.sep+File_Name)
		Mask_DB_Global = Folder_Name+os.sep+File_Name

	cursor = connection.cursor()


	###################################
	#     Create Resonators Table     #
	###################################
	cursor.execute('drop table if exists Resonators')
	sql_cmd = """CREATE TABLE Resonators (resonator_id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id INT, Design_Freq FLOAT, Width FLOAT, Design_Q FLOAT, Head_Space FLOAT, Coupler_Zone FLOAT, Meander_Pitch FLOAT, Meander_Zone FLOAT, simid INT)"""
	cursor.execute(sql_cmd)



	resdata = loadtxt(Folder_Name+os.sep+"Resonators.csv", delimiter=",",skiprows =1,dtype='int, float, float, float, float, float, float,float',usecols = (0,1,2,3,4,5,6,7))
	global num_resonators
	num_resonators = len(resdata)
	
	for row in resdata:	 
		sql_cmd = ("INSERT INTO  Resonators (sensor_id, Design_Freq, Width, Design_Q, Head_Space, Coupler_Zone, Meander_Pitch, Meander_Zone) VALUES " + str(row))
		cursor.execute(sql_cmd)


	#cursor.execute("SELECT simid from Resonators where id = 1")
	#print(cursor.fetchall())

	connection.commit()

	#sql_cmd = ("select * from Resonators")
	#cursor.execute(sql_cmd)
	#cursor.fetchall()


	###################################
	#       Create Sensor Table       #
	###################################
	cursor.execute('drop table if exists Sensors')
	sql_cmd = """CREATE TABLE Sensors (sensor_id INTEGER PRIMARY KEY AUTOINCREMENT, X_Length FLOAT, Y_Length FLOAT, Cut_Line_Width FLOAT, Pillar_Diameter FLOAT, Pillar_Grid_Spacing FLOAT, Pillar_Clearance Float, Through_Line_Type Text, Through_Line_Width FLOAT, Through_Line_Turn_Radius FLOAT, Through_Line_Gap FLOAT, Through_Line_Edge_Offset FLOAT)"""
	cursor.execute(sql_cmd)

	sensordata = loadtxt(Folder_Name+os.sep+"Sensors.csv", delimiter=",",skiprows =1,dtype='int, float, float, float, float, float, float, |S1, float,float, float,float',usecols = (0,1,2,3,4,5,6,7,8,9,10,11))

	try:
		for row in sensordata:
			sql_cmd = ("INSERT INTO  Sensors (sensor_id, X_Length, Y_Length, Cut_Line_Width, Pillar_Diameter, Pillar_Grid_Spacing, Pillar_Clearance, Through_Line_Type, Through_Line_Width, Through_Line_Turn_Radius,Through_Line_Gap, Through_Line_Edge_Offset) VALUES " + str(row))
			cursor.execute(sql_cmd)
	except: #Exception if there is only one row of data in sensdata
		sql_cmd = ("INSERT INTO  Sensors (sensor_id, X_Length, Y_Length, Cut_Line_Width, Pillar_Diameter, Pillar_Grid_Spacing, Pillar_Clearance, Through_Line_Type, Through_Line_Width, Through_Line_Turn_Radius,Through_Line_Gap, Through_Line_Edge_Offset) VALUES " + str(sensordata))
		cursor.execute(sql_cmd)

	connection.commit()

	 #f = open('Wafer.csv', 'rU') #to read contents of Wafer.csv
	 #f.next()
	 #f.close()

	###################################
	#        Create Wafer Table       #
	###################################
	cursor.execute('drop table if exists Wafer')
	sql_cmd = """CREATE TABLE Wafer (wafer_id INTEGER PRIMARY KEY AUTOINCREMENT, X_Length FLOAT,Y_Length FLOAT,Rows INT, Columns INT,Thickness FLOAT, Dielectric_Constant FLOAT,Freg_High FLOAT,Freq_Low FLOAT, Pillar_Height FLOAT)"""
	cursor.execute(sql_cmd)

	waferdata = loadtxt(Folder_Name+os.sep+"Wafer.csv", delimiter=",",skiprows =1,dtype='float, float, int, int, float, float, float,float,float',usecols = (0,1,2,3,4,5,6,7,8))

	sql_cmd = ("INSERT INTO  Wafer (X_Length, Y_Length, Rows, Columns, Thickness, Dielectric_Constant,Freg_High,Freq_Low, Pillar_Height) VALUES " + str(waferdata))
	cursor.execute(sql_cmd)

	connection.commit()


	sql_cmd = '''SELECT  Resonators.Width, Sensors.Through_Line_Width, Sensors.Through_Line_Gap, Sensors.X_Length, Resonators.resonator_id FROM Resonators, Sensors WHERE Resonators.sensor_id = Sensors.sensor_id
	ORDER BY Resonators.Width, Sensors.Through_Line_Width, Sensors.Through_Line_Gap, Sensors.X_Length ASC'''
	cursor.execute(sql_cmd)
	output = cursor.fetchall()

	#check if table exists:
	#cursor.execute('SELECT name FROM sqlite_master where type ="table" and name = "Resonators"')
	
	###################################
	#Create Computed_Parameters Table #
	###################################
	cursor.execute('drop table if exists Computed_Parameters')
	sql_cmd = """CREATE TABLE Computed_Parameters (resonator_id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id INTEGER, Through_Line_Impedance FLOAT, 
		Resonator_Impedance FLOAT, Coupler_Length FLOAT, Aux_Coupler_Length FLOAT, Resonator_Eeff FLOAT, Through_Line_Eeff FLOAT, Resonator_Length FLOAT, Meander_Pitch FLOAT,  
		Meander_Zone FLOAT, Meander_Length FLOAT, Through_Line_Length FLOAT, Through_Line_Metal_Area FLOAT, Resonator_Metal_Area FLOAT, 
		Patch_Area FLOAT,Turn_Extension FLOAT, Rungs FLOAT, Sensor_Pillar_Area FLOAT, Coupler_Zone FLOAT, Design_Q FLOAT, Coupler_Phase_Change FLOAT)"""
	#Note: Computed Resonator Length has been shortened by presence of coupler. phase change of Coupler has been subtracted from vacuum lenght or resonator.
	cursor.execute(sql_cmd)
	cursor.executemany("INSERT INTO Computed_Parameters (resonator_id) VALUES (?)",zip(range(1,num_resonators+1)))


	#####################################
	# Create Simulation_Geometries Table#
	#####################################
	cursor.execute('drop table if exists Simulation_Geometries')
	sql_cmd = """CREATE TABLE  Simulation_Geometries (simid INTEGER PRIMARY KEY AUTOINCREMENT, Simulation_Geometry Text)"""
		#CouplerSweep  blob, AuxCouplerSweep  blob)"""
	cursor.execute(sql_cmd)

	sql_cmd = "INSERT INTO  Simulation_Geometries (simid) VALUES (1)"
	cursor.execute(sql_cmd)

	i = 1
	k = 1
	prev_record = output[0]
	sql_cmd = "UPDATE Resonators SET simid = " + str(i) + " WHERE resonator_id = " + str(prev_record[-1])
	cursor.execute(sql_cmd)

	for record in output[1:]:
		if record[:-1] == prev_record[:-1]:
			sql_cmd = "UPDATE Resonators SET simid = " + str(i) + " WHERE resonator_id = " + str(record[-1])
			cursor.execute(sql_cmd)
		else:
			i=i+1
			sql_cmd = "UPDATE Resonators SET simid = " + str(i) + " WHERE resonator_id = " + str(record[-1])
			cursor.execute(sql_cmd)
		prev_record = record
		if i != k: #initialize empty  Simulation_Data Table
			k = i
			sql_cmd = ("INSERT INTO  Simulation_Geometries (simid) VALUES (" + str(k) + ")")
			cursor.execute(sql_cmd)


	#cursor.execute('UPDATE Simulation_Data SET CouplerSweep =  :SIM WHERE simid = 1', {'SIM' : Sim})
	#cursor.execute("UPDATE Resonators SET simid = :sim WHERE id = 1" ,{'sim': 110})

	connection.commit()

	num_simulation = i 	

	###################################
	#  Create Simulation_Data Table  #
	###################################

	#global data_connection
	#global data_cursor	

	global Simulation_DB_Global
	Simulation_DB_Global = Folder_Name+os.sep+'Simulation.db'
	
	data_connection = sqlite3.connect(Simulation_DB_Global)
	data_cursor = data_connection.cursor()
	
	# Simulation Name Must Be Unique! (since its the primary key)
	sql_cmd = """CREATE TABLE if not exists Simulation_Data (Simulation_Geometry Text PRIMARY KEY, CouplerSweep  blob, AuxCouplerSweep  blob)"""
	data_cursor.execute(sql_cmd)

	connection.close()
	data_connection.close()

	return num_simulation

def Get_Mask_Data(CMD,fetch = 'all'):

	if Is_Initialized == 0: 
		warnings.warn('Attempt to use frunction from ' + __name__ + ' without first initializing DB. Ignoring Attempt....')
		return

	connection = sqlite3.connect(Mask_DB_Global)
	cursor = connection.cursor()
	cursor.execute(CMD)
	if fetch == 'all':
		out = cursor.fetchall()
	else:
		out =  cursor.fetchone()
	connection.close()

	return out

def Update_Simulation_Geometries(simid,Simulation_Geometry):
	connection = sqlite3.connect(Mask_DB_Global)
	cursor = connection.cursor()
	cursor.execute("UPDATE Simulation_Geometries SET Simulation_Geometry = :sim_geo WHERE simid = :simid", {"sim_geo":Simulation_Geometry, "simid":simid})
	connection.commit()
	connection.close()	


def Update_Computed_Parameters(resonator_id, Parameter_Dict):
	if resonator_id > num_resonators:
		warnings.warn('Attempting to update computed parameters for resonator_id = ' + str(resonator_id) + ', but there are only ' + str(num_resonators) + ' total. Ignoring Request.')
		return

	sql_cmd = "UPDATE Computed_Parameters SET "
	for i in range(len(Parameter_Dict)):
		sql_cmd = sql_cmd + str(Parameter_Dict.keys()[i]) + " = " +  str(Parameter_Dict.values()[i]) + ", "
	sql_cmd = sql_cmd[:-2] + " WHERE resonator_id = " + str(resonator_id)

	connection = sqlite3.connect(Mask_DB_Global)
	cursor = connection.cursor()
	cursor.execute(sql_cmd)
	connection.commit()
	connection.close()
	


def Get_Schema(Table = ''):
	if Table == '':
		out = Get_Mask_Data('SELECT sql FROM sqlite_master where type = "table" ',fetch = 'all')
	else:
		out =Get_Mask_Data('SELECT sql FROM sqlite_master where type = "table" and name = "' + str(Table)+ '"',fetch = 'all')
	print(out)
	return out

def Get_Res_Dict(resonator_id):

	pass


def Update_Simulation_Data(Simulation_Geometry, Column_Name, Simulation):
	""" Column_Name  can  be "CouplerSweep" or "AuxCouplerSweep"
	"""
	if Is_Initialized == 0: 
		warnings.warn('Attempt to use frunction from ' + __name__ + ' without first initializing BD. Ignoring Attempt....')
		return

	data_connection = sqlite3.connect(Simulation_DB_Global)
	data_cursor = data_connection.cursor()
	# Here we force pickle to use the efficient binary protocol (protocol=2). This means you absolutely must use an SQLite BLOB field
	data_cursor.execute('SELECT Simulation_Geometry FROM Simulation_Data WHERE Simulation_Geometry = :sim_geo', {"sim_geo":Simulation_Geometry})

	if data_cursor.fetchone() == None:
		print('Inserting (row = %s,column = %s) as new Simulation to table Simulation_Data' % (Simulation_Geometry,Column_Name))
		data_cursor.execute("INSERT INTO Simulation_Data (Simulation_Geometry) VALUES (:sim_geo)", {"sim_geo":Simulation_Geometry})
	else:
		print('Updating (row = %s,column = %s) in table Simulation_Data' % (Simulation_Geometry,Column_Name))


	data_cursor.execute("UPDATE Simulation_Data SET " + str(Column_Name)+ " = :Simulation WHERE Simulation_Geometry  = :sim_geo ", {"Simulation":sqlite3.Binary(pickle.dumps(Simulation, protocol=2)), "sim_geo":Simulation_Geometry})
	#data_cursor.execute("UPDATE Simulation_Data SET " + str(Column_Name)+ " = :Simulation WHERE Simulation_Geometry  = :sim_geo ", {"Simulation":sqlite3.Binary(pickle.dumps(Simulation, protocol=2)), "sim_geo":Simulation_Geometry})
	data_connection.commit()
	data_connection.close()


def Get_Simulation_Data(Simulation_Geometry, Column_Name):
	"""Return Deserialized date from blob at Column "Column_Name", row "Simulation_Geometry" on table Simulation_Data
	"""

	if Is_Initialized == 0: 
		warnings.warn('Attempt to use frunction from ' + __name__ + ' without first initializing BD. Ignoring Attempt....')
		return
	data_connection = sqlite3.connect(Simulation_DB_Global)
	data_cursor = data_connection.cursor()

	data_cursor.execute("SELECT " + str(Column_Name) + " FROM Simulation_Data WHERE Simulation_Geometry  = :sim_geo", {"sim_geo":Simulation_Geometry})
	Simulation = data_cursor.fetchone()

	try:
		Simulation = pickle.loads(str(Simulation[0]))
	except:
		#No Data
		data_connection.close()
		raise RuntimeError('Attempt to Deserialize data from table Simulation_Data failed. Probably No Data...')
	data_connection.close()
	
	return Simulation



