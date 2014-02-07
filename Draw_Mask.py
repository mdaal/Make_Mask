import numpy as np
#from  Draw_Sensor import Draw_Sensor
import gdspy
import os
import Mask_DB

text_cell_name = 'MASK_TEXT'
text_cell = gdspy.Cell(text_cell_name,exclude_from_global=True)
current_sensor_origin = np.array([0,0])
current_resonator_origin = np.array([0,0])
resonator_label_location = np.array([0,0])



def Draw_Mask(Save_Path = '.', Through_Line_Layer = 1, Resonator_Trace_Layer = 2, Pillar_Layer = 3):
	
	#For Test Only! Remove when deployed
	gdspy.Cell.cell_dict = {}

	# Obtain Sensor Parapeters
	Mask_Params = Mask_DB.Get_Mask_Data("SELECT X_Length, Y_Length, Rows, Columns FROM Wafer WHERE wafer_id = 1",'all')
	#sql_cmd = "SELECT X_Length, Y_Length, Rows, Columns FROM Wafer WHERE id = 1"
	#Cursor.execute(sql_cmd)
	#Mask_Params = Cursor.fetchall()

	Mask_Cell_X_Length, Mask_Cell_Y_Length, Mask_Rows, Mask_Columns= Mask_Params[0]

	# Obtain list of sensor ids
	Sensor_Nums = Mask_DB.Get_Mask_Data("SELECT sensor_id FROM Sensors",'all')
	#sql_cmd = "SELECT id, Sensor FROM Sensors"
	#Cursor.execute(sql_cmd)
	#Sensor_Nums = Cursor.fetchall()	
	

	#Initialize Mask Cell
	mask_cell_name = 'MASK'
	global mask_cell
	mask_cell = gdspy.Cell(mask_cell_name)

	sens_index = 0

	for col in xrange(Mask_Columns):
		for row in xrange(Mask_Rows):
			global current_sensor_origin
			current_sensor_origin = np.array([Mask_Cell_X_Length*row + -Mask_Cell_X_Length*Mask_Rows/2, -Mask_Cell_Y_Length*(col+1) + Mask_Cell_Y_Length*Mask_Columns/2])
			print('row %i, col %i' % (row,col))
			sensor_cell = Draw_Sensor(Sensor_Nums[sens_index][0], Through_Line_Layer = Through_Line_Layer, Resonator_Trace_Layer = Resonator_Trace_Layer, Pillar_Layer = Pillar_Layer)

			mask_cell.add(gdspy.CellReference(sensor_cell, tuple(current_sensor_origin)))
			sens_index += 1

	#Add text for all cells incldings the sensor labels and the resonator labels
	mask_cell.add(gdspy.CellReference(text_cell, (0,0)))
	
	##################
	# Draw Alignment Marks
	##################

	def draw_alignment(Inner_Cross_Layer, Outer_Cross_Layer,Inner_Cross_Thickness,Outer_Cross_Thickness,Outer_Cross_Width, Guidelines = True, Outer_Only = False, *arg):
		""" Inner_Cross_Thickness is line width of cross
		Outer_Cross_Thickness is line width of outer cross
		Outer_Cross_Width is overall width and height of cross
		Guidelines = True -- draws stepped guidlines which point to alignment cross
		Outer_Only =  True  -- draws only the outer features on each layer: Inner_Cross_Layer, Outer_Cross_Layer
		if Outer_Cross_Thickness == 0 only the inner features are drawn on each layer: Inner_Cross_Layer, Outer_Cross_Layer
		"""

		Inner_Cross_Thickness = float(Inner_Cross_Thickness)
		Outer_Cross_Thickness = float(Outer_Cross_Thickness)
		Outer_Cross_Width = float(Outer_Cross_Width)
		if arg is not ():
			ang = arg[0]
		else:
			ang = 0

		def draw_cross(Layer,cross_line_width,cross_width):
			"""cross_line_width is line width of cross
			cross_width is Overall width and height of cross """
			P_1 = gdspy.Path(cross_line_width, (-cross_width/2, 0))
			P_1.segment(cross_width, '+x', layer = Layer)
			P_2 = gdspy.Path(cross_line_width, (0,-cross_width/2))
			P_2.segment((cross_width/2)-(cross_line_width/2), '+y', layer = Layer)
			P_3 = gdspy.Path(cross_line_width, (P_2.x,P_2.y+cross_line_width))
			P_3.segment((cross_width/2)-(cross_line_width/2), '+y', layer = Layer)
			return P_1.polygons+P_2.polygons+ P_3.polygons

		def draw_guide_lines(Layer,Line_Width_Start,Length,Steps):
			polygons = []
			for i in xrange(1,Steps+1):
				polygons.append(gdspy.Path(Line_Width_Start*i,(Outer_Cross_Width/2 + Inner_Cross_Thickness +(i-1)*(Length/Steps),0)).segment(Length/Steps,'+x',layer = Layer).polygons)
			for i in xrange(1,Steps+1):
				polygons.append(gdspy.Path(Line_Width_Start*i,(-(Outer_Cross_Width/2 + Inner_Cross_Thickness +(i-1)*(Length/Steps)),0)).segment(Length/Steps,'-x', layer = Layer).polygons)
			return 	reduce(lambda x, y: x+y,polygons)

		cross_line_width = Inner_Cross_Thickness  #line width of cross
		cross_width = Outer_Cross_Width - 2*Outer_Cross_Thickness # overall width and height of cross

		i = draw_cross(Inner_Cross_Layer,cross_line_width,cross_width)
		inner_cross_poly_set = gdspy.PolygonSet(i, layer =Inner_Cross_Layer ).rotate(ang, center=(0, 0))

		if Outer_Cross_Thickness==0:
			o = draw_cross(Outer_Cross_Layer,cross_line_width,cross_width)
			outer_cross_poly_set = gdspy.PolygonSet(o, layer =Outer_Cross_Layer ).rotate(ang, center=(0, 0))
		else:
			o = draw_cross(Outer_Cross_Layer,3*cross_line_width,Outer_Cross_Width)
			primitives = [gdspy.PolygonSet(i, layer = 0),gdspy.PolygonSet( o, layer = 0)]
			subtraction = lambda p1, p2: p2 and not p1
			outer_cross_poly_set = gdspy.boolean( primitives, subtraction, max_points=199,layer =Outer_Cross_Layer).rotate(ang, center=(0, 0))
		
		if Outer_Only == True:
			inner_cross_poly_set = gdspy.boolean( primitives, subtraction, max_points=199,layer =Inner_Cross_Layer ).rotate(ang, center=(0, 0))
		poly_set_list = [inner_cross_poly_set, outer_cross_poly_set]

		if Guidelines == True:
			guide_line_length = 5*Outer_Cross_Width
			num_steps = 3
			gi = draw_guide_lines(Inner_Cross_Layer,Inner_Cross_Thickness,guide_line_length,num_steps)
			inner_guide_line_poly_set = gdspy.PolygonSet( gi, layer =Inner_Cross_Layer )

			if Outer_Cross_Thickness==0:
				go = draw_guide_lines(Outer_Cross_Layer,Inner_Cross_Thickness,guide_line_length,num_steps)
				outer_guide_line_poly_set = gdspy.PolygonSet( go, layer =Outer_Cross_Layer )
			else:
				go = draw_guide_lines(Outer_Cross_Layer,2*Outer_Cross_Thickness+Inner_Cross_Thickness ,guide_line_length,num_steps)
				primitives = [gdspy.PolygonSet(gi, layer = 0),gdspy.PolygonSet( go, layer = 0 )]
				subtraction = lambda p1, p2: p2 and not p1
				outer_guide_line_poly_set = gdspy.boolean(primitives, subtraction, max_points=199, layer =Inner_Cross_Layer )
			
			if Outer_Only == True:
				inner_guide_line_poly_set = gdspy.boolean(primitives, subtraction, max_points=199, layer =Inner_Cross_Layer )

			poly_set_list.append(inner_guide_line_poly_set)
			poly_set_list.append(outer_guide_line_poly_set)

		align_cell = gdspy.Cell('Alignment_Mark', exclude_from_global=True)
		align_cell.add(poly_set_list)	
		return align_cell


	align_mark_y_separation = 400.
	align_mark_x_separation = 48600.
	align_mark_set_separation = 10800.
	align_cell1 = draw_alignment(Pillar_Layer, Resonator_Trace_Layer,10,10,200,True,True,0*np.pi/4) #Outer_Only == True because Pillar_Layerwill be polarity reversed
	align_cell2 = draw_alignment(Through_Line_Layer, Resonator_Trace_Layer,5,5,200,True,False,np.pi/4)

	align_cell_ref = gdspy.CellArray(align_cell1, 2, 2, [align_mark_x_separation,align_mark_y_separation], origin=(-align_mark_x_separation/2, -align_mark_y_separation/2), rotation=None, magnification=None, x_reflection=False)

	mask_cell.add(align_cell_ref)
	align_cell_ref = gdspy.CellArray(align_cell2, 2, 2, [align_mark_x_separation+align_mark_set_separation,align_mark_y_separation], origin=(-(align_mark_x_separation+align_mark_set_separation)/2, -align_mark_y_separation/2), rotation=None, magnification=None, x_reflection=False)
	mask_cell.add(align_cell_ref)

	
	name = Save_Path + os.sep + 'mask'
	mask_cell.flatten()

	#name = os.path.abspath(os.path.dirname(os.sys.argv[0])) + os.sep + 'mask'

	## Output the layout to a GDSII file (default to all created cells).
	## Set the units we used to micrometers and the precision to nanometers.
	gdspy.gds_print(name + '.gds', unit=1.0e-6, precision=1.0e-9)
	print('gds file saved: ' + name + '.gds')
	## Save an image of the boolean cell in a png file.  Resolution refers
	## to the number of pixels per unit in the layout. Resolution changed from 4
	## to 1 to avoid  "malloc_error"
	#gdspy.gds_image([resonator_cell], image_name=name, resolution=1, antialias=4)

	#comment out save as png for speed
	#print('Image of the boolean cell saved: ' + name + '.png')

	## Import the file we just created, and extract the cell 'POLYGONS'. To
	## avoid naming conflict, we will rename all cells.
	#gdsii = gdspy.GdsImport(name + '.gds', rename={sensor_cell_name:'IMPORT_SENSOR'})

	## Now we extract the cells we want to actually include in our current
	## structure. Note that the referenced cells will be automatically
	## extracted as well.
	#gdsii.extract(sensor_cell_name)
	    
	## View the layout using a GUI.  Full description of the controls can
	## be found in the online help at http://gdspy.sourceforge.net/
	#gdspy.LayoutViewer(colors=[None] * 64) # for outlined polygons
	gdspy.LayoutViewer()


	#return Sensor_Nums


