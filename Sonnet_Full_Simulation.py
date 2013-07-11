import numpy as np
import io
import os
from datetime import datetime as dt


extend_box = {"x_min":1000, "x_max":1000, "y_min":5000, "y_max":1000} #extend simulation box
extend_box.update({"y_min":extend_box["y_max"] ,"y_max":extend_box["y_min"]}) #switch y_max, y_min values because Sonnet switches positive with negative y-axis
extend_poly = {"x_min":False, "x_max":False, "y_min":True, "y_max":True} #extend polygins which have sides colinear with the box edges if box extened as per extend_box
internal_port = True


ref = Make_Mask.Get_Cell_Reference('S8', Origin=(0, 18000), Rotation=0, Magnification=None, X_reflection=True )
polygons = ref.get_polygons(by_layer=True, depth=None)

parameters = Make_Mask.Mask_DB.Get_Mask_Data("SELECT Resonators.Width,Resonators.Coupler_Zone,Sensors.Through_Line_Width,Computed_Parameters.Meander_Pitch,Computed_Parameters.Coupler_Length,Computed_Parameters.Aux_Coupler_Length, Computed_Parameters.Phase_Midpoint, Computed_Parameters.Sensor_Origin,Computed_Parameters.Resonator_Origin FROM Computed_Parameters, Resonators, Sensors WHERE Computed_Parameters.resonator_id = Resonators.resonator_id AND Computed_Parameters.sensor_id = Sensors.sensor_id AND Sensors.sensor_id = %i" % (8), fetch = 'one')
Resonator_Width = parameters[0]
Coupler_Zone = parameters[1] 
Through_Line_Width = parameters[2]
Meander_Pitch = parameters[3]
Coupler_Length = parameters[4]
Aux_Coupler_Length = parameters[5]
Phase_Midpoint = parameters[6] #is a string
Sensor_Origin = parameters[7] #is a string 
Resonator_Origin = parameters[8] #is a string


#####################################################################
#This Functions Finds The polygons along the edge of the 
#device/structure... useful for placing the ports

def Compute_Poly_Extremes(polygon_list,start):
	''' Creats poly_extremes dictionary
	start is the offset for the numbering of the polygons in the list.
	e.g. the 0th polygon in the list will be polygon #start'''
	poly_extremes = {}

	prev_x_min  = polygon_list[0][0,0]
	prev_x_max	= polygon_list[0][0,0]
	prev_y_min  = polygon_list[0][0,1]
	prev_y_max  = polygon_list[0][0,1]

	for p in xrange(len(polygon_list)):
		d = {}
		d['x_min'] = polygon_list[p][:,0].min()
		d['x_max'] = polygon_list[p][:,0].max()
		d['y_min'] = polygon_list[p][:,1].min()
		d['y_max'] = polygon_list[p][:,1].max()

		poly_extremes[p+start] = d

		if d['x_min'] <= prev_x_min:
			prev_x_min = d['x_min']
			poly_extremes['poly_x_min'] = set([p+start]) 

		if d['y_min'] <= prev_y_min:
			prev_y_min = d['y_min']
			poly_extremes['poly_y_min'] = set([p+start])

		if d['x_max'] >= prev_x_max:
			prev_x_max = d['x_max']
			poly_extremes['poly_x_max'] = set([p+start])

		if d['y_max'] >= prev_y_max:
			prev_y_max = d['y_max']
			poly_extremes['poly_y_max'] = set([p+start])

	for p in xrange(len(polygon_list)):
		if poly_extremes[p+start]['x_min'] == poly_extremes[list(poly_extremes['poly_x_min'])[0]]['x_min']:
			poly_extremes['poly_x_min'].add(p+start)
			poly_extremes['bounding_box_x_min'] = poly_extremes[p+start]['x_min']

		if poly_extremes[p+start]['y_min'] == poly_extremes[list(poly_extremes['poly_y_min'])[0]]['y_min']:
			poly_extremes['poly_y_min'].add(p+start)
			poly_extremes['bounding_box_y_min'] = poly_extremes[p+start]['y_min']

		if poly_extremes[p+start]['x_max'] == poly_extremes[list(poly_extremes['poly_x_max'])[0]]['x_max']:
			poly_extremes['poly_x_max'].add(p+start)
			poly_extremes['bounding_box_x_max'] = poly_extremes[p+start]['x_max']

		if poly_extremes[p+start]['y_max'] == poly_extremes[list(poly_extremes['poly_y_max'])[0]]['y_max']:
			poly_extremes['poly_y_max'].add(p+start)
			poly_extremes['bounding_box_y_max'] = poly_extremes[p+start]['y_max']
	return poly_extremes
#####################################################################







sonnet_path = 'Sonnet_Files'+ os.sep + dt.now().strftime('%Y%m%d') + os.sep

