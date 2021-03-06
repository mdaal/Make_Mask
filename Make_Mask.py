import Mask_DB
import warnings
import Sonnet_Coupling
import Sonnet_Interface
import Parse_Sonnet_Response
import Compute_Parameters
import SimStruc
import os

import gdspy
import Draw_Mask as D_M

mask_file_loaded = 0
num_simulation = 0 
Through_Line_Layer = 1
Resonator_Trace_Layer = 2
Pillar_Layer = 3

warnings.filterwarnings('always')

Mask_Folder = ''

def Make_Mask(Folder_Name = 'Mask_Files',Mask_DB_Name = ":memory:", Rebuild_DB = False):
	'''This function performs necessary initializations for the the module. It must be run first.'''

	#Read Mask Parameters from file
	global num_simulation
	num_simulation = Mask_DB.Init_DB(Folder_Name,Mask_DB_Name,Rebuild_DB = Rebuild_DB)

	if Rebuild_DB == True:
		print('Executing coupler simulatoins (Force_Simulation = False)...')
		Execute_Coupler_Simulations()
		print('Computing all mask parameters...')
		Compute_All_Mask_Parameters()

	#Set Mask folder location global
	global Mask_Folder
	Mask_Folder = Folder_Name

	return num_simulation # #note: this number not to total number of sonnet simulations, its the number of resonator geometeries. for each geometery, CouplerSweep and maybe a AuxCouplerSweep will be needed

def Execute_Coupler_Simulations(Force_Simulation = False):
	if num_simulation is 0:
		RuntimeError('Number of Simulation is 0. Must run Make_Mask() command first to initialize Mask Database and compute number of simulations.')

	simid = 1
	def Simulate(Simulation_Type = 0):
		if isinstance(Simulation_Type, str):
			raise RuntimeError('Simulation_Type must be integer')
		#File_Name looks like CouplerSweep_TLW360TLG00RW200SG03ST500E1120_20130228_143425.son
		#Simulation_Geometry looks like TLW360TLG00RW200SG03ST500E1120
		Sonnet_Path,  File_Name, Simulation_Geometry, Simulation_Type_Name,Coupler_Space = Sonnet_Coupling.Sonnet_Coupling(simid, Simulation_Type = Simulation_Type)
		print('Simulating %s for geometry %s, %i of %s' % (Simulation_Type_Name,Simulation_Geometry,simid,num_simulation))

		if 1: #1 for computing actual sumlations, 0 for using local files "log_response.log" and "aux_log_response.log"
			response = Sonnet_Interface.Run_EM_nogui(Sonnet_Path,File_Name, Terminal_Output = True)

			Simulation = Parse_Sonnet_Response.Parse_Sonnet_Response(response)
		else:
			FN = {0: "log_response.log", 1:"aux_log_response.log" }
			Simulation = Parse_Sonnet_Response.Parse_Sonnet_Response(FN[Simulation_Type])

		Mask_DB.Update_Simulation_Geometries(simid,Simulation_Geometry)	
		Mask_DB.Update_Simulation_Data(Simulation_Geometry, Simulation_Type_Name, Simulation)
		return Simulation

	def Check_For_Simulation(Simulation_Type = 0):
		""" Returns False is No Simulation of type SimStruc.Simulation is in simulation database for current Simulation_Geometry.
		if a Simulation does exise, updates pdate_Simulation_Geometries table in database"""

		Simulation_Geometry = Sonnet_Coupling.Get_Simulation_Geometry(simid = simid)
		try:
			Simulation  = Mask_DB.Get_Simulation_Data(Simulation_Geometry, Sonnet_Coupling.Get_Simulation_Type(Simulation_Type))

		except:
			Simulation  = False

		if isinstance(Simulation,SimStruc.Simulation) is False:
			Simulation  = False
		else:
			Mask_DB.Update_Simulation_Geometries(simid,Simulation_Geometry)
		return Simulation 

	for simid in reversed(xrange(1,num_simulation+1)): #Use reversed to count down rather than up. (wide to narrow resonators.)
		Simulation_Type = 0
		if Force_Simulation == True:
			Simulation = Simulate(Simulation_Type = Simulation_Type)
		else:
			Simulation = Check_For_Simulation(Simulation_Type = Simulation_Type)
			if Simulation is not False:
				print('Skipping simulation for %s %s, simid = %i, because simulation already exists.' % (Sonnet_Coupling.Get_Simulation_Type(Simulation_Type), Sonnet_Coupling.Get_Simulation_Geometry(simid = simid),simid))
			else:
				Simulation = Simulate(Simulation_Type = Simulation_Type)

		resonators = Mask_DB.Get_Mask_Data('SELECT Design_Q, Design_Freq FROM Resonators WHERE simid = %i ORDER BY Design_Q ASC' % (simid),fetch = 'all')
		
		Simulation_Type = 1
		for resonator in resonators:
			if Qcheck(resonator[0], resonator[1]*pow(10,9), Simulation) is not True:
				print('Auxiliary Coupler Simulation Needed for geometry %s.' % Sonnet_Coupling.Get_Simulation_Geometry(simid = simid))
				if Force_Simulation == True:
					Simulate(Simulation_Type = Simulation_Type)
				else:
					Simulation = Check_For_Simulation(Simulation_Type = Simulation_Type)
					if Simulation is not False:
						print('Skipping Simulation for %s %s, simid = %i, becasue simulation already exists.' % (Sonnet_Coupling.Get_Simulation_Type(Simulation_Type), Sonnet_Coupling.Get_Simulation_Geometry(simid = simid),simid))
					else:
						Simulate(Simulation_Type = Simulation_Type)
				break

