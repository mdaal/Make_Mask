import cPickle as  pickle
import io

if 0:
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

if 1:
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

	num_simulation = Make_Mask.Make_Mask('Mask_Files',File_Name = "Mask_Data.db") #why not :memory:??
	Make_Mask.Execute_Coupler_Simulations(num_simulation)

