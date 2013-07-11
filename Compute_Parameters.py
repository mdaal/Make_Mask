import Mask_DB
import scipy as sp
#import Draw_Resonator
import SimStruc
from scipy import constants
import warnings

C = constants.c * pow(10,6) #micrometers per second 
#C = 2.998*pow(10,14)

warnings.filterwarnings('always')

# def Define_Coupler(Resonator_ID):

# 	Draw_Resonator.Draw_Resonator(Resonator_Name='',Resonator_ID=Resonator_ID, Resonator_Trace_Layer = Resonator_Trace_Layer, Pillar_Layer = Pillar_Layer, Y_Pitch_Tight = True, X_Pitch_Tight = True,Update_DB = True)
	
# 	out = Mask_DB.Get_Mask_Data("SELECT Computed_Parameters.Meander_Zone, Computed_Parameters.Meander_Pitch, Resonators.Width, Resonators.Design_Freq, Resonators.Design_Q,\
# 		Sensors.Through_Line_Gap,Sensors.Through_Line_Width,Sensors.Through_Line_Edge_Offset,Sensors.X_Length, Simulation_Names.Simulation_Name FROM Resonators, Sensors, \
# 		Simulation_Names, Computed_Parameters WHERE Sensors.sensor_id = Resonators.sensor_id AND Resonators.resonator_id = Computed_Parameters.resonator_id AND \
# 		Simulation_Names.simid = Resonators.simid AND Resonators.resonator_id = " + str(Resonator_ID) ,'one')
	
# 	MZ   = out[0] # um - Actual Meander Zone 
# 	MP   = out[1] # um - Actual Meander Pitch
# 	RW   = out[2] # um - Resonator Width
# 	Freq = out[3]*pow(10,9) # Hz - Resonator Design Freq
# 	#Resonator_Length
# 	Qc   = out[4]	
# 	#Resonator_Eeff
# 	#Through_Line_Eeff
# 	#Resonator_Impedance
# 	#Through_Line_Impedance
# 	TLG = out[5] # um - Through Line Gap
# 	TLW = out[6] # um - Through Line Width
# 	TLE = out[7] # um - Through Line Edge Offset
# 	X_Length = out[8] # um - Device X Length
# 	Simulation_Name = out[9]

	 

# 	#Max_Coupler_Offset = Sim.Pmax

# 	#Dont want resonators to come closer than 1500 um to die edge
# 	Max_Coupler_Zone = X_Length - (TLE + TLW + TLG) - (MZ + MP) - 1500 

	
def Estimate_Length(Resonator_ID):
	Freq = Mask_DB.Get_Mask_Data("SELECT Design_Freq FROM Resonators WHERE resonator_id =" + str(Resonator_ID) ,'one')[0] * pow(10,9)
	
	Eeff = 1.0

	Phase_Velocity = C / sp.sqrt(Eeff);

	Length = (Phase_Velocity / Freq)*(1./2) #Factor of 1/2 is for half wave resonator

	Mask_DB.Update_Computed_Parameters(Resonator_ID, {"Resonator_Length" : Length})
	return Length

def Load_Freq_Q_Geo(Resonator_ID):
	Freq, Design_Q, Geometry = Mask_DB.Get_Mask_Data("SELECT Resonators.Design_Freq, Resonators.Design_Q, Simulation_Geometries.Simulation_Geometry FROM Resonators, Simulation_Geometries WHERE Simulation_Geometries.simid = Resonators.simid AND Resonators.resonator_id =" + str(Resonator_ID) ,'one')

	Freq = Freq * pow(10,9)
	Geometry = str(Geometry)
	return Freq, Design_Q, Geometry

def beta(Resonator_ID):
	"""returns phase change per unit length in rad/um"""
	Freq, Design_Q, Geometry = Load_Freq_Q_Geo(Resonator_ID)

	Sim = Mask_DB.Get_Simulation_Data(Geometry, "CouplerSweep" )


	if isinstance(Sim,SimStruc.Simulation):
		Sim.values("Eeff")
		Eeff = Sim.interp(Freq,Sim.Pmax)[2].real  #Interpolate to find real part of Eeff of port 3 (the resonator) at the design frequence and for max coupler offset. (choice of coupler offset should not matter)
	else:
		Eeff = 1.0
		warnings.warn("Function %s in module %s: Cannot obtain Eeff because no Simulation structure found for Resonator_ID = %i. Using Eeff =  %f" % (__name__, __file__,Resonator_ID, Eeff))

	return 2.0*sp.pi*Freq*sp.sqrt(Eeff)/C
	
def Compute_Length(Resonator_ID):
	b = beta(Resonator_ID)

	Length = sp.pi/b #from theta = beta*(2L), theta is 2*pi and 2*L because 1/2-wave resonator

	return Length

def Q2S(Q):
	"""Returns Scattering Parameter Value the correcponds to Q value"""
	return sp.sqrt(sp.pi/Q) #assumes 1/2-wave resonator


