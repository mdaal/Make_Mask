import numpy as np
from  Draw_Sensor import Draw_Sensor
import gdspy
import os
import Mask_DB

def Draw_Mask(Through_Line_Layer = 1, Resonator_Trace_Layer = 2, Pillar_Layer = 3):
	
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

	name = os.path.abspath(os.path.dirname(os.sys.argv[0])) + os.sep + 'mask'

	## Output the layout to a GDSII file (default to all created cells).
	## Set the units we used to micrometers and the precision to nanometers.
	gdspy.gds_print(name + '.gds', unit=1.0e-6, precision=1.0e-9)
	print('Sample gds file saved: ' + name + '.gds')

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