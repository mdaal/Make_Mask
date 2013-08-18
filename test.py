
if 0:
	import cPickle as  pickle
	import io


	dest = open('test.pkl',mode='wb')
	mypickler = pickle.Pickler(dest,2)

	if not 'Sim' in vars():
		Sim = {}
		Sim['test'] = 456


	mypickler.dump(Sim)

	source = open('test.pkl',mode='rb') #or mode = 'r'
	myunpickler = pickle.Unpickler(source)
	j = myunpickler.load()
	dest.close()
	source.close()

if 0:
	favorite_color = { "lion": "yellow", "kitty": "red" }
	pickle.dump( favorite_color, io.open( "test.pkl", "wb" ) )
	del favorite_color
	favorite_color = pickle.load( io.open( "test.pkl", "rb" ) )




if 0: ## This works use it
	import Parse_Sonnet_Response
	Sim = Parse_Sonnet_Response.Parse_Sonnet_Response('log_response.log')
	## !!! Will get a "EOFError: " if file is not closed before opening it
	dest.close()
	source.close()

	#this works. .. Make sure that dest was closed before trying to open 
	dest = io.open( "test.pkl", "wb" )
	pickle.dump( Sim, dest, -1 ) # -1 means pickle using highest protocol, which writes file in binary

	#pickle.dump( Sim, io.open( "test.pkl", "wb" ), -1 )

	del Sim

	#This works..
	source = io.open( "test.pkl", "rb" )
	SimS = pickle.load( source )

	#This also works....
	#SimS = pickle.load( io.open( "test.pkl", "rb" ) )

	#dest.close()
	#source.close()

if 0:
	import shelve
	import Parse_Sonnet_Response

	Sim = Parse_Sonnet_Response.Parse_Sonnet_Response('log_response.log')
	d = shelve.open('data.shlv',protocol=-1, writeback=False) # set writeback=True if you want to mutate an object and have d commit comutated object to disk upon d.close() or d.sync()

	d['Shelve_Sim'] = Sim
	del Sim

	d['dict'] = {1: 23, 'kitty': 2, 'g': 'h'}

	d.close()


if 0: # does not work "InterfaceError: Error binding parameter :SIM - probably unsupported type."
	import sqlite3
	from SimStruc import Simulation
	import Parse_Sonnet_Response

	def adapter_func(obj):
	    """Convert from in-memory to storage representation.
	    """
	    print 'adapter_func(%s)\n' % obj
	    return pickle.dumps(obj)#, HIGHEST_PROTOCOL)

	def converter_func(data):
	    """Convert from storage to in-memory representation.
	    """
	    print 'converter_func(%r)\n' % data
	    return pickle.loads(data)


	# Register the functions for manipulating the type.
	sqlite3.register_adapter( Simulation, adapter_func)
	sqlite3.register_converter("Simulation", converter_func)

	connection = sqlite3.connect(":memory:",detect_types=sqlite3.PARSE_DECLTYPES) #to try to store sim types
	#connection = sqlite3.connect(":memory:")
	cursor = connection.cursor()

	sql_cmd = """CREATE TABLE  Simulation_Data (simid INTEGER PRIMARY KEY AUTOINCREMENT, CouplerSweep  Simulation, AuxCouplerSweep  Simulation)"""
	cursor.execute(sql_cmd)

	#Sim = Parse_Sonnet_Response.Parse_Sonnet_Response('log_response.log')
	#cursor.execute("INSERT INTO  Simulation_Data (simid) VALUES (1)")
	#cursor.execute('INSERT INTO  Simulation_Data (CouplerSweep) Values :SIM',  {'SIM' : Sim})

	# Create some objects to save.  Use a list of tuples so we can pass
	# this sequence directly to executemany().
	to_save = [ Parse_Sonnet_Response.Parse_Sonnet_Response('log_response.log'),
	            Parse_Sonnet_Response.Parse_Sonnet_Response('log_response.log'),
	            ]
	cursor.executemany("INSERT INTO Simulation_Data (CouplerSweep) VALUES (?)", to_save)


	#cursor.execute('UPDATE Simulation_Data SET CouplerSweep =  :SIM WHERE simid = 1', {'SIM' : Sim})