def Compute_Coupler(Resonator_ID):
	""" Computes Line coupler length and  Aux coupler length, if an Aux coupler is needed. Uses this to compute Resonator Length (which is length of the meander excluding the coupler).
		Adds resonator and through line Eeff and Port_Z to table of computed parameters"""
	Coupler_Length = 0.0
	Aux_Coupler_Length = 0.0
	_Length = 0.0
	b = beta(Resonator_ID)
	Freq, Design_Q, Geometry = Load_Freq_Q_Geo(Resonator_ID)
	Coupler_Zone = Mask_DB.Get_Mask_Data("SELECT Coupler_Zone FROM Resonators Where resonator_id = " + str(Resonator_ID) ,'one')[0]

	### Coupler Zone shall be greater than a coupler_offset which yields Coupler_Zone_Q_Limit 
	Coupler_Zone_Q_Limit = float(pow(10,10))
	### in general "Coupler Zone Q" is the Q attained using a coupler_offset = coupler_zone 
	
	Sim = Mask_DB.Get_Simulation_Data(Geometry, "CouplerSweep")

	######## Extract  Resonator and Throughline Eeff #####
	Sim.values('Eeff')
	Eeff = sp.absolute(Sim.interp(Freq,Parameter_Value = Sim.Pmax))
	Resonator_Eeff  = Eeff[2]
	Through_Line_Eeff = Eeff[1]

	Sim.values('Port_Z0')
	Port_Z0 = sp.absolute(Sim.interp(Freq,Parameter_Value = Sim.Pmax))
	Resonator_Impedance  = Port_Z0[2]
	Through_Line_Impedance = Port_Z0[1]	
	########
	
	Sim.values('Port_S')
	try:
		offset = Sim.optvalues(Freq,Q2S(Coupler_Zone_Q_Limit),2,0)[0] #May fail if S31 at Sim.Pmax yelds  Q < Coupler_Zone_Q_Limit 
	except:
		offset = Sim.Pmax
		print("Function %s in module %s: For Resonator_ID = %i, insufficient Coupler_Offset in Simulation to attain Coupler Zone Q > %i" % (__name__, __file__,Resonator_ID,Coupler_Zone_Q_Limit))

	if offset > Coupler_Zone:
		print("Function %s in module %s: For Resonator_ID = %i, Coupler_Zone Increased to make Coupler Zone Q closer to %i" % (__name__, __file__,Resonator_ID,Coupler_Zone_Q_Limit))
		offset = Coupler_Zone


	delta_L = Sim.Pmax - Coupler_Zone #is a Length, um
	if delta_L <= 0:
		warnings.warn('Coupler_Zone is greater than Coupler_Offset')
	delta_coupler_phase = -2.0 * b * delta_L #2 is becasue 1/2-wave resonator, phase is  in radians 

	if Design_Q < Sim.Qmin(Freq): #Condition where an Aux is needed.
		Sim = Mask_DB.Get_Simulation_Data(Geometry, "AuxCouplerSweep")
		Sim.values('Port_S')

		Coupler_Length = Coupler_Zone 

		if Design_Q < Sim.Qmin(Freq): #Condition where an Aux at its maximum length it not sufficient
			print("Function %s in module %s: Design_Q is lower than minimum acheivable Q with Pad Coupler for Resonator_ID = %i. Using Max Coupler Pad Length" % (__name__, __file__,Resonator_ID))
			
			####### CAUTION ########
			Design_Q = Sim.Qmin(Freq)
			########################

		Aux_Coupler_Length = Sim.optvalues(Freq,Q2S(Design_Q),2,0)[0]
		_Length = Aux_Coupler_Length
	else:
		Coupler_Length = Sim.optvalues(Freq,Q2S(Design_Q),2,0)[0]
		_Length = Coupler_Length

	
	#compute resonator length
	Coupler_Phase_Change = sp.absolute(sp.angle(Sim.interp(Freq,Parameter_Value = _Length)[2,2], deg = False))  + delta_coupler_phase #radians

	Resonator_Phase_Length = 2.0*sp.pi - Coupler_Phase_Change

	#Note: Computed Resonator Length has been shortened by presence of coupler. phase change of Coupler has been subtracted from vacuum lenght or resonator.
	Resonator_Length = Resonator_Phase_Length/(2*b)

	#This is the "midpoint", as determined by phase  =  pi, along the resonator length where the current is maximal. NOTE: THis is along the meandered portion of the resonator. The couple has been substracted
	Max_Current_Length =  sp.around((Resonator_Phase_Length-sp.pi)/(2*b),decimals=3)

	#print(Sim.Current_Attribute,{"Coupler_Zone" : Coupler_Zone, "Design_Q" : Design_Q, "Aux_Coupler_Length" : Aux_Coupler_Length, "Coupler_Length" : Coupler_Length, "Coupler_Phase_Change" : Coupler_Phase_Change})


	Mask_DB.Update_Computed_Parameters(Resonator_ID, {"Coupler_Zone" : Coupler_Zone, "Design_Q" : Design_Q, "Aux_Coupler_Length" : Aux_Coupler_Length, "Coupler_Length" : Coupler_Length, "Coupler_Phase_Change" : Coupler_Phase_Change, "Resonator_Length" : Resonator_Length,"Resonator_Eeff":Resonator_Eeff, "Through_Line_Eeff":Through_Line_Eeff, "Resonator_Impedance":Resonator_Impedance,"Through_Line_Impedance":Through_Line_Impedance,"Max_Current_Length" : Max_Current_Length} )	
	return (Coupler_Zone,Design_Q,Aux_Coupler_Length,Coupler_Length, sp.rad2deg(Coupler_Phase_Change),Resonator_Length)

	

	

