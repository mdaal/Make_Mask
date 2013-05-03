import numpy as np
from  Draw_Sensor import Draw_Sensor
import gdspy
import os
import Mask_DB

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
	mask_cell_name = 'Mask'
	mask_cell = gdspy.Cell(mask_cell_name)

	sens_index = 0

	for col in xrange(Mask_Columns):
		for row in xrange(Mask_Rows):
			print('row %i, col %i' % (row,col))
			sensor_cell = Draw_Sensor(Sensor_Nums[sens_index][0], Through_Line_Layer = Through_Line_Layer, Resonator_Trace_Layer = Resonator_Trace_Layer, Pillar_Layer = Pillar_Layer)
			mask_cell.add(gdspy.CellReference(sensor_cell, (Mask_Cell_X_Length*row + -Mask_Cell_X_Length*Mask_Rows/2, -Mask_Cell_Y_Length*(col+1) + Mask_Cell_Y_Length*Mask_Columns/2)))
			sens_index += 1

	
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
			P_1.segment(Layer,cross_width, '+x')
			P_2 = gdspy.Path(cross_line_width, (0,-cross_width/2))
			P_2.segment(Layer,(cross_width/2)-(cross_line_width/2), '+y')
			P_3 = gdspy.Path(cross_line_width, (P_2.x,P_2.y+cross_line_width))
			P_3.segment(Layer,(cross_width/2)-(cross_line_width/2), '+y')
			return P_1.polygons+P_2.polygons+ P_3.polygons

		def draw_guide_lines(Layer,Line_Width_Start,Length,Steps):
			polygons = []
			for i in xrange(1,Steps+1):
				polygons.append(gdspy.Path(Line_Width_Start*i,(Outer_Cross_Width/2 + Inner_Cross_Thickness +(i-1)*(Length/Steps),0)).segment(Layer,Length/Steps,'+x').polygons)
			for i in xrange(1,Steps+1):
				polygons.append(gdspy.Path(Line_Width_Start*i,(-(Outer_Cross_Width/2 + Inner_Cross_Thickness +(i-1)*(Length/Steps)),0)).segment(Layer,Length/Steps,'-x').polygons)
			return 	reduce(lambda x, y: x+y,polygons)

		cross_line_width = Inner_Cross_Thickness  #line width of cross
		cross_width = Outer_Cross_Width - 2*Outer_Cross_Thickness # overall width and height of cross

		i = draw_cross(Inner_Cross_Layer,cross_line_width,cross_width)
		inner_cross_poly_set = gdspy.PolygonSet(Inner_Cross_Layer,i).rotate(ang, center=(0, 0))

		if Outer_Cross_Thickness==0:
			o = draw_cross(Outer_Cross_Layer,cross_line_width,cross_width)
			outer_cross_poly_set = gdspy.PolygonSet(Outer_Cross_Layer,o).rotate(ang, center=(0, 0))
		else:
			o = draw_cross(Outer_Cross_Layer,3*cross_line_width,Outer_Cross_Width)
			primitives = [gdspy.PolygonSet(0,i),gdspy.PolygonSet(0, o)]
			subtraction = lambda p1, p2: p2 and not p1
			outer_cross_poly_set = gdspy.boolean(Outer_Cross_Layer, primitives, subtraction, max_points=199).rotate(ang, center=(0, 0))
		
		if Outer_Only == True:
			inner_cross_poly_set = gdspy.boolean(Inner_Cross_Layer, primitives, subtraction, max_points=199).rotate(ang, center=(0, 0))
		
		poly_set_list = [inner_cross_poly_set, outer_cross_poly_set]

		if Guidelines == True:
			guide_line_length = 5*Outer_Cross_Width
			num_steps = 3
			gi = draw_guide_lines(Inner_Cross_Layer,Inner_Cross_Thickness,guide_line_length,num_steps)
			inner_guide_line_poly_set = gdspy.PolygonSet(Inner_Cross_Layer, gi)

			if Outer_Cross_Thickness==0:
				go = draw_guide_lines(Outer_Cross_Layer,Inner_Cross_Thickness,guide_line_length,num_steps)
				outer_guide_line_poly_set = gdspy.PolygonSet(Outer_Cross_Layer, go)
			else:
				go = draw_guide_lines(Outer_Cross_Layer,2*Outer_Cross_Thickness+Inner_Cross_Thickness ,guide_line_length,num_steps)
				primitives = [gdspy.PolygonSet(0,gi),gdspy.PolygonSet(0, go)]
				subtraction = lambda p1, p2: p2 and not p1
				outer_guide_line_poly_set = gdspy.boolean(Outer_Cross_Layer, primitives, subtraction, max_points=199)
			
			if Outer_Only == True:
				inner_guide_line_poly_set = gdspy.boolean(Inner_Cross_Layer, primitives, subtraction, max_points=199)

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
	gdspy.LayoutViewer(colors=[None] * 64) # for outlined polygons
	#gdspy.LayoutViewer()


	#return Sensor_Nums