if 0: #dont know if this works
	import sqlite3
	from SimStruc import Simulation
	import Parse_Sonnet_Response
	connection = sqlite3.connect(":memory:")
	cursor = connection.cursor()


	sql_cmd = """CREATE TABLE  Simulation_Data (simid INTEGER PRIMARY KEY AUTOINCREMENT, CouplerSweep  blob, AuxCouplerSweep  blob)"""
	cursor.execute(sql_cmd)

	# Here we force pickle to use the efficient binary protocol (protocol=2). This means you absolutely must use an SQLite BLOB field
	# and make sure you use sqlite3.Binary() to bind a BLOB parameter.
	Sim = Parse_Sonnet_Response.Parse_Sonnet_Response('log_response.log')
	cursor.execute("insert into Simulation_Data(CouplerSweep) values (?)", (sqlite3.Binary(pickle.dumps(Sim, protocol=2)),))

	# If we use old pickle protocol (protocol=0, which is also the default),
	# we get away with sending ASCII bytestrings to SQLite.
	# p2 = Point(-5, 3.12)
	# cur.execute("insert into pickled(data) values (?)", (pickle.dumps(p2, protocol=0),))

	# Fetch the BLOBs back from SQLite
	cursor.execute("select CouplerSweep from Simulation_Data")
	#s = cursor.fetchall()
	for row in cursor:
		s = row[0]

	# Deserialize the BLOB to a Python object - # pickle.loads() needs a
	# bytestring.
	Sim2 = pickle.loads(str(s))
	#Sim2 = pickle.loads(str(s[0][1]))


#to sear for a column.. returns all tables containing something like "Meander"
#Mask_DB.Get_Mask_Data('SELECT name FROM sqlite_master where sql like("%Meander%")',fetch = 'all')

if 0:
	print('')
	#suppose that the functions is defined as:
	#Draw_Resonator(Resonator_Name,Resonator_ID, Resonator_Trace_Layer = 1, Pillar_Layer = 2, Y_Pitch_Tight = False, X_Pitch_Tight = False,Update_DB = True, *Geometry_Tuple):

	#this gives an error - SyntaxError: non-keyword arg after keyword arg
	#Resonator_ID = 1 is parses as a keyword  though it it not
	#Res_Tuple= Draw_Resonator(Res_Name,Resonator_ID = 1,Geometry_Tuple, Y_Pitch_Tight = True,  X_Pitch_Tight = True,Update_DB = False)

	#this also gives an error - SyntaxError: non-keyword arg after keyword arg
	#even though Geometry_Tuple was defined at the end. postional arguments must always come before keyword arguments
	#Res_Tuple= Draw_Resonator(Res_Name,1, Y_Pitch_Tight = True,  X_Pitch_Tight = True,Update_DB = False,Geometry_Tuple)

	#The following does not give an error, but print(Geometry_Tuple) gives () --> the function does not find geometry tuple
	#Res_Tuple= Draw_Resonator(Res_Name,1,Geometry_Tuple, Y_Pitch_Tight = True,  X_Pitch_Tight = True,Update_DB = False)

	#if i supply all keywords, this also gives an error - SyntaxError: non-keyword arg after keyword arg
	#Res_Tuple= Draw_Resonator(Res_Name,1,Resonator_Trace_Layer =1,Pillar_Layer =2,Y_Pitch_Tight = True, X_Pitch_Tight =True,Update_DB = False,Geometry_Tuple)

	# this gives the error, "TypeError: Draw_Resonator() got multiple values for keyword argument 'Resonator_Trace_Layer'" as it Resonator_Trace_Layer is getting 1 and Geometry_Tuple
	#Res_Tuple= Draw_Resonator(Res_Name,1,Geometry_Tuple,Resonator_Trace_Layer =1,Pillar_Layer =2,Y_Pitch_Tight = True, X_Pitch_Tight =True,Update_DB = False)

	#THIS WORKS!
	#Res_Tuple= Draw_Resonator(Res_Name,1,1,2,True, True,False,Geometry_Tuple)

	#see:
	#http://stackoverflow.com/questions/8486067/python-positional-args-and-keyword-args