################## Draw_Sensor: Draw the Individual Dies ######################
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
	sensor_cell = gdspy.Cell(sensor_cell_name,exclude_from_global=False)


	
	
	# We draw the cut lines by boolean operation on two squares defining the die outline
	poly1 = gdspy.Rectangle(current_sensor_origin, current_sensor_origin+ np.array([X_Length, Y_Length]), layer=Resonator_Trace_Layer)
	poly2 = gdspy.Rectangle(current_sensor_origin + np.array([Cut_Line_Width, Cut_Line_Width]), current_sensor_origin+np.array([X_Length-Cut_Line_Width, Y_Length-Cut_Line_Width]), layer=Resonator_Trace_Layer)
	#poly1 = gdspy.Rectangle(Resonator_Trace_Layer, (0, 0), (X_Length, Y_Length))
	#poly2 = gdspy.Rectangle(Resonator_Trace_Layer, (Cut_Line_Width, Cut_Line_Width), (X_Length-Cut_Line_Width, Y_Length-Cut_Line_Width))
	primitives = [poly2,poly1]
	subtraction = lambda p1, p2: p2 and not p1
	mask_cell.add(gdspy.boolean( primitives, subtraction, max_points=199,layer=Resonator_Trace_Layer))

	#
	#
	#
	#Bare sensor cell is sensor cell without text and cutlines
	#bare_sensor_cell_name = 'BARE_'+sensor_cell_name
	#bare_sensor_cell = gdspy.Cell(bare_sensor_cell_name,exclude_from_global=False)
	#
	#
	#
	#


	#
	#
	#
	#
	#
	#Add the name of the sensor in the lower left of the die
	Text_Offset = 100
	#sensor_cell.add(gdspy.Text(Resonator_Trace_Layer, 'S' + str(Sensor_Number), 300, (Cut_Line_Width+Text_Offset, Cut_Line_Width+Text_Offset)))
	text_cell.add(gdspy.Text('S' + str(Sensor_Number), 300, tuple(current_sensor_origin + np.array([Cut_Line_Width+Text_Offset, Cut_Line_Width+Text_Offset])), layer=Resonator_Trace_Layer))
	#
	#
	#
	##


	#Draw Throughline
	#assuming L shape
 	Though_Line_Trace = gdspy.Path(Through_Line_Width, (X_Length/2, 0))
 	Though_Line_Trace.segment( Through_Line_Edge_Offset + Through_Line_Width/2 - Through_Line_Turn_Radius, '+y', layer=Through_Line_Layer)
 	Though_Line_Trace.turn(Through_Line_Turn_Radius, 'l',layer=Through_Line_Layer)
	Though_Line_Trace.segment((X_Length/2)-Through_Line_Edge_Offset-Through_Line_Width/2 - 2*Through_Line_Turn_Radius, '-x', layer=Through_Line_Layer)
	Though_Line_Trace.turn(Through_Line_Turn_Radius, 'r', layer=Through_Line_Layer)
	Though_Line_Trace.segment(Y_Length-2*Through_Line_Edge_Offset-Through_Line_Width - 2*Through_Line_Turn_Radius, '+y',layer=Through_Line_Layer)
	_res_x_zero = Though_Line_Trace.x
	Though_Line_Trace.turn( Through_Line_Turn_Radius, 'r',layer=Through_Line_Layer)
	_res_y_zero = Though_Line_Trace.y	
	Though_Line_Trace.segment( (X_Length/2)-Through_Line_Edge_Offset-Through_Line_Width/2 - 2*Through_Line_Turn_Radius, '+x',layer=Through_Line_Layer)
	Though_Line_Trace.turn( Through_Line_Turn_Radius, 'l',layer=Through_Line_Layer)
	Though_Line_Trace.segment(Through_Line_Edge_Offset + Through_Line_Width/2 - Through_Line_Turn_Radius, '+y',layer=Through_Line_Layer)

	sensor_cell.add(Though_Line_Trace)

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
		resonator_cell,_y_initial = Draw_Resonator(Resonator_Name=Resonator_Name,Resonator_ID=resonator_id, Resonator_Trace_Layer = Resonator_Trace_Layer, Pillar_Layer = Pillar_Layer, Y_Pitch_Tight = True, X_Pitch_Tight = True,Update_DB = True)

		_cur_Res_x_pos = Coupler_Zone + _res_x_zero
		_cur_Res_y_pos += -Head_Space-_y_initial
		#global current_resonator_origin
		current_resonator_origin = np.array([_cur_Res_x_pos, _cur_Res_y_pos])
		resonator_origin = str(current_resonator_origin.tolist()).replace(',',';')
		Mask_DB.Update_Computed_Parameters(resonator_id, {"Resonator_Origin":'"'+resonator_origin+'"'})
		_curr_Res_ref =  gdspy.CellReference(resonator_cell, tuple(current_resonator_origin))
		sensor_cell.add(_curr_Res_ref)
		
		#add resonator label text
		text_location = current_sensor_origin + current_resonator_origin + resonator_label_location 
		text_cell.add(gdspy.Text( Resonator_Name, 3*Pillar_Radius, tuple(text_location), layer=Resonator_Trace_Layer))

		_bounding_box_edges = resonator_cell.get_bounding_box() + np.array([[_cur_Res_x_pos, _cur_Res_y_pos],[_cur_Res_x_pos, _cur_Res_y_pos]])
		_total_y_distance = _bounding_box_edges[1][1] - _bounding_box_edges[0][1]
		_cur_Res_y_pos += -_total_y_distance 

		while _pillar_y_index >= _cur_Res_y_pos:
			while _pillar_x_index <= X_Length - Pillar_Radius:
				if not in_rectangle((_pillar_x_index, _pillar_y_index),_bounding_box_edges,Pillar_Radius):#Pillar_Radius+Pillar_Grid_Spacing):
					sensor_cell.add(gdspy.Round((_pillar_x_index, _pillar_y_index), Pillar_Radius,number_of_points=60, layer=Pillar_Layer))
				_pillar_x_index += Pillar_Grid_Spacing
			_pillar_x_index = (Pillar_Grid_Spacing+Pillar_Diameter)/2
			_pillar_y_index -= Pillar_Grid_Spacing

		Res_Number += 1 
	
	while _pillar_y_index >= Pillar_Radius:
		while _pillar_x_index <= X_Length - Pillar_Radius:
			sensor_cell.add(gdspy.Round((_pillar_x_index, _pillar_y_index), Pillar_Radius,number_of_points=60, layer=Pillar_Layer))
			_pillar_x_index += Pillar_Grid_Spacing
		_pillar_x_index = (Pillar_Grid_Spacing+Pillar_Diameter)/2
		_pillar_y_index -= Pillar_Grid_Spacing
	
	#bare_sensor_cell_ref =  gdspy.CellReference(bare_sensor_cell, (0,0))
	#sensor_cell.add(bare_sensor_cell_ref)	
	Sensor_Dict = {"Through_Line_Metal_Area":Though_Line_Trace.area(),"Through_Line_Length":Though_Line_Trace.length, "Sensor_Pillar_Area": sensor_cell.area(by_spec=True)[(Pillar_Layer,0)], "sensor_id":Sensor_Number, "Sensor_Cell_Name":'"'+sensor_cell_name+'"' }
	for ID in Res_IDs:
		resonator_id = ID[0]
		Mask_DB.Update_Computed_Parameters(resonator_id, Sensor_Dict)


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