def Compute_All_Mask_Parameters():
	#get the total number of resonators..
	num_res = Mask_DB.Get_Mask_Data("SELECT resonator_id FROM Resonators ORDER BY resonator_id DESC", fetch = 'one')[0]

	for res in xrange(1,num_res+1):
		print("Function %s in module %s: Computing coupler and length for Resonator_ID = %i" % (__name__, __file__,res))
		Compute_Parameters.Compute_Coupler(res)

def Manual_Add_Simulation(Sonnet_Path,File_Name,Folder_Name,Mask_DB_Name = ":memory:"):
	if not Sonnet_Path.endswith(os.sep):
		raise RuntimeError('Sonnet_Path must end with "' + os.sep + '"')
	Mask_DB.Init_DB(Folder_Name,Mask_DB_Name) #it is not really necessary to creat Mask_DB. All we need to make sure of is that Simulation.db is created.
	Sonnet_Interface.Copy_From_Remote(Sonnet_Path,File_Name)
	Simulation = Parse_Sonnet_Response.Parse_Sonnet_Response(Sonnet_Path+File_Name)
	if Sonnet_Coupling.Get_Simulation_Type(File_Name.split('_')[0]) in set([0,1,2]):
		Mask_DB.Update_Simulation_Data(File_Name.split('_')[1], File_Name.split('_')[0], Simulation)


def Output_Parameters():
	'''Write a file Mask_Parameters.csv containing most mask parameters in the Mask_Folder'''
	cmd = """SELECT Computed_Parameters.resonator_id,Computed_Parameters.sensor_id,Resonators.Design_Freq,Resonators.Width,Computed_Parameters.Design_Q,Computed_Parameters.Coupler_Zone,Sensors.Through_Line_Width, 
	Computed_Parameters.Through_Line_Impedance,Computed_Parameters.Resonator_Impedance,Computed_Parameters.Coupler_Length,Computed_Parameters.Aux_Coupler_Length,Computed_Parameters.Resonator_Eeff,
	Computed_Parameters.Through_Line_Eeff,Computed_Parameters.Resonator_Length,Computed_Parameters.Meander_Pitch,Computed_Parameters.Meander_Zone,Computed_Parameters.Meander_Length,Computed_Parameters.Through_Line_Length,
	Computed_Parameters.Through_Line_Metal_Area,Computed_Parameters.Resonator_Metal_Area,Computed_Parameters.Patch_Area,Computed_Parameters.Turn_Extension,Computed_Parameters.Rungs,Computed_Parameters.Sensor_Pillar_Area,
	Computed_Parameters.Coupler_Phase_Change, Computed_Parameters.Max_Current_Length FROM Computed_Parameters, Resonators, Sensors WHERE Computed_Parameters.resonator_id = Resonators.resonator_id AND Computed_Parameters.sensor_id = Sensors.sensor_id"""


	records = Mask_DB.Get_Mask_Data(cmd)
	f = open(Mask_Folder + os.sep + 'Mask_Parameters.csv', mode = 'w')
	f.write(unicode("resonator_id,sensor_id,Design_Freq [GHz],Resonator_Width,Design_Q,Coupler_Zone,Through_Line_Width,Through_Line_Impedance,Resonator_Impedance,Coupler_Length,Aux_Coupler_Length,Resonator_Eeff,Through_Line_Eeff,Resonator_Length,Meander_Pitch,Meander_Zone,Meander_Length,Through_Line_Length,Through_Line_Metal_Area,Resonator_Metal_Area,Resonator_Patch_Area,Turn_Extension,Rungs,Sensor_Pillar_Area,Coupler_Phase_Change [rad], Max_Current_Length\n"))

	data = ''
	for rec in records:
		data = data + unicode(str(rec).lstrip('(').rstrip(')')+'\n')

	f.write(data)
	#probably want to remove final ',\n' manually
	f.close()