if 0:
	schemata_dict = {}
	table_names = Mask_DB.Get_Mask_Data('SELECT name FROM sqlite_master WHERE type = "table"',fetch = 'all')
	table_names.remove((u'sqlite_sequence',))
	for table in tablenames:
		columns = Mask_DB.Get_Mask_Data('pragma table_info(Resonators)',fetch = 'all')
	#for col in columns

	schemata_dict[table[0]]
if 0:
	import numpy as np
	import matplotlib.pyplot as plt
	import Parse_Sonnet_Response, SimStruc
	import scipy as sp 

	#exec("%reload_ext SimStruc") # does not work 
	reload(SimStruc)
	Sim = Parse_Sonnet_Response.Parse_Sonnet_Response('aux_log_response.log')

	attribute = "Port_S"
	Freq = 790000000 #Hz
	Sim.values(attribute)

	Fmin = Sim.Fmin  # Hz 
	Fmax = Sim.Fmax  # Hz 
	Pmin = Sim.Pmin  # um
	Pmax = Sim.Pmax  # um


	Qc = 60000

	#start ipython as such..
	#ipython --pylab=wx


	f, axarr = plt.subplots(2, 2)
	#f.set_size_inches(8*1680/1050, 8)

	S31 = np.sqrt(np.pi/np.float(Qc))
	#S31 = 0.00015



	index_i = 2
	index_j = 0

	p, xmin, xmax,fun = Sim.optvalues(Freq,S31,index_i,index_j)	
	grid_x, grid_y = np.mgrid[Sim.Fmin:Sim.Fmax:200j, Sim.Pmin:Sim.Pmax:200j]
	imgplot = axarr[0,0].imshow(np.absolute(Sim.interp(grid_x, grid_y))[:,:,index_i,index_j].T, extent=(Fmin,Fmax,Pmin,Pmax), aspect = 'auto',origin ='lower')
	#f.colorbar(imgplot, ax=axarr[0,0])
	axarr[0,0].set_title('|%s$_{%i}$$_{%i}$|' % (attribute,index_i+1,index_j+1))
	axarr[0,0].set_ylabel('Coupler Offset [$\mu$m]')
	axarr[0,0].set_xlabel('Frequency [Hz]')
	axarr[0,0].vlines(Freq, Sim.Pmin,Sim.Pmax, color='k', linestyles='solid',linewidth=2)
	axarr[0,0].hlines(p, Sim.Fmin,Sim.Fmax, color='k', linestyles='solid',linewidth=2)

	x = np.linspace(Pmin,Pmax,200)
	y = np.absolute(Sim.interp(Freq,x)[:,index_i,index_j])
	axarr[1,0].semilogy(x,y, label='f =%s GHz' % round(float(Freq)/pow(10,9),2))
	plt.setp(axarr[1,0].lines, linewidth=2)#ax.lines if axis object
	axarr[1,0].set_title('|%s$_{%i}$$_{%i}$|' % (attribute,index_i+1,index_j+1))
	axarr[1,0].set_ylabel('|%s$_{%i}$$_{%i}$|' % (attribute,index_i+1,index_j+1))
	axarr[1,0].set_xlabel('Coupler Offset [$\mu$m]')
	axarr[1,0].vlines(p, fun(xmin),fun(xmax), color='k', linestyles='solid',linewidth=2)
	#axarr[1,0].vlines(S31,  color='k', linestyles='solid',linewidth=2)
	axarr[1,0].grid(True)
	axarr[1,0].yaxis.grid(True,which='minor')
	axarr[1,0].legend()

	index_i = 2
	index_j = 2
	imgplot = axarr[0,1].imshow(np.angle(Sim.interp(grid_x, grid_y),deg=True)[:,:,index_i,index_j].T, extent=(Fmin,Fmax,Pmin,Pmax), aspect = 'auto',origin ='lower')
	axarr[0,1].vlines(Freq, Sim.Pmin,Sim.Pmax, color='k', linestyles='solid',linewidth=2)
	axarr[0,1].hlines(p, Sim.Fmin,Sim.Fmax, color='k', linestyles='solid',linewidth=2)
	#axarr[0,1].hlines(x, Sim.Fmin,Sim.Fmax, color='k', linestyles='solid',linewidth=2)
	axarr[0,1].set_title('ANG[%s$_{%i}$$_{%i}$] Degrees' % (attribute,index_i+1,index_j+1))
	axarr[0,1].set_ylabel('Coupler Offset [$\mu$m]')
	axarr[0,1].set_xlabel('Frequency [Hz]')
	#f.colorbar(imgplot, ax=axarr[0,1])


	y = np.absolute(np.angle(Sim.interp(Freq,x)[:,index_i,index_j], deg = True))
	axarr[1,1].plot(x,y, label='f =%s GHz' % round(float(Freq)/pow(10,9),2))
	plt.setp(axarr[1,1].lines, linewidth=2)#ax.lines if axis object
	axarr[1,1].legend(loc = 'best')
	axarr[1,1].set_title('ANG[%s$_{%i}$$_{%i}$]' % (attribute,index_i+1,index_j+1))
	axarr[1,1].set_ylabel('ANG[%s$_{%i}$$_{%i}$]' % (attribute,index_i+1,index_j+1))
	axarr[1,1].set_xlabel('Coupler Offset [$\mu$m]')
	axarr[1,1].grid(True)
	#f.set_size_inches(6, 6)
	#ax.autoscale_view()
	#plt.ion()
	#f.tight_layout()
	l = plt.get_current_fig_manager()
	l.resize(800, 800)
	plt.show()