try:                                           
    os.makedirs(sonnet_path)
    #makedirs recursively creates all intermediate-level directories
    #needed to contain the leaf directory
except:
    pass

file_name  = 'File' 


stream = io.open(sonnet_path + file_name + '.son', mode='w')

n = os.linesep #New Line

content = '''
FTYP SONPROJ 11 ! Sonnet Project File 
VER 13.56
HEADER
LIC ucalberk2.2.35817
DAT {dat}
BUILT_BY_CREATED Unknown "Unknown Version" {dat}
BUILT_BY_SAVED xgeom 13.56
END HEADER
DIM
FREQ {freq}
IND {ind}
LNG {lng}
ANG {ang}
CON {con}
CAP {cap}
RES {res}
END DIM
FREQ
ABS {start_freq} {stop_freq} 
END FREQ
CONTROL
ABS
OPTIONS  {options} 
SPEED {speed}
RES_ABS {abs_man_freq_resolution_on} {abs_man_freq_resolution}
CACHE_ABS 1
TARG_ABS {abs_auto_freq_res}
Q_ACC {q_acc_on}
END CONTROL
GEO
TMET {lossless}
BMET {aluminum}
MET {niobium}
!additional metals may be declared here...
BOX {num_metal_lev} {box_width_x} {box_width_y} {xcells2} {ycells2} 20 0
      {layer_3}
      {layer_2}
      {layer_1}
!layers are declared top to bottom
LORGN {lorgn}
{PORTS}
NUM {num_of_polygons}
{POLYGONS}
END GEO
OPT
MAX {max_number_opt_iterations}
VARS
END
END OPT
VARSWP
END VARSWP
FILEOUT
{touchstone}
{comma_sep_variable}
FOLDER {folder}
END FILEOUT
QSG
IMPORT YES
EXTRA_METAL NO
UNITS YES
ALIGN NO
REF NO
VIEW_RES NO
METALS YES
USED YES
END QSG
'''
format_dict = {}

######### Header Information ########################################
format_dict["dat"] = dt.now().strftime('%m/%d/%Y %H:%M:%S')

######### Specify Units #############################################
format_dict["freq"] = "GHZ"
format_dict["ind"] = "NH"
format_dict["lng"] = "UM"
format_dict["ang"] = "DEG"
format_dict["con"] = "/OH"
format_dict["cap"] = "PF"
format_dict["res"] = "OH"

######### Define Frequency Band #####################################
format_dict["start_freq"] = 0.71 #Ghz
format_dict["stop_freq"] = 0.735 #Ghz

######### Specify Analysis Control Settings #########################
format_dict["options"] = "-bd"
format_dict["speed"] = 0
format_dict["abs_man_freq_resolution_on"] = "Y"
format_dict["abs_man_freq_resolution"] = 6.0e-8 #Ghz
format_dict["abs_auto_freq_res"] = 1000
format_dict["q_acc_on"] = "Y"

######### Specify Metal Parameters ##################################
format_dict["metal_id"] = -1 #"id" starts at 0 and counts up with the number of MET ... declaration. Thus the first MET .... declaration is id = 0.
format_dict["SUP_Metal_Format"] = '"{name}" {hash_pattern_id} SUP {rdc} {rrf} {xdc} {ls}'
Lossless = {"name" : "Lossless", "hash_pattern_id" : 0, "rdc" : 0, "rrf" : 0, "xdc" : 0, "ls" : 0, "id":format_dict["metal_id"]}; format_dict["metal_id"] += 1
format_dict["lossless"] = format_dict["SUP_Metal_Format"].format(**Lossless)
Niobium = {"name" : "Niobium", "hash_pattern_id" : 1, "rdc" : 0, "rrf" : 0, "xdc" : 0, "ls" : 0.049, "id":format_dict["metal_id"]} ; format_dict["metal_id"] += 1
format_dict["niobium"] = format_dict["SUP_Metal_Format"].format(**Niobium)
Aluminum = {"name" : "Aluminum", "hash_pattern_id" : 2, "rdc" : 0, "rrf" : 0, "xdc" : 0, "ls" : 0.201, "id":format_dict["metal_id"]}; format_dict["metal_id"] += 1
format_dict["aluminum"] = format_dict["SUP_Metal_Format"].format(**Aluminum)