########################### Draw_Resonator ####################################
def Draw_Resonator(Resonator_Name,Resonator_ID, Resonator_Trace_Layer = 1, Pillar_Layer = 2, Y_Pitch_Tight = False, X_Pitch_Tight = False,Update_DB = True, *Geometry_Tuple):
	''' This function draws a meandered resonator specified by the arguments and keyword options.


	Geometry_Tuple = (Resonator_Width,Resonator_Length,Aux_Coupler_Length,Coupler_Length,Meander_Pitch,Meander_Zone,Pillar_Diameter,Pillar_Spacing,Pillar_Clearance,Through_Line_Width )

	If Geometry_Tuple is given, then it is used to generate resonator..

	If Geometry_Tuple is not given, This function obtains Geometry_Tuple information directly from the Mask_DB

	The Y_Pitch_Tight option reduces the Pillar_Spacing so that the calculated number of folds/meanders fits perfectly between pillars without empty space.
	The X_Pitch_Tight option reduces the Meander_Zone so that right (and left) turns occur as close to pillars as permitted by the Pillar_Clearance.  
	If  Pillar_Spacing - 2*Pillar_Clearance < Resonator_Width+Meander_Pitch, pillar spaceing is increased so that a row of columns fits between every fold/meander.
	*Pillar Spacing (in any direction) can only decrease (unless an increase in necessary in order to fit a rung between Pillar rows due to wide resonator)
	*Meander Zone can only decrease
	*Pillar clearance can only increase
	*Meander Pitch Can only decrease

	This function updates the Computed_Parameters table in the Mask_DB if Update_DB = True

	'''

	if Geometry_Tuple == ():
	    Geometry_Tuple = Mask_DB.Get_Mask_Data("SELECT Resonators.Width, Computed_Parameters.Resonator_Length, Computed_Parameters.Aux_Coupler_Length,Computed_Parameters.Coupler_Length, Resonators.Meander_Pitch, Resonators.Meander_Zone, Sensors.Pillar_Diameter, Sensors.Pillar_Grid_Spacing, Sensors.Pillar_Clearance,Sensors.Through_Line_Width, Computed_Parameters.Max_Current_Length FROM Resonators, Sensors,Computed_Parameters WHERE Sensors.sensor_id = Resonators.sensor_id AND Resonators.resonator_id = Computed_Parameters.resonator_id AND Resonators.resonator_id = " + str(Resonator_ID) ,'one')
	    
	    #print("Function %s in module %s: Resonator_Length == None.... Estimating length to be %f" % (__name__, __module__,Geometry_Tuple[1]))
	else:
	   Geometry_Tuple = Geometry_Tuple[0]


	Resonator_Width,Resonator_Length,Aux_Coupler_Length,Coupler_Length,Meander_Pitch,Meander_Zone,Pillar_Diameter,Pillar_Spacing,Pillar_Clearance,Through_Line_Width,Max_Current_Length = Geometry_Tuple




	Pillar_Radius = Pillar_Diameter/2


	_pillar_y_Spacing_flag = False # Is set to true when _pillar_y_Spacing needs to be increased so that a rung of the resonator can fit between pillar rows
	_min_rung_clearance = Pillar_Spacing - 2*(Pillar_Clearance + Pillar_Radius)
	if _min_rung_clearance < Resonator_Width:
	    _pillar_y_Spacing = 2*(Pillar_Clearance + Pillar_Radius) + Resonator_Width
	    print("Pillar spacing in y directions is overridden. It is changed from " + str(Pillar_Spacing) + " to " + str(_pillar_y_Spacing) + \
	        " so that a rung can fit between pillars.")        
	    _min_rung_clearance = _pillar_y_Spacing - 2*(Pillar_Clearance + Pillar_Radius)
	    _pillar_y_Spacing_flag = True
	else:
	    _pillar_y_Spacing = Pillar_Spacing
	    
	(_fold_bundle_size,_remainder) = divmod(_min_rung_clearance - Resonator_Width, Resonator_Width+Meander_Pitch)





	if (_min_rung_clearance - Resonator_Width > Resonator_Width+Meander_Pitch): 
	    #pitch can be tightened ...
	    if  Y_Pitch_Tight == True:
	        print("Pillar spacing in y directions is overridden. It is changed from " + str(_pillar_y_Spacing) +" to " + \
	            str(_pillar_y_Spacing - _remainder)+" to coil the resonator as tight as possible in the y direction given the Meander_Pitch.")
	        _pillar_y_Spacing = _pillar_y_Spacing - _remainder
	        _remainder = 0
	        
	elif (_min_rung_clearance - Resonator_Width < Resonator_Width+Meander_Pitch) and (_min_rung_clearance > Resonator_Width+Meander_Pitch): 
	    #pitch can be tightened...
	    if  Y_Pitch_Tight == True:
	        print("Pillar spacing in y directions is overridden. It is changed from " + str(_pillar_y_Spacing) +" to " + \
	            str(_pillar_y_Spacing - _remainder)+" to coil the resonator as tight as possible in the y direction given the Meander_Pitch.")
	        print("_remainder is " + str(_remainder))
	        _pillar_y_Spacing = max(_pillar_y_Spacing - _remainder,2*(Pillar_Clearance + Pillar_Radius)+Resonator_Width)
	        _remainder = 0
	    
	    if _fold_bundle_size != 0.0:
	        print("_fold_bundle_size != 0.0 and it should be. There may be a problem")

	elif (_min_rung_clearance - Resonator_Width < Resonator_Width+Meander_Pitch) and (_min_rung_clearance < Resonator_Width+Meander_Pitch):
	    # **** Next: change (decrease) pillar spacing rather than  changing meander Pitch
	    #pitch can not be tightened
	    
	    if _pillar_y_Spacing_flag == False:
	        print("Disabled - Meander_Pitch has been is overridden so that one rung can fit between pillar rows. It is changed from "+ \
	            str(Meander_Pitch)+" to "+str(_min_rung_clearance - Resonator_Width))
	        #Meander_Pitch = _min_rung_clearance - Resonator_Width
	    else:
	        print("Meander_Pitch has been is overridden so that inner side of turn is rounded. It is changed from "+str(Meander_Pitch)+ \
	            " to "+str(2*(Pillar_Clearance + Pillar_Radius)))
	        Meander_Pitch = 2*(Pillar_Clearance + Pillar_Radius)
	        
	    (_fold_bundle_size,_remainder) = divmod(_min_rung_clearance - Resonator_Width, Resonator_Width+Meander_Pitch)
	    

	meander_radius = Meander_Pitch/2 + Resonator_Width/2 #distance between resonator turn center an resonator trace **center line**
	#if (_remainder == 0) and (meander_radius < Pillar_Clearance+Pillar_Radius+Resonator_Width/2):
	#    meander_radius = Pillar_Clearance+Pillar_Radius+Resonator_Width/2
	#    print("Decreasing meander radius so that segments of turns do not overlap.")


	_turn_extension = abs(2*Pillar_Radius+ 2*Pillar_Clearance-(2*meander_radius-Resonator_Width)+_remainder)

	#This addresses the case where multiple rows of pillars fit within the resonator Meander_Pitch
	_pillar_bundle_flag = 0
	(_pillar_bundle_size,_pillar_bundle_remainder) = divmod(Meander_Pitch-2*(Pillar_Clearance + Pillar_Radius),_pillar_y_Spacing)

	#divmod(_pillar_bundle_remainder,_pillar_bundle_size) # <-- I think this line can be deleted...
	if _pillar_bundle_size > 0:
	    _turn_extension = 0
	    _pillar_bundle_flag = 1
	    print("More than one row of pillars will fit between resonator rungs...") 
	    if (Y_Pitch_Tight == True):
	        _pillar_y_Spacing_increase, r = divmod(_pillar_bundle_remainder,_pillar_bundle_size)
	        print("Pillar spacing in y directions is overridden. It is changed from " + str(_pillar_y_Spacing) +" to " + \
	        str(_pillar_y_Spacing + _pillar_y_Spacing_increase) + " so that pillar clearance remains constant with increasing _fold_num.")
	        _pillar_y_Spacing += _pillar_y_Spacing_increase
	        print("This condition needs to be fixed ",_pillar_bundle_remainder,_pillar_bundle_size,_pillar_y_Spacing_increase)
	        #print(_pillar_bundle_size)
	        #print(_pillar_y_Spacing_increase)


	if (Meander_Pitch > 2*(Pillar_Radius + Pillar_Clearance)) and (Y_Pitch_Tight == True) and (_pillar_bundle_flag == 0):
	    _turn_extension = 0
	    print("Increasing Pillar_Clearance from " + str(Pillar_Clearance) + " to " + str(meander_radius-Resonator_Width/2-Pillar_Radius))
	    Pillar_Clearance = meander_radius-Resonator_Width/2-Pillar_Radius
	    print("Pillar spacing in y directions is overridden. It is changed from " + str(_pillar_y_Spacing) +" to " + str(_fold_bundle_size*(meander_radius*2) \
	        + 2*Pillar_Clearance+ Resonator_Width+ Pillar_Radius*2)+" so that pillar clearance remains constant with increasing _fold_num.")
	    _pillar_y_Spacing =  _fold_bundle_size*(meander_radius*2) + 2*Pillar_Clearance+ Resonator_Width+ Pillar_Radius*2
	 
	#Initialize GDS cell
	resonator_cell_name = 'RESONATOR_'+str(Resonator_ID)
	resonator_cell = gdspy.Cell(resonator_cell_name,exclude_from_global=False)

	#initialize Resonator trace object
	_y_initial = -(Pillar_Clearance+Pillar_Radius+Resonator_Width/2)
	resonator_start_point = (0, _y_initial)
	trace = gdspy.Path(Resonator_Width, (0, _y_initial)) 

	#########################
	# Draw Coupler
	#########################
	#Coupler_Length = 1000.0
	coupler_trace = gdspy.Path(Resonator_Width, resonator_start_point)
	coupler_trace.segment( Coupler_Length, '-x', layer=Resonator_Trace_Layer)
	resonator_cell.add(coupler_trace)

	#Aux_Coupler_Length = 1000.0
	#Through_Line_Width = 360

	if Aux_Coupler_Length is not 0.0:
	    # Find Start Point
	    aux_coupler_start_point = (coupler_trace.x- 0.5*Through_Line_Width, coupler_trace.y+0.5*Resonator_Width)

	    aux_coupler_trace = gdspy.Path(Through_Line_Width, aux_coupler_start_point)
	    aux_coupler_trace.segment(Aux_Coupler_Length,'-y', layer=Resonator_Trace_Layer)
	    resonator_cell.add(aux_coupler_trace)
	#########################


	    

	#Adjust Resonator Length
	#Resonator_Length = Resonator_Length-Coupler_Length Not Necessary!
	   
	#add small section to trace to compensate for x distance of 180 degree turn
	_turn_outer_radius = Resonator_Width/2 + meander_radius
	if Resonator_Width + meander_radius  < Resonator_Length:
	    trace.segment(_turn_outer_radius, '+x', layer=Resonator_Trace_Layer)
	    

	       
	_new_meander_zone = Meander_Zone
	_segment_direction = ('+x','-x')
	_angel_direction = ('r','l')
	_fold_num = 0
	_pillar_index = 0
	_pillar_y_index = 0
	_fold_bundle_num = 0
	_current_rung_y_value = 0
	_break_after_pillars = 0 #_break_after_pillars flag is used to make sure that pillars are drawn in and arroung the last rung of the resonator, turn or turn_extension of the resonator

	if Pillar_Radius + Pillar_Clearance > meander_radius - Resonator_Width/2:
	    _pillar_x_index = Resonator_Width + Pillar_Clearance + Pillar_Radius #current x location of pillar center
	else:
	    _pillar_x_index = _turn_outer_radius #current x location of pillar center

	#this is the starting x postion for the pillars in the coupler zone
	_pillar_x_index_coupler = _pillar_x_index

	#center distance between first and last pillars in a row
	_pillar_straight = Meander_Zone-2*_pillar_x_index


	#_meander_straight is length of straight resonator meander segments. x-dist between resonator turn centers
	_meander_straight = Meander_Zone - 2*_turn_outer_radius

	# If X_Pitch_Tight == True, shorten _meander_straight to empty pillar (space without pillars) on right side of resonator
	_delta = abs(_pillar_x_index - _turn_outer_radius)
	(_pillar_straight_num,r)=divmod(_pillar_straight,Pillar_Spacing)
	_meander_zone_delta = 0.0
	if X_Pitch_Tight == True:
	    _meander_zone_delta = _meander_straight - (_pillar_straight_num*Pillar_Spacing+2*_delta)        
	    _meander_straight =  _pillar_straight_num*Pillar_Spacing+2*_delta # 2*Pillar_Radius #Consider removing  2*Pillar_Clearance term
	    _new_meander_zone = _meander_straight+2*_turn_outer_radius
	    print("Meander_Zone is overridden. It is shortened from " + str(Meander_Zone) +" to " + \
	        str(_meander_straight+2*_turn_outer_radius) + " to reduce empty space in the x-direction")

	def draw_coupler_zone_pillars():
	    #_x = _pillar_x_index_coupler - float(divmod(_turn_outer_radius,Pillar_Spacing)[0]+1)*Pillar_Spacing # The second term is there to clear the turn area of the resonator
	    _x = -(Pillar_Clearance + Pillar_Radius)-Pillar_Spacing
	    _y = -abs(_pillar_y_index)
	    _r = Pillar_Radius
	    _x_min = coupler_trace.x - Pillar_Radius - Pillar_Clearance #This is for drawing a left most column of pillars so that resonator cell is bordered on all 4 sides by pillars
	    if (Aux_Coupler_Length == 0.0):
	        #print("cond 1")
	        while _x >= -Coupler_Length:
	            resonator_cell.add(gdspy.Round( (_x, _y), _r, layer= Pillar_Layer))
	            _x -= Pillar_Spacing
	    elif (Aux_Coupler_Length != 0.0) and (Aux_Coupler_Length <= Resonator_Width) or (_fold_bundle_num ==0):# note condition _fold_bundle_num ==0 so that top row of pillars is drawn on top of Aux coupler no matter what
	        #print("cond 2")
	        _x_min = _x_min - Through_Line_Width
	        while _x >= -(Coupler_Length+Through_Line_Width):
	            resonator_cell.add(gdspy.Round((_x, _y), _r, layer= Pillar_Layer))
	            _x -= Pillar_Spacing
	    elif (Aux_Coupler_Length != 0.0) and (Aux_Coupler_Length >= Resonator_Width) and (_y > aux_coupler_trace.y- Pillar_Radius - Pillar_Clearance):#note that aux_coupler_trace may not be defined
	        #print("cond 3, _y = %f" % _y)
	        _x_min = _x_min - Through_Line_Width
	        while _x >= -(Coupler_Length-Pillar_Clearance):
	            resonator_cell.add(gdspy.Round((_x, _y), _r, layer= Pillar_Layer))
	            _x -= Pillar_Spacing
	    elif (Aux_Coupler_Length != 0.0) and (Aux_Coupler_Length >= Resonator_Width) and (_y < aux_coupler_trace.y- Pillar_Radius - Pillar_Clearance):
	        #print("cond 4, _y = %f" % _y)
	        _x_min = _x_min - Through_Line_Width
	        while _x >= -(Coupler_Length+Through_Line_Width):
	            resonator_cell.add(gdspy.Round((_x, _y), _r, layer= Pillar_Layer))
	            _x -= 2*Pillar_Spacing
	    else:
	        print('encountered unknown pillar zone pillar drawn condition')

		_x += Pillar_Spacing
		if (_x - _x_min) > _r*2: # dont draw if pillars intersect
			resonator_cell.add(gdspy.Round((_x_min, _y), _r, layer= Pillar_Layer))

	rung_count = 0
	phase_midpoint = '[0,0]'
	#The Resonator and its interspersed pillars are drawn here
	while trace.length <=  Resonator_Length:      
	    #Draw Straight length of resonator

		if _meander_straight + trace.length <= Resonator_Length:
			if trace.length <= Max_Current_Length and _meander_straight + trace.length >= Max_Current_Length:
				dif = Max_Current_Length - trace.length
				partial_segment(Resonator_Trace_Layer, trace, Max_Current_Length, _segment_direction[_fold_num%2])
				phase_midpoint = [trace.x,trace.y]
				partial_segment(Resonator_Trace_Layer, trace, _meander_straight - dif + trace.length , _segment_direction[_fold_num%2])
			else:
				trace.segment(_meander_straight , _segment_direction[_fold_num%2], layer=Resonator_Trace_Layer)
			rung_count = rung_count + 1		
		elif _break_after_pillars is not 1:
			partial_segment(Resonator_Trace_Layer, trace, Resonator_Length, _segment_direction[_fold_num%2])
			if _fold_num > 0: #for the case that Resonator_Length < _meander_straight.
				_break_after_pillars = 1 #_break_after_pillars flag is used to make sure that pillars are drawn in and arroung the last rung of the resonator, turn or turn_extension of the resonator
	              
	    #Now Draw Pillars     
		if ((_fold_bundle_size > 0)  and  (_fold_num%(_fold_bundle_size+1) == 0.0)) or (_fold_bundle_size == 0.0):
			_current_rung_y_value = trace.y
			if _fold_bundle_num == 0 or _pillar_bundle_flag == 0:

				#Draw the pillars in the coupler zone
				draw_coupler_zone_pillars() #must be called before _fold_bundle_num is incremented

				while _pillar_index*Pillar_Spacing <= _pillar_straight:
					resonator_cell.add(gdspy.Round( (_pillar_x_index, -_pillar_y_index), Pillar_Radius, layer= Pillar_Layer))
					_pillar_x_index += ((-1)**(_fold_bundle_num))*Pillar_Spacing  
					_pillar_index+=1           
				_pillar_x_index += ((-1)**(_fold_bundle_num))*(-Pillar_Spacing)
				_fold_bundle_num += 1
				#Add a Pillar on left of resonator meander
				resonator_cell.add(gdspy.Round(( -(Pillar_Clearance + Pillar_Radius),-_pillar_y_index),Pillar_Radius, layer= Pillar_Layer))

				#Add a Pillar on right of resonator meander
				resonator_cell.add(gdspy.Round((Meander_Zone+Pillar_Clearance+Pillar_Radius-_meander_zone_delta,-_pillar_y_index),Pillar_Radius, layer= Pillar_Layer))
				_pillar_index = 0
				_pillar_y_index+=_pillar_y_Spacing
			else: #This is the case where multiple rows of pillar fit between resonator rungs (within the meander pitch)
				_pillar_y_index=_current_rung_y_value+Resonator_Width/2 + Pillar_Clearance + Pillar_Radius
				for i in xrange(int(_pillar_bundle_size+1)): 

				    #Draw the pillars in the coupler zone
					draw_coupler_zone_pillars() #must be called before _fold_bundle_num is incremented

					while _pillar_index*Pillar_Spacing <= _pillar_straight:                        
						resonator_cell.add(gdspy.Round((_pillar_x_index, _pillar_y_index), Pillar_Radius,layer= Pillar_Layer))
						_pillar_x_index += ((-1)**(_fold_bundle_num))*Pillar_Spacing  
						_pillar_index+=1           
					_pillar_x_index += ((-1)**(_fold_bundle_num))*(-Pillar_Spacing)
					_fold_bundle_num += 1
					#Add a Pillar on left of resonator meander
					resonator_cell.add(gdspy.Round(( -(Pillar_Clearance + Pillar_Radius),_pillar_y_index),Pillar_Radius, layer= Pillar_Layer))

					#Add a Pillar on right of resonator meander
					resonator_cell.add(gdspy.Round((Meander_Zone+Pillar_Clearance+Pillar_Radius-_meander_zone_delta,_pillar_y_index),Pillar_Radius, layer= Pillar_Layer))
					_pillar_index = 0
					_pillar_y_index+=_pillar_y_Spacing
			if _break_after_pillars == 1:
				break
	            
	    
	    #for the case that Resonator_Length < _meander_straight. This makes sure that the top row of pillars is drawn.
		if trace.length >= Resonator_Length:
			break

	    #Draw 90 degree turn so that resonator path is oriented in y direction
		if trace.length + 0.5*np.pi*meander_radius <= Resonator_Length:
			if trace.length <= Max_Current_Length and 0.5*np.pi*meander_radius + trace.length >= Max_Current_Length: # the case where the midpoint is in this segment
				dif = Max_Current_Length - trace.length
				partial_turn(Resonator_Trace_Layer, trace, Max_Current_Length, meander_radius, _angel_direction[_fold_num%2])
				phase_midpoint = [trace.x,trace.y]
				partial_turn(Resonator_Trace_Layer, trace, 0.5*np.pi*meander_radius - dif + trace.length , meander_radius, _angel_direction[_fold_num%2])
			else:
				trace.turn( meander_radius, _angel_direction[_fold_num%2], layer= Resonator_Trace_Layer)
		elif _break_after_pillars is not 1:
			partial_turn(Resonator_Trace_Layer, trace, Resonator_Length, meander_radius,  _angel_direction[_fold_num%2])
			_break_after_pillars = 1
		        
		#Decide if turn extension is needed, and if so, draw turn extension in y direction    
		if ((_fold_bundle_size > 0)  and  ((_fold_num+1)%(_fold_bundle_size+1) == 0.0)) or ((_turn_extension > 0) and (_fold_bundle_size == 0.0)):
			if  (trace.length + _turn_extension <= Resonator_Length):
				if trace.length <= Max_Current_Length and _turn_extension + trace.length >= Max_Current_Length: # the case where the midpoint is in this segment
					dif = Max_Current_Length - trace.length
					partial_segment(Resonator_Trace_Layer, trace, Max_Current_Length, '-y')
					phase_midpoint = [trace.x,trace.y]
					partial_segment(Resonator_Trace_Layer, trace, _turn_extension - dif + trace.length , '-y')
				else:
					trace.segment(_turn_extension, '-y', layer= Resonator_Trace_Layer)
			elif _break_after_pillars is not 1:
				partial_segment(Resonator_Trace_Layer, trace, Resonator_Length, '-y')
				_break_after_pillars = 1

	    #Draw 90 degree turn so that resonator path is oriented back in x direction                      
		if trace.length + 0.5*np.pi*meander_radius <= Resonator_Length:
			if trace.length <= Max_Current_Length and 0.5*np.pi*meander_radius + trace.length >= Max_Current_Length: # the case where the midpoint is in this segment
				dif = Max_Current_Length - trace.length
				partial_turn(Resonator_Trace_Layer, trace, Max_Current_Length, meander_radius, _angel_direction[_fold_num%2])
				phase_midpoint = [trace.x,trace.y]
				partial_turn(Resonator_Trace_Layer, trace, 0.5*np.pi*meander_radius - dif + trace.length , meander_radius, _angel_direction[_fold_num%2])
			else:
				trace.turn(meander_radius, _angel_direction[_fold_num%2], layer= Resonator_Trace_Layer)
		elif _break_after_pillars is not 1:
			partial_turn(Resonator_Trace_Layer, trace, Resonator_Length, meander_radius,  _angel_direction[_fold_num%2])
			_break_after_pillars = 1
	    
		_fold_num+=1

	_current_y_value = min(_current_rung_y_value,trace.y)

	#Draw Bottom row of Pillars no matter what
	_pillar_y_index=_current_y_value-Resonator_Width/2 - Pillar_Clearance - Pillar_Radius
	draw_coupler_zone_pillars()   
	while _pillar_index*Pillar_Spacing <= _pillar_straight:
		resonator_cell.add(gdspy.Round( (_pillar_x_index, _pillar_y_index), Pillar_Radius, layer= Pillar_Layer))
		_pillar_x_index += ((-1)**(_fold_bundle_num))*Pillar_Spacing  
		_pillar_index+=1           
	_pillar_x_index += ((-1)**(_fold_bundle_num))*(-Pillar_Spacing)
	_fold_bundle_num += 1   
	#Add a Pillar on left of resonator meander
	resonator_cell.add(gdspy.Round(( -(Pillar_Clearance + Pillar_Radius),_pillar_y_index),Pillar_Radius,layer= Pillar_Layer))
	#Add a Pillar on right of resonator meander
	resonator_cell.add(gdspy.Round((Meander_Zone+Pillar_Clearance+Pillar_Radius-_meander_zone_delta,_pillar_y_index),Pillar_Radius, layer= Pillar_Layer))
	 
	#
	#
	#
	#    
	#Add Define Resonator Label Location Global
	#resonator_cell.add(gdspy.Text(Resonator_Trace_Layer, Resonator_Name, 3*Pillar_Radius, (-Pillar_Spacing/2,Pillar_Radius+5)))
	global resonator_label_location
	resonator_label_location = np.array([-Pillar_Spacing/2,Pillar_Radius+5])
	#
	#
	#
	#

	#The total y distance traverse by resonator and pillars. measured from top pillar center to bottom pillar center
	total_y_distance = min(_pillar_y_index, trace.y)
	print('total_y_distance = '+ str(total_y_distance))
	_pillar_y_Spacing = _pillar_y_Spacing
	#The total x distance traverse by resonator and pillars. measured from left pillar center to right pillar center 
	total_x_distance = Meander_Zone+2*Pillar_Clearance+2*Pillar_Radius 
	print('total_x_distance = '+ str(total_x_distance))
	_pillar_x_Spacing = Pillar_Spacing

	_meander_length = _y_initial - trace.y + Resonator_Width

	resonator_cell.add(trace)
	phase_midpoint = str(phase_midpoint).replace(',',';')
	sensor_origin = str(current_sensor_origin.tolist()).replace(',',';')
	#resonator_origin = str(current_resonator_origin.tolist()).replace(',',';')


	Res_Dict = {"Meander_Pitch": Meander_Pitch,"Meander_Zone":_new_meander_zone,"Meander_Length":_meander_length, "Resonator_Metal_Area":trace.area(),"Patch_Area":_meander_length*_new_meander_zone,"Turn_Extension":_turn_extension,"Rungs":rung_count, "Resonator_Cell_Name":'"'+resonator_cell_name+'"',"Phase_Midpoint": '"'+phase_midpoint+'"', "Sensor_Origin":'"'+sensor_origin+'"'}
    
	if Update_DB == True:
		Mask_DB.Update_Computed_Parameters(Resonator_ID, Res_Dict)
	return resonator_cell,_y_initial


def partial_turn(layer, trace, Resonator_Length, turn_radius, turn_direction):
    arc_angle = (Resonator_Length - trace.length)/turn_radius
    if turn_direction == 'r':
        arc_angle = -arc_angle
    trace.turn( turn_radius, arc_angle, layer = layer)
    return trace

def partial_segment(layer, trace, Resonator_Length, direction):
    length = Resonator_Length - trace.length
    trace.segment(length, direction, layer = layer)
    return trace