if 0:
	from scipy import optimize
	def fun(x): return np.absolute(Sim.interp(800000000,x)[2,0]) - 0.00015
	x  = optimize.brentq(fun, Sim.Pmin, Sim.Pmax, args=(), xtol=1e-12, rtol=4.4408920985006262e-16, maxiter=100, full_output=False, disp=True)
	
	xmin = optimize.fminbound(fun, Sim.Pmin, Sim.Pmax)
	def fun2(x): return -1*fun(x)
	xmax = optimize.fminbound(fun2, Sim.Pmin, Sim.Pmax)

if 0:
	import gdspy
	import os
	#For Test Only! Remove when deployed
	gdspy.Cell.cell_dict = {}

	align_cell = gdspy.Cell('Alignment_Marks')
	align_cell2 = gdspy.Cell('Alignment_Marks2')
	width_1 = 5  #Width of X on pillar layer
	width_2 = 10 #Width of X on Through Line layer
	P_1 = gdspy.Path(width_1, (0, 10))

	Through_Line_Layer = 1
	Resonator_Trace_Layer = 2
	Pillar_Layer = 3
	primitives = []
	# P1=gdspy.Rectangle(7, (2.5, 2.5), (100+2.5, 100+2.5))
	# P2=gdspy.Rectangle(7, (-2.5, 2.5), (-(100+2.5), (100+2.5)))
	# P3=gdspy.Rectangle(7, (-2.5, -2.5), (-(100+2.5), -(100+2.5)))
	# P4=gdspy.Rectangle(7, (2.5, -2.5), ((100+2.5), -(100+2.5)))

	align_cell.add(gdspy.Rectangle(7, (2.5, 2.5), (100+2.5, 100+2.5)))
	align_cell.add(gdspy.Rectangle(7, (-2.5, 2.5), (-(100+2.5), (100+2.5))))
	align_cell.add(gdspy.Rectangle(7, (-2.5, -2.5), (-(100+2.5), -(100+2.5))))
	align_cell.add(gdspy.Rectangle(7, (2.5, -2.5), ((100+2.5), -(100+2.5))))

	align_cell2.add(gdspy.Rectangle(7, (-(100+2.5), -(100+2.5)), ((100+2.5), (100+2.5))))

	#primitives.append(gdspy.PolygonSet(0, [P1.points ,P2.points,P3.points,P4.points]))
	#primitives.append(gdspy.PolygonSet(0,B.points))
	primitives = [gdspy.CellReference(align_cell, origin=(0, 0)), gdspy.CellReference(align_cell2, origin=(0, 0))]

	subtraction = lambda p1, p2: p2 and not p1
	bool_cell = gdspy.Cell('Bool_Alignment_Marks')
	bool_cell.add(gdspy.boolean(1, primitives, subtraction, max_points=199))	


	name = os.path.abspath(os.path.dirname(os.sys.argv[0])) + os.sep + 'bool_align_mark'

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
	#gdsii = gdspy.GdsImport(name + '.gds')

	## Now we extract the cells we want to actually include in our current
	## structure. Note that the referenced cells will be automatically
	## extracted as well.
	#gdsii.extract('IMPORT_REFS')
	    
	## View the layout using a GUI.  Full description of the controls can
	## be found in the online help at http://gdspy.sourceforge.net/
	gdspy.LayoutViewer(colors=[None] * 64)

