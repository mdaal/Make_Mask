import numpy as np
from  Draw_Resonator import Draw_Resonator
import gdspy
import os
import Mask_DB

def Draw_Sensor(Sensor_Number, Through_Line_Layer = 1, Resonator_Trace_Layer = 2, Pillar_Layer = 3):
	'''
	This Function draws a sensor. It positions the resonators according to the mask definition input files. 
	Its also draws the pillars outside of the bounding box of the resonators, the sensor die cut lines and
	the through line.
	Origin of the Sensor is the lower left corner.
	'''

	#For Test Only! Remove when deployed
	#gdspy.Cell.cell_dict = {}

	# Obtain Sensor Parameters
	Sensor_Params = Mask_DB.Get_Mask_Data("SELECT X_Length, Y_Length, Cut_Line_Width, Pillar_Diameter, Pillar_Grid_Spacing, Pillar_Clearance, Through_Line_Type, Through_Line_Width, Through_Line_Turn_Radius,Through_Line_Gap, Through_Line_Edge_Offset FROM Sensors WHERE sensor_id = " + str(Sensor_Number),'all')
	#sql_cmd = "SELECT X_Length, Y_Length, Cut_Line_Width, Pillar_Diameter, Pillar_Grid_Spacing, Pillar_Clearance, Through_Line_Type, Through_Line_Width, Through_Line_Turn_Radius,Through_Line_Gap, Through_Line_Edge_Offset FROM Sensors WHERE Sensor = " + str(Sensor_Number)
	#Cursor.execute(sql_cmd)
	#Sensor_Params = Cursor.fetchall()

	#There should only be one sensor returned from database. We make sure of this.
	if len(Sensor_Params) > 1:
		print("Something is wrong. There are more than one senor #" + str(Sensor_Number) + ". Using the first one pulled.")

	Pillar_Grid_Spacing_Reduction_Factor = 3.0

	X_Length, Y_Length, Cut_Line_Width, Pillar_Diameter, Pillar_Grid_Spacing, Pillar_Clearance, Through_Line_Type, Through_Line_Width, Through_Line_Turn_Radius,Through_Line_Gap, Through_Line_Edge_Offset = Sensor_Params[0]
	Pillar_Radius = Pillar_Diameter/2
	Pillar_Grid_Spacing = Pillar_Grid_Spacing*Pillar_Grid_Spacing_Reduction_Factor
	#Initialize Sensor Cell
	sensor_cell_name = 'SENSOR_'+str(Sensor_Number)
	sensor_cell = gdspy.Cell(sensor_cell_name,exclude_from_global=True)


	
	
	# We draw the cut lines by boolean operation on two squares defining the die outline
	poly1 = gdspy.Rectangle(Resonator_Trace_Layer, (0, 0), (X_Length, Y_Length))
	poly2 = gdspy.Rectangle(Resonator_Trace_Layer, (Cut_Line_Width, Cut_Line_Width), (X_Length-Cut_Line_Width, Y_Length-Cut_Line_Width))
	primitives = [poly2,poly1]
	subtraction = lambda p1, p2: p2 and not p1
	sensor_cell.add(gdspy.boolean(Resonator_Trace_Layer, primitives, subtraction, max_points=199))

	#Bare sensor cell is sensor cell without text and cutlines
	bare_sensor_cell_name = 'BARE_'+sensor_cell_name
	bare_sensor_cell = gdspy.Cell(bare_sensor_cell_name,exclude_from_global=False)

	#Add the name of the sensor in the lower left of the die
	Text_Offset = 100
	sensor_cell.add(gdspy.Text(Resonator_Trace_Layer, 'S' + str(Sensor_Number), 300, (Cut_Line_Width+Text_Offset, Cut_Line_Width+Text_Offset)))

	#Draw Throughline
	#assuming L shape
 	Though_Line_Trace = gdspy.Path(Through_Line_Width, (X_Length/2, 0))
 	Though_Line_Trace.segment(Through_Line_Layer, Through_Line_Edge_Offset + Through_Line_Width/2 - Through_Line_Turn_Radius, '+y')
 	Though_Line_Trace.turn(Through_Line_Layer, Through_Line_Turn_Radius, 'l')
	Though_Line_Trace.segment(Through_Line_Layer, (X_Length/2)-Through_Line_Edge_Offset-Through_Line_Width/2 - 2*Through_Line_Turn_Radius, '-x')
	Though_Line_Trace.turn(Through_Line_Layer, Through_Line_Turn_Radius, 'r')
	Though_Line_Trace.segment(Through_Line_Layer, Y_Length-2*Through_Line_Edge_Offset-Through_Line_Width - 2*Through_Line_Turn_Radius, '+y')
	_res_x_zero = Though_Line_Trace.x
	Though_Line_Trace.turn(Through_Line_Layer, Through_Line_Turn_Radius, 'r')
	_res_y_zero = Though_Line_Trace.y	
	Though_Line_Trace.segment(Through_Line_Layer, (X_Length/2)-Through_Line_Edge_Offset-Through_Line_Width/2 - 2*Through_Line_Turn_Radius, '+x')
	Though_Line_Trace.turn(Through_Line_Layer, Through_Line_Turn_Radius, 'l')
	Though_Line_Trace.segment(Through_Line_Layer, Through_Line_Edge_Offset + Through_Line_Width/2 - Through_Line_Turn_Radius, '+y')

	bare_sensor_cell.add(Though_Line_Trace)

	#This is a test rectange to check the through line placement
	#sensor_cell.add(gdspy.Rectangle(Resonator_Trace_Layer, (Through_Line_Edge_Offset, Through_Line_Edge_Offset), (Through_Line_Edge_Offset+Through_Line_Width/2 + Through_Line_Turn_Radius, Through_Line_Edge_Offset+Through_Line_Width/2 + Through_Line_Turn_Radius)))
	
	#Starting position of first resonator
	_res_x_zero += (Through_Line_Width/2)
	_res_y_zero += (-Through_Line_Width/2)
	_cur_Res_y_pos = _res_y_zero


	Res_IDs = Mask_DB.Get_Mask_Data("SELECT resonator_id, Coupler_Zone, Head_Space, Design_Freq,Design_Q FROM Resonators WHERE sensor_id = " + str(Sensor_Number),'all')
	#sql_cmd = "SELECT Design_Freq, Width, Design_Q, Head_Space, Coupler_Zone, Meander_Pitch, Meander_Zone FROM Resonators WHERE Sensor = " + str(Sensor_Number)
	#Cursor.execute(sql_cmd)
	#Res_IDs = Cursor.fetchall()
	

	
	#For boolean subtraction, however does not work due to insufficient memory
	# #Initialize Resonator Mask Cell, which will contain rectangles positioned over the resonators
	# res_mask_cell_name = 'S'+str(Sensor_Number)+'ResMask'
	# res_mask_cell = gdspy.Cell(res_mask_cell_name, exclude_from_global=True)

	_pillar_x_index = (Pillar_Grid_Spacing+Pillar_Diameter)/2
	_pillar_y_index = Y_Length - (Pillar_Grid_Spacing+Pillar_Diameter)/2

	Res_Number = 1

	
	for ID in Res_IDs:
		resonator_id,Coupler_Zone, Head_Space,Design_Freq,Design_Q = ID
		Resonator_Name = 'F' + str(Design_Freq) + ' Qc' + str(int(Design_Q)) + ' R' + str(resonator_id)
		#Resonator_Name = 'S' + str(Sensor_Number) + 'R' + str(Res_Number) + '#' + str(resonator_id)
		resonator_cell,_y_initial = Draw_Resonator(Resonator_Name=Resonator_Name,Resonator_ID=resonator_id, Resonator_Trace_Layer = Resonator_Trace_Layer, Pillar_Layer = Pillar_Layer, Y_Pitch_Tight = True, X_Pitch_Tight = True,Update_DB = True)

		_cur_Res_x_pos = Coupler_Zone + _res_x_zero
		_cur_Res_y_pos += -Head_Space-_y_initial
		_curr_Res_ref =  gdspy.CellReference(resonator_cell, (_cur_Res_x_pos, _cur_Res_y_pos))
		bare_sensor_cell.add(_curr_Res_ref)
		_bounding_box_edges = resonator_cell.get_bounding_box() + np.array([[_cur_Res_x_pos, _cur_Res_y_pos],[_cur_Res_x_pos, _cur_Res_y_pos]])
		#sensor_cell.add(  gdspy.Rectangle(Through_Line_Layer, (_bounding_box_edges[0][0], _bounding_box_edges[0][1]), (_bounding_box_edges[1][0], _bounding_box_edges[1][1])))

		#For boolean subtraction, however does not work due to insufficient memory
		#res_mask_cell.add(gdspy.Rectangle(Through_Line_Layer, (_bounding_box_edges[0][0], _bounding_box_edges[0][1]), (_bounding_box_edges[1][0], _bounding_box_edges[1][1])))

		#_total_x_distance = _bounding_box_edges[1][0] - _bounding_box_edges[0][0] #not used currently
		_total_y_distance = _bounding_box_edges[1][1] - _bounding_box_edges[0][1]
		_cur_Res_y_pos += -_total_y_distance 

		while _pillar_y_index >= _cur_Res_y_pos:
			while _pillar_x_index <= X_Length - Pillar_Radius:
				if not in_rectangle((_pillar_x_index, _pillar_y_index),_bounding_box_edges,Pillar_Radius):#Pillar_Radius+Pillar_Grid_Spacing):
					bare_sensor_cell.add(gdspy.Round(Pillar_Layer, (_pillar_x_index, _pillar_y_index), Pillar_Radius,number_of_points=60))
				_pillar_x_index += Pillar_Grid_Spacing
			_pillar_x_index = (Pillar_Grid_Spacing+Pillar_Diameter)/2
			_pillar_y_index -= Pillar_Grid_Spacing

		Res_Number += 1 
	
	while _pillar_y_index >= Pillar_Radius:
		while _pillar_x_index <= X_Length - Pillar_Radius:
			bare_sensor_cell.add(gdspy.Round(Pillar_Layer, (_pillar_x_index, _pillar_y_index), Pillar_Radius,number_of_points=60))
			_pillar_x_index += Pillar_Grid_Spacing
		_pillar_x_index = (Pillar_Grid_Spacing+Pillar_Diameter)/2
		_pillar_y_index -= Pillar_Grid_Spacing
	
	bare_sensor_cell_ref =  gdspy.CellReference(bare_sensor_cell, (0,0))
	sensor_cell.add(bare_sensor_cell_ref)	

	Sensor_Dict = {"Through_Line_Metal_Area":Though_Line_Trace.area(),"Through_Line_Length":Though_Line_Trace.length, "Sensor_Pillar_Area": sensor_cell.area(by_layer=True)[Pillar_Layer], "sensor_id":Sensor_Number, "Sensor_Cell_Name":'"'+bare_sensor_cell_name+'"'}
	for ID in Res_IDs:
		resonator_id = ID[0]
		Mask_DB.Update_Computed_Parameters(resonator_id, Sensor_Dict)

	#Insufficuent Memory to perform boolean subtraction below
	# #Initialize Pillar Cell, which will contain a grid of pillars for the sensor
	# pillar_cell_name = 'S'+str(Sensor_Number)+'Pillars'
	# pillar_cell = gdspy.Cell(pillar_cell_name, exclude_from_global=True)
	# pillar_cell.add(gdspy.Round(Pillar_Layer, (0, 0), Pillar_Radius))
	# #Perform boolean subtraction of resonator mask rectangels
	# num_pillars_x =  (X_Length-Pillar_Grid_Spacing-2*Pillar_Radius)%Pillar_Grid_Spacing
	# num_pillars_y =  (Y_Length-Pillar_Grid_Spacing-2*Pillar_Radius)%Pillar_Grid_Spacing
	# primitives = [gdspy.CellReference(res_mask_cell),gdspy.CellArray(pillar_cell, int(num_pillars_x), int(num_pillars_y), (Pillar_Grid_Spacing, Pillar_Grid_Spacing) ,(Pillar_Grid_Spacing/2 + Pillar_Radius, Pillar_Grid_Spacing/2 + Pillar_Radius),magnification=1)]
	# sensor_cell.add(gdspy.boolean(Pillar_Layer, primitives, sub, max_points=199))


	# name = os.path.abspath(os.path.dirname(os.sys.argv[0])) + os.sep + 'single_sensor'

	# ## Output the layout to a GDSII file (default to all created cells).
	# ## Set the units we used to micrometers and the precision to nanometers.
	# gdspy.gds_print(name + '.gds', unit=1.0e-6, precision=1.0e-9)
	# print('Sample gds file saved: ' + name + '.gds')

	# ## Save an image of the boolean cell in a png file.  Resolution refers
	# ## to the number of pixels per unit in the layout. Resolution changed from 4
	# ## to 1 to avoid  "malloc_error"
	# #gdspy.gds_image([resonator_cell], image_name=name, resolution=1, antialias=4)

	# #comment out save as png for speed
	# #print('Image of the boolean cell saved: ' + name + '.png')

	# ## Import the file we just created, and extract the cell 'POLYGONS'. To
	# ## avoid naming conflict, we will rename all cells.
	# #gdsii = gdspy.GdsImport(name + '.gds', rename={sensor_cell_name:'IMPORT_SENSOR'})

	# ## Now we extract the cells we want to actually include in our current
	# ## structure. Note that the referenced cells will be automatically
	# ## extracted as well.
	# #gdsii.extract(sensor_cell_name)
	    
	# ## View the layout using a GUI.  Full description of the controls can
	# ## be found in the online help at http://gdspy.sourceforge.net/
	# gdspy.LayoutViewer(colors=[None] * 64) # for outlined polygons
	# #gdspy.LayoutViewer()
	return sensor_cell
   
	
def in_rectangle(pt,_bounding_box_edges,padding):
	x_min = _bounding_box_edges[0][0] - (padding)
	y_min = _bounding_box_edges[0][1] - (padding)
	x_max = _bounding_box_edges[1][0] + (padding)
	y_max = _bounding_box_edges[1][1] + (padding)

	in_box = False
	if (pt[0] > x_min) and (pt[0] < x_max):
		if (pt[1] > y_min) and (pt[1] < y_max):
			in_box = True
	return in_box

def sub(p1,p2):
	#global n
	#print('p1 is %f and p2 is %f and n is %i' % (p1,p2,n))
	#n = n+1
	return ((p2 and not p1))