######### Define Dielectric Layer Settings ##########################
format_dict["Dielectric_Layer_Fromat"] = '{thickness} {xy_erel} {xy_mrel} {xy_eloss} {xy_mloss} {xy_esignma} {nzpart} "{name}"' 
format_dict["Dielectric_Layer_Fromat_Anisotropic"] = format_dict["Dielectric_Layer_Fromat"]  + ' A {z_erel} {z_mrel} {z_eloss} {z_mloss} {z_esignma}'
Teflon = {"name" : "Teflon", "thickness" : 1524, "xy_erel" : 2.08, "xy_mrel" : 1, "xy_eloss" : 1e-005, "xy_mloss" : 0, "xy_esignma" : 0, "nzpart" : 0}
format_dict["layer_3"] = format_dict["Dielectric_Layer_Fromat"].format(**Teflon)
Sapphire = {"name" : "Sapphire", "thickness" : 500, "xy_erel" : 9.265, "xy_mrel" : 1, "xy_eloss" : 1e-008, "xy_mloss" : 0, "xy_esignma" : 0, "nzpart" : 0, "z_erel" : 11.34, "z_mrel" : 1, "z_eloss" : 3.5e-008, "z_mloss" : 0, "z_esignma" : 0}
format_dict["layer_2"] = format_dict["Dielectric_Layer_Fromat_Anisotropic"].format(**Sapphire)
Vacuum = {"name" : "Vacuum", "thickness" : 3, "xy_erel" : 1, "xy_mrel" : 1, "xy_eloss" : 0, "xy_mloss" : 0, "xy_esignma" : 0, "nzpart" : 0}
format_dict["layer_1"] = format_dict["Dielectric_Layer_Fromat"].format(**Vacuum)


######### Declare Device/Structure Configuration ####################
##This is necessary for defining the ports and polygons....
Through_Line_Layer = 1  #e.g. Mask layer of the Through_Line_Layer is 1
Resonator_Trace_Layer = 2
Metal_Layers = {Through_Line_Layer:{"metal":Niobium,"level":0, "ports":True},Resonator_Trace_Layer:{"metal":Niobium,"level":1,"ports":False}}
total_polygon_list = reduce(lambda layer1, layer2: polygons[layer1]+polygons[layer2], Metal_Layers.keys()) 
total_poly_extremes = Compute_Poly_Extremes(total_polygon_list,0)

######### Define Box Settings #######################################
format_dict["num_metal_lev"] = 2
format_dict["box_width_x"] = extend_box['x_min'] + extend_box['x_max'] + total_poly_extremes['bounding_box_x_max'] - total_poly_extremes['bounding_box_x_min'] # X_Length
format_dict["box_width_y"] = extend_box['y_min'] + extend_box['y_max'] + total_poly_extremes['bounding_box_y_max'] - total_poly_extremes['bounding_box_y_min'] # Y_Length
format_dict["xcells2"] = 2*388 #2 times the number of cells in the x dir
format_dict["ycells2"] = 2*427 #2 times the number of cells in the y dir
format_dict['lorgn'] = '{dX} {dY} L'.format(dX = 0, dY = format_dict["box_width_y"])#format_dict["box_width_y"]) # Local Origin: dX and dY are local origin location offset from upper right corner of substrate box


###### Define POLYGONS and find PORT vertices #######################
format_dict['Polygon_Format'] = n +'{level} {num_of_vertices} {metal_type} {fill_type} {polygon_id} {xmin} {ymin} {xmax} {ymax} {conmax} 0 0 {edgemesh_on}' + n + '{vertices}' + 'END'
#{xmin} {ymin} {xmax} {ymax}: define the minimum/maximum subsection size in number of cells for each dimension
#{conmax} : is the maximum length for a conformal mesh subsection. If this value is zero, the maximum length for a conformal mesh subsection is automatically calculated
format_dict["POLYGONS"] = ''
polygon_id = 1
num_of_vertices = 0
vertices = ''
port_dict = {}

fill_types = {"conformal": "V", "diagonal":"T", "staircase":"N"}
def fill_type(m):
	if m > 5:
		return fill_types["conformal"]
	else:
		return fill_types["staircase"]

def find_port_vertex(port_dict,bound):
	''' bound is x_min, x_max, y_min or y_max'''
	direction = bound[0]
	poly_bound = 'poly_'+bound
	extreme_bound = 'bounding_box_' + bound

	if poly_extremes[extreme_bound] == total_poly_extremes[extreme_bound] and extend_poly[bound] == True:
		for poly in poly_extremes[poly_bound]:
			points = polygons[layer][poly-Metal_Layers[layer]['polygon_id_start']]
			points_view = np.array(map(tuple,points.tolist() + [points.tolist()[0]]),dtype =[('x', '<f8'), ('y', '<f8')])
			
			#pick out the vertices along the given direction which are equal to the a value that coencides with the box edge and that are equal to the next polygon vertex
			vertices = [l for l in xrange(points_view[direction].size-1) if (points_view[direction][l] ==  points_view[direction][l+1]) and points_view[direction][l] == total_poly_extremes[extreme_bound]]

			if vertices != []:
				#Add vertex to port_dict if a vertex is found
				#then add port location point along ling between that vertex and the next vertex on the polygon
				#this dict will be used to define the ports
				
				v1 = divmod(vertices[0]+1,points.shape[0])[1] # roll around vertex index if its at the end of the array
				vertices.append(points[vertices[0]] + points[v1]/2)
				port_dict[poly] = vertices
				
				## Here we extend the polygons found above to the edge of the box.
				points_view = points.view(dtype=[('x', '<f8'), ('y', '<f8')])
				for i in xrange(points_view[direction].size):
					if points_view[direction][i] == total_poly_extremes[extreme_bound]:
						points_view[direction][i] = points_view[direction][i] + {"x_min":-1, "x_max":1, "y_min":-1, "y_max":1}[bound]*extend_box[bound]
	return port_dict