if 0:
	import gdspy
	import os
	import numpy as np
	#For Test Only! Remove when deployed
	gdspy.Cell.cell_dict = {}

	#inner_cross_cell = gdspy.Cell('Inner_Cross')
	#outer_cross_cell = gdspy.Cell('Outer_Cross')

	Through_Line_Layer = 1
	Resonator_Trace_Layer = 2
	Pillar_Layer = 3

	# P_4 = gdspy.Path(cross_line_width, (0, 0))
	# rt2 = np.sqrt(2)
	# P_4.segment(Layer,(rt2*cross_width/2) , np.pi/4)
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


	align_mark_y_separation = 200.
	align_mark_x_separation = 50000.
	align_mark_set_separation = 5000.
	align_cell1 = draw_alignment(Pillar_Layer, Resonator_Trace_Layer,5,5,100,True,True,0*np.pi/4) #Outer_Only == True because Pillar_Layerwill be polarity reversed
	align_cell2 = draw_alignment(Through_Line_Layer, Resonator_Trace_Layer,10,10,200,True,False,np.pi/4)
	test_cell =  gdspy.Cell('Test_Cell')
	test_cell_ref = gdspy.CellArray(align_cell1, 2, 2, [align_mark_x_separation,align_mark_y_separation], origin=(-align_mark_x_separation/2, -align_mark_y_separation/2), rotation=None, magnification=None, x_reflection=False)

	test_cell.add(test_cell_ref)
	test_cell_ref = gdspy.CellArray(align_cell2, 2, 2, [align_mark_x_separation+align_mark_set_separation,align_mark_y_separation], origin=(-(align_mark_x_separation+align_mark_set_separation)/2, -align_mark_y_separation/2), rotation=None, magnification=None, x_reflection=False)

	test_cell.add(test_cell_ref)


	name = os.path.abspath(os.path.dirname(os.sys.argv[0])) + os.sep + 'align_mark'
	gdspy.gds_print(name + '.gds', unit=1.0e-6, precision=1.0e-9)
	print('Sample gds file saved: ' + name + '.gds')
	#gdspy.LayoutViewer(colors=[None] * 64)
	gdspy.LayoutViewer()

if 0:
	import os
	import Parse_Sonnet_Response
	reload(Parse_Sonnet_Response)
	File_Name_or_String = '/Users/miguel_daal/Documents/Projects/Make_Mask_Code/Make_Mask/Sonnet_Files/20130402/CouplerSweep_TLW395TLG000RW256SG03ST500E1120_20130402_214356_Output'
	if os.path.isdir(File_Name_or_String):
		summary_file = ''
		for files in os.listdir(File_Name_or_String):
			if files.endswith("files.txt"):
				summary_file = files
				break
		if summary_file == '':
			raise RuntimeError('No summary file found for simulation data')
		f = io.open(File_Name_or_String+ os.sep +summary_file , mode='r')
		line = f.next()
		Agg_File_Set = False
		while 1:
			if line.startswith('USER_FILE') and Agg_File_Set == False:
				Agg_File = line.split(' ')[1].strip('\n').strip('.s3p')+'_Aggregated.s3p'
				Agg_File_Path = File_Name_or_String+ os.sep +Agg_File 
				Agg_File = io.open(Agg_File_Path , mode='w')
				Agg_File_Set = True
			if line.startswith('OUTPUT_FILE'):
				s3p_file = line.split(' ')[1].strip('\n')
				s3p_file = io.open(File_Name_or_String+ os.sep +s3p_file , mode='r')
				Agg_File.write(s3p_file.read())
				Agg_File.write(unicode('\n%%\n\n'))
				s3p_file.close()
			try:
				line = f.next()
			except:
				Agg_File.close()
				f.close()
				break
if 0:
	import gdspy
	#File = 'Mask_Files/mask.gds'
	File = 'Mask_Test_2/mask.gds'
	gdspy.Cell.cell_dict = {}
	gdsii = gdspy.GdsImport(File)
	for cell_name in gdsii.cell_dict:
		gdsii.extract(cell_name)
	gdspy.LayoutViewer()

