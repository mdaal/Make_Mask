import Mask_DB
import warnings
import Sonnet_Coupling
import Sonnet_Interface
import Parse_Sonnet_Response
import Compute_Parameters


warnings.filterwarnings('always')

def Make_Mask(Folder_Name,File_Name = ":memory:"):

	num_simulation = Mask_DB.Init_DB(Folder_Name,File_Name)
	return num_simulation


def Execute_Coupler_Simulations(num_simulation):
	for simid in xrange(1,num_simulation+1):

		#File_Name looks like CouplerSweep_TLW360TLG00RW200SG03ST500E1120_20130228_143425.son
		#Simulation_Geometry looks like TLW360TLG00RW200SG03ST500E1120
		Sonnet_Path,  File_Name, Simulation_Geometry, Simulation_Type_Name,Coupler_Space = Sonnet_Coupling.Sonnet_Coupling(simid, Simulation_Type = 0)
		print('Simulating Line Coupler geometry %s, %i of %s' % (Simulation_Geometry,simid,num_simulation))
		#response = Sonnet_Interface.Run_EM_nogui(Sonnet_Path,File_Name, Terminal_Output = True)
		Mask_DB.Update_Simulation_Geometries(simid,Simulation_Geometry)
		Simulation = Parse_Sonnet_Response.Parse_Sonnet_Response("log_response.log")
		Mask_DB.Update_Simulation_Data(Simulation_Geometry, Simulation_Type_Name, Simulation)
		resonators = Mask_DB.Get_Mask_Data('SELECT Design_Q, Design_Freq FROM Resonators WHERE simid = %i ORDER BY Design_Q ASC' % (simid),fetch = 'all')
		
		for resonator in resonators:
			if Qcheck(resonator[0], resonator[1]*pow(10,9), Simulation) is not True:
				print('Auxiliary Coupler Simulation Needed for geometry %s. Performing Simulation ...' % Simulation_Geometry)
				Sonnet_Path,  File_Name, Simulation_Geometry, Simulation_Type_Name,Coupler_Space = Sonnet_Coupling.Sonnet_Coupling(simid, Simulation_Type = 1)
				#response = Sonnet_Interface.Run_EM_nogui(Sonnet_Path,File_Name, Terminal_Output = True)
				Simulation = Parse_Sonnet_Response.Parse_Sonnet_Response("aux_log_response.log")
				Mask_DB.Update_Simulation_Data(Simulation_Geometry, Simulation_Type_Name, Simulation)
				break

def Compute_Lengths_And_Couplers():
	#get the total number of resonators..
	num_res = Mask_DB.Get_Mask_Data("SELECT resonator_id FROM Resonators ORDER BY resonator_id DESC", fetch = 'one')[0]

	for res in xrange(1,num_res+1):
		print("Function %s in module %s: Computing coupler and length for Resonator_ID = %i" % (__name__, __file__,res))
		Compute_Parameters.Compute_Coupler(res)



def Qcheck(Design_Q, Design_Freq, Simulation):
	"""Returns True if Design_Q at Design_Frequency can be attained in simulation """
	low_enough = True

	if Simulation.Qmin(Design_Freq) > Design_Q:
		low_enough = False

	return low_enough