def find_interal_port_vertex(port_dict):
	if  internal_port == True:
		Mid_Point = np.array([float(num) for  num in Phase_Midpoint.replace(' ', '').strip('[').strip(']').split(';')])



	return port_dict

def translate_point(point):
	''' translates polygon point to go in bounding box with whatever box extension is specified'''
	return np.array([point[0]-total_poly_extremes['bounding_box_x_min']+extend_box['x_min'],point[1]-total_poly_extremes['bounding_box_y_min']+extend_box['y_min']])

Polygon_Format = {"edgemesh_on": "Y", "xmin" : 4, "ymin": 4, "xmax" : 10,  "ymax" : 10,  "conmax": 0}

for layer in Metal_Layers.keys():
	polygon_list = polygons[layer]
	Metal_Layers[layer]['polygon_id_start'] = polygon_id

	#pick out the polygons that are on the edge of the layers that have ports on them...
	if Metal_Layers[layer]["ports"] == True:
		poly_extremes = Compute_Poly_Extremes(polygons[layer], Metal_Layers[layer]['polygon_id_start'])
		port_dict = find_port_vertex(port_dict,'y_max')
		port_dict = find_port_vertex(port_dict,'y_min')
		port_dict = find_port_vertex(port_dict,'x_max')
		port_dict = find_port_vertex(port_dict,'x_min')

	for poly in polygon_list:
		poly = np.round(poly,decimals=3) #Assuming unit is microns, this rounds to 1 nm precision

		#format the polygon vertices to be printed in the sonnet file. Also translate the polygons from the mask as per extend_box and total_poly_extremes
		for num_of_vertices in xrange(0,np.shape(poly)[0],1):
			pt = translate_point(poly[num_of_vertices])
			vertices += "{0:.3f} {1:.3f} {2}".format(pt[0],pt[1],n)
			if num_of_vertices == 0:
				last_vertex = "{0:.3f} {1:.3f} {2}".format(pt[0],pt[1],n)
		num_of_vertices = num_of_vertices + 2
		vertices += last_vertex
		Polygon_Format.update({"level": Metal_Layers[layer]["level"], "num_of_vertices":num_of_vertices, "metal_type":Metal_Layers[layer]["metal"]["id"],"fill_type":fill_type(num_of_vertices), "polygon_id":polygon_id, "vertices":vertices})
		format_dict["POLYGONS"] += format_dict['Polygon_Format'].format(**Polygon_Format)
		polygon_id += 1
		vertices = ''

format_dict["num_of_polygons"] = polygon_id - 1



######### Define PORTS ##############################################
format_dict["PORTS"] = ''
format_dict['Port_Format'] = 'POR1 STD' + n + 'POLY {polygon_id} 1' + n + '{vertex}' + n + '{port_number} {port_resistance} {port_reactance} {port_inductance} {port_capacitance} {x_location} {y_location}' + n
Port_Format = {"port_resistance":50, "port_reactance":0, "port_inductance": 0, "port_capacitance": 0}
port_number = 1

for port_polygon in port_dict.keys():
	Port_Format.update({"polygon_id":port_polygon, "vertex":port_dict[port_polygon][0],  "port_number":port_number, "x_location":port_dict[port_polygon][1][0], "y_location":port_dict[port_polygon][1][1]})
	format_dict["PORTS"] += format_dict['Port_Format'].format(**Port_Format)
	port_number += 1



######### Define Optimication Settings ##############################
format_dict["max_number_opt_iterations"] = 100

######### Specify Output Files ######################################
format_dict["touchstone"] =  "TS D Y $BASENAME.s2p IC 15 S RI R 50.00000"
format_dict["comma_sep_variable"]  = "CSV D Y $BASENAME.csv IC 15 S RI R 50.00000"
format_dict["folder"] = "$BASENAME" # might not work. might need to say file_name

######### Quick Start Guide Status ##################################




content = content.format(**format_dict)



stream.write(unicode(content)+n)
stream.close()