if 0:
	try:
	    client = SSHClient()
	    client.load_system_host_keys()
	    client.connect('ssh.example.com')
	    stdin, stdout, stderr = client.exec_command('ls -l')
	finally:
	    if client:
	        client.close()


	#Instead of calling exec_command on the client, get hold of the transport and generate your own channel. The channel can be used to execute a command, 
	#and you can use it in a select statement to find out when data can be read:

	#!/usr/bin/env python
	import paramiko
	import select
	client = paramiko.SSHClient()
	client.load_system_host_keys()
	client.connect('host.example.com')
	transport = client.get_transport()
	channel = transport.open_session()
	channel.exec_command("tail -f /var/log/everything/current")
	while True:
	  rl, wl, xl = select.select([channel],[],[],0.0)
	  if len(rl) > 0:
	      # Must be stdout
	      print channel.recv(1024)
	#The channel object can be read from and written to, connecting with stdout and stdin of the remote command. You can get at stderr by calling channel.makefile_stderr(...)


if 0:
	#plot mask polygons...
	import gdspy
	#cl= gdspy.CellReference("_DS_1020500_", origin=(0, 0), rotation=None, magnification=None, x_reflection=False)
	#pgs = cl.get_polygons(by_layer=False, depth=None)

	pgs = vars()['pgs']

	import numpy as np
	import matplotlib
	from matplotlib.patches import Polygon
	from matplotlib.collections import PatchCollection
	import matplotlib.pyplot as plt


	fig=plt.figure()
	ax=fig.add_subplot(111)


	patches = []


	for j in pgs:
	    polygon = Polygon(j, False)
	    patches.append(polygon)

	colors = 100*np.random.rand(len(patches))
	p = PatchCollection(patches, cmap=matplotlib.cm.jet, alpha=0.4)
	p.set_array(np.array(colors))
	ax.add_collection(p)
	plt.colorbar(p)
	#ax.autoscale_view()
	plt.axis('image')
	#plt.axis('equal')

	plt.show()



if 0: #use this to generate Mask_Parameters.csv file

	cmd = """SELECT Computed_Parameters.resonator_id,Computed_Parameters.sensor_id,Resonators.Design_Freq,Resonators.Width,Computed_Parameters.Design_Q,Computed_Parameters.Coupler_Zone,Sensors.Through_Line_Width, 
	Computed_Parameters.Through_Line_Impedance,Computed_Parameters.Resonator_Impedance,Computed_Parameters.Coupler_Length,Computed_Parameters.Aux_Coupler_Length,Computed_Parameters.Resonator_Eeff,
	Computed_Parameters.Through_Line_Eeff,Computed_Parameters.Resonator_Length,Computed_Parameters.Meander_Pitch,Computed_Parameters.Meander_Zone,Computed_Parameters.Meander_Length,Computed_Parameters.Through_Line_Length,
	Computed_Parameters.Through_Line_Metal_Area,Computed_Parameters.Resonator_Metal_Area,Computed_Parameters.Patch_Area,Computed_Parameters.Turn_Extension,Computed_Parameters.Rungs,Computed_Parameters.Sensor_Pillar_Area,
	Computed_Parameters.Coupler_Phase_Change FROM Computed_Parameters, Resonators, Sensors WHERE Computed_Parameters.resonator_id = Resonators.resonator_id AND Computed_Parameters.sensor_id = Sensors.sensor_id"""

	if 0:
		records = Mask_DB.Get_Mask_Data(cmd)
		f = open('Mask_Parameters.csv', mode = 'w')
		f.write(unicode("resonator_id,sensor_id,Design_Freq [GHz],Resonator_Width,Design_Q,Coupler_Zone,Through_Line_Width,Through_Line_Impedance,Resonator_Impedance,Coupler_Length,Aux_Coupler_Length,Resonator_Eeff,Through_Line_Eeff,Resonator_Length,Meander_Pitch,Meander_Zone,Meander_Length,Through_Line_Length,Through_Line_Metal_Area,Resonator_Metal_Area,Resonator_Patch_Area,Turn_Extension,Rungs,Sensor_Pillar_Area,Coupler_Phase_Change [rad],\n"))

		for rec in records:
			f.write(unicode(str(rec).lstrip('(').rstrip(')')+',\n'))

		#probably want to remove final ',\n' manually
		f.close()

	if 1:
		Mask_Folder = 'Mask_Files'
		records = Mask_DB.Get_Mask_Data(cmd)
		f = open(Mask_Folder + os.sep + 'Mask_Parameters.csv', mode = 'w')
		f.write(unicode("resonator_id,sensor_id,Design_Freq [GHz],Resonator_Width,Design_Q,Coupler_Zone,Through_Line_Width,Through_Line_Impedance,Resonator_Impedance,Coupler_Length,Aux_Coupler_Length,Resonator_Eeff,Through_Line_Eeff,Resonator_Length,Meander_Pitch,Meander_Zone,Meander_Length,Through_Line_Length,Through_Line_Metal_Area,Resonator_Metal_Area,Resonator_Patch_Area,Turn_Extension,Rungs,Sensor_Pillar_Area,Coupler_Phase_Change [rad]\n"))

		data = ''
		for rec in records:
			data = data + unicode(str(rec).lstrip('(').rstrip(')')+'\n')

		f.write(data)
		#probably want to remove final ',\n' manually
		f.close()