def Qcheck(Design_Q, Design_Freq, Simulation):
	"""Returns True if Design_Q at Design_Frequency can be attained in simulation """
	low_enough = True

	if Simulation.Qmin(Design_Freq) > Design_Q:
		low_enough = False

	return low_enough

def Draw_Mask():
	''' Draws Mask and saves gds file. Displays Mask in  gds viewer. Then writes output cvs file from the computed mask parameters'''
	D_M.Draw_Mask(Save_Path = Mask_Folder, Through_Line_Layer = Through_Line_Layer , Resonator_Trace_Layer = Resonator_Trace_Layer, Pillar_Layer = Pillar_Layer)
	print('Writing mask parameters to .csv file.')
	Output_Parameters()


def View_Mask(Structure = '', Mask_File = ''):
	'''Displays specified cells in the mask file (full path) Mask_File.
	If Structure = '', displays all cells contained in Mask_Filie
	if Structure = 'R3', displays only resonator 3, for example
	if Structure = 'S7', displays only sensor 7, for example
	if Structure = 'Mask', only displaces the flattened mask cell
	if Structure = 'Top', displays all top level cells (cells not referenced by any other cells)'''

	gdsii = Load_Mask(Mask_File = '')

	if Structure == '':
		gdspy.LayoutViewer()
	elif Structure.startswith('R'): #The Case for Resonators
		res_id = int(Structure.strip('R'))
		cell_name = Mask_DB.Get_Mask_Data("Select Resonator_Cell_Name from Computed_Parameters where resonator_id = %i" % (res_id), fetch = 'one')[0]
		gdspy.LayoutViewer(cells = str(cell_name))
	elif Structure.startswith('S'): #The Case for Sensors
		sensor_id = int(Structure.strip('S'))
		cell_name = Mask_DB.Get_Mask_Data("Select Sensor_Cell_Name from Computed_Parameters where sensor_id = %i" % (sensor_id), fetch = 'one')[0]
		gdspy.LayoutViewer(cells = str(cell_name))
	elif Structure == 'Mask':# this is the flattened top cell.
		gdspy.LayoutViewer(cells = 'Mask')
	elif Structure == 'Top': # Includes all cess not reference by a any other cells
		gdspy.LayoutViewer(cells = gdsii.top_level())

def Load_Mask(Mask_File = ''):
	'''Loads mask into memory'''
	if Mask_File == '':
		Mask_File = Mask_Folder+ os.sep +'mask.gds'

	gdspy.Cell.cell_dict = {}
	gdsii = gdspy.GdsImport(Mask_File)
	for cell_name in gdsii.cell_dict:
		gdsii.extract(cell_name)

	global mask_file_loaded
	mask_file_loaded = 1

	return gdsii


def Get_Polygons(Structure):
	'''Returns dictionary of Polygons by layer for the Spefied structure. Structures are Sensors or Resonators for example
	Structure = 'S1' is Sensor 1
	Structir = 'R16' is Resonator 16'''


	cell_ref = Get_Cell_Reference(Structure)
	cell_polygons = cell_ref.get_polygons(by_layer=True, depth=None)
	

	return cell_polygons

def Get_Cell_Reference(Structure, Origin=(0, 0), Rotation=None, Magnification=None, X_reflection=False ):
	'''Returns a GDSPY cell receference for the Spefied structure. Structures are Sensors or Resonators for example
	Structure = 'S1' is Sensor 1
	Structir = 'R16' is Resonator 16'''

	if mask_file_loaded == 0:
		Load_Mask(Mask_File = '')

	if Structure == '':
		raise RuntimeError('Must Specify a Structure')
	elif Structure.startswith('R'): #The Case for Resonators
		res_id = int(Structure.strip('R'))
		cell_name = Mask_DB.Get_Mask_Data("Select Resonator_Cell_Name from Computed_Parameters where resonator_id = %i" % (res_id), fetch = 'one')[0]
		cell_ref = gdspy.CellReference(cell_name, origin=Origin, rotation=Rotation, magnification=Magnification, x_reflection=X_reflection)
		
	elif Structure.startswith('S'): #The Case for Sensors
		sensor_id = int(Structure.strip('S'))
		cell_name = Mask_DB.Get_Mask_Data("Select Sensor_Cell_Name from Computed_Parameters where sensor_id = %i" % (sensor_id), fetch = 'one')[0]
		cell_ref = gdspy.CellReference(cell_name, origin=Origin, rotation=Rotation, magnification=Magnification, x_reflection=X_reflection)
		
	else:
		raise RuntimeError('Unrecognized Structure')

	return cell_ref