if 0:    #print(10*'\a')
    from matplotlib import cm
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, PathPatch
    from matplotlib.patches import Polygon
    from mpl_toolkits.mplot3d import axes3d
    import mpl_toolkits.mplot3d.art3d as art3d

    pgs_dict = Make_Mask.Get_Polygons('S8')

    fig = plt.figure()
    ax=fig.gca(projection='3d')

    for layer in pgs_dict.keys():
        poly_list = pgs_dict[layer]
        for p in poly_list:
            polygon = Polygon(p, closed=  False)
            ax.add_patch(polygon)
            art3d.pathpatch_2d_to_3d(polygon, z=layer, zdir="z")


    ax.set_xlim3d(0, 20000)
    ax.set_ylim3d(0, 20000)
    ax.set_zlim3d(0, 3)

    plt.show()





    fig = plt.figure()
    ax = fig.gca(projection='3d')
    X, Y, Z = axes3d.get_test_data(0.05)
    cset = ax.contour(X, Y, Z, extend3d=True, cmap=cm.coolwarm)
    ax.clabel(cset, fontsize=9, inline=1)

    plt.show()

if 0:
	from mpl_toolkits.mplot3d import axes3d
	import matplotlib.pyplot as plt
	from matplotlib import cm

	fig = plt.figure()
	ax = fig.gca(projection='3d')
	X, Y, Z = axes3d.get_test_data(0.01)
	cset = ax.contour(X, Y, Z, extend3d=True, cmap=cm.coolwarm)
	ax.clabel(cset, fontsize=9, inline=1)

	plt.show()


if 0:
	#############
	# Run This to generate Mask
	#############
	import Make_Mask
	reload(Make_Mask)
	import Sonnet_Interface
	reload(Sonnet_Interface)
	import Sonnet_Coupling
	reload(Sonnet_Coupling)
	import SimStruc
	reload(SimStruc)
	import Parse_Sonnet_Response
	reload(Parse_Sonnet_Response)
	import Mask_DB
	reload(Mask_DB)
	import Compute_Parameters
	reload(Compute_Parameters)
	import Draw_Resonator
	reload(Draw_Resonator)
	import Draw_Sensor
	reload(Draw_Sensor)
	import Draw_Mask
	reload(Draw_Mask)



	
	Make_Mask.Make_Mask(Folder_Name = 'Mask_Files',Mask_DB_Name = "Mask_Data.db", Rebuild_DB = False) #why not :memory:??

	#Make_Mask.Execute_Coupler_Simulations()
	#Make_Mask.Compute_All_Mask_Parameters()
	#Make_Mask.Output_Parameters()
	Make_Mask.Draw_Mask()

	#print(10*'\a')
poly_extremes = {}

prev_x_min  = polygon_list[0][0,0]
prev_x_max	= polygon_list[0][0,0]
prev_y_min  = polygon_list[0][0,1]
prev_y_max  = polygon_list[0][0,1]


if 0:
	for p in xrange(len(polygon_list)):
		d = {}
		d['x_min'] = polygon_list[p][:,0].min()
		d['x_max'] = polygon_list[p][:,0].max()
		d['y_min'] = polygon_list[p][:,1].min()
		d['y_max'] = polygon_list[p][:,1].max()

		poly_extremes[p] = d

		if d['x_min'] <= prev_x_min:
			prev_x_min = d['x_min']
			poly_extremes['poly_x_min'] = set([p])

		if d['y_min'] <= prev_y_min:
			prev_y_min = d['y_min']
			poly_extremes['poly_y_min'] = set([p])

		if d['x_max'] >= prev_x_max:
			prev_x_max = d['x_max']
			poly_extremes['poly_x_max'] = set([p])

		if d['y_max'] >= prev_y_max:
			prev_y_max = d['y_max']
			poly_extremes['poly_y_max'] = set([p])

	for p in xrange(len(polygon_list)):
		if poly_extremes[p]['x_min'] == poly_extremes[list(poly_extremes['poly_x_min'])[0]]['x_min']:
			poly_extremes['poly_x_min'].add(p)
			poly_extremes['bounding_box_x_min'] = poly_extremes[p]['x_min']

		if poly_extremes[p]['y_min'] == poly_extremes[list(poly_extremes['poly_y_min'])[0]]['y_min']:
			poly_extremes['poly_y_min'].add(p)
			poly_extremes['bounding_box_y_min'] = poly_extremes[p]['y_min']

		if poly_extremes[p]['x_max'] == poly_extremes[list(poly_extremes['poly_x_max'])[0]]['x_max']:
			poly_extremes['poly_x_max'].add(p)
			poly_extremes['bounding_box_x_max'] = poly_extremes[p]['x_max']

		if poly_extremes[p]['y_max'] == poly_extremes[list(poly_extremes['poly_y_max'])[0]]['y_max']:
			poly_extremes['poly_y_max'].add(p)
			poly_extremes['bounding_box_y_max'] = poly_extremes[p]['y_max']


if 0:
	dt = [('x', np.float64), ('y', np.float64)]
	k = [[8802.5, 18000.0], [9197.5, 18000.0], [9197.5, 17502.5], [8802.5, 17502.5]]
	g =numpy.array(map(tuple,k),dtype = dt) #i.e. Data must be read in as a list of tuples
	#is the same as 
	g = k.view(dt)


if 0:
	poly_extremes = {}
	start = 1

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

if 0:  # does not work  because "Point" needs to be a class.
	import sqlite3
	

	def adapter_func(obj): 
	    """Convert from in-memory to storage representation.
	    """
	    print 'adapter_func(%s)\n' % obj
	    return pickle.dumps(str(obj))#, HIGHEST_PROTOCOL)

	def converter_func(data):
	    """Convert from storage to in-memory representation.
	    """
	    print 'converter_func(%r)\n' % data
	    return pickle.loads(list(data)


	# Register the functions for manipulating the type.
	sqlite3.register_adapter(Point, adapter_func)
	sqlite3.register_converter("Point", converter_func)

	connection = sqlite3.connect(":memory:",detect_types=sqlite3.PARSE_DECLTYPES) #to try to store sim types
	#connection = sqlite3.connect(":memory:")
	cursor = connection.cursor()

	sql_cmd = """CREATE TABLE  Convert_Data (simid INTEGER PRIMARY KEY AUTOINCREMENT, midpoints Point)"""
	cursor.execute(sql_cmd)

	#Sim = Parse_Sonnet_Response.Parse_Sonnet_Response('log_response.log')
	#cursor.execute("INSERT INTO  Simulation_Data (simid) VALUES (1)")
	#cursor.execute('INSERT INTO  Simulation_Data (CouplerSweep) Values :SIM',  {'SIM' : Sim})

	# Create some objects to save.  Use a list of tuples so we can pass
	# this sequence directly to executemany().
	to_save = [ [1,3],
	            [3.2,5.0833],
	            ]
	cursor.executemany("INSERT INTO Convert_Data (midpoints) VALUES (?)", to_save)

if 0:
	#to extract floats from 
	l = "[1.28573;95853.4]"
	g = lambda f : [ float(num) for  num in f.replace(' ', '').strip('[').strip(']').split(';')]

