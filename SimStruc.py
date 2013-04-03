import warnings
import scipy as sp
from scipy.interpolate import griddata
from scipy.optimize import brentq, fminbound
import numpy as np
from numpy import linalg as la

warnings.filterwarnings('always')

class SParam:	
	def __init__(self,S,Port_Z0,Norm_Z0,Eeff,R,C,Freq):
		self.S = S
		self.Port_Z0 = Port_Z0
		self.Norm_Z0 = Norm_Z0
		self.Eeff = Eeff # Effective dielectric constant of the transmission line connected to the port. Complex value
		self.R = R #Equivalent series resistance of port discontinuity, in ohms.
		self.C = C #Equivalent series capacitance of port discontinuity, in F
		self.Freq = np.float64(Freq)
		self.Calc_Port_S() #self.Port_S 

	def __del__(self):
		pass
		#print("s-parameter instance over-written or deleted")

	def __str__(self):
		return "S-Parameters for freq %f" % (self.Freq)

	#def __repr__(self):
		#return "Coord: " + str(self.__dict__)
		#pass

	def Calc_Port_S(self):
		w = 2*np.pi*self.Freq
		j = np.complex(0,1)
		rr = self.Port_Z0/(1+j*w*self.Port_Z0*self.C) #This is the impedance in of Port_Z0 and C in parallel at the port. *Big question is what to do with R*

		r = (rr-self.Norm_Z0)/(rr+self.Norm_Z0.conjugate())
		I = np.identity(self.Norm_Z0.size, dtype = complex)
		Ref = I * r
		a =  (((1 - r.conjugate()) / np.abs(1-r)) * np.sqrt(1-r*r.conjugate()))
		A = I * a
		S_inv = la.inv(self.S)
		A_inv = la.inv(A)
		 
		self.Port_S = np.dot(A_inv, np.dot((self.S - Ref.conj().transpose()),np.dot(la.inv(I-np.dot(Ref,self.S)),A.conj().transpose())))


class Simulation:

	def __init__(self,S,Port_Z0,Norm_Z0,Eeff,R,C,Freq,Sim_Name,*parameter_combo):
		''' parameter_combo is a dict, {parameter_name: value}'''
		self.Sim_Dict_F = {} #Sim_Dict_F[Freq][ParamV],  ParamV = 0 if no parameters
		self.Sim_Dict_P = {} #Sim_Dict_P[ParamV][Freq]
		
		print("%s New Simulation created" % (' '*5))

		self.File_Name = Sim_Name

		S_P = SParam(S,Port_Z0,Norm_Z0,Eeff,R,C,Freq)
		

		if parameter_combo == ():
			parameter_combo = ({'Null':0},)

		Parameter_Value = parameter_combo[0].values()[-1]
		Parameter_Name = parameter_combo[0].keys()[-1]


		if len(parameter_combo) > 1:
			warnings.warn('More than one Paramater = Value given. Taking one of them. Note sure which one. Probably the first one')

		
		self.Parameter_Name = Parameter_Name

		self.Sim_Dict_F[Freq] = {Parameter_Value:S_P}
		self.Sim_Dict_P[Parameter_Value] = {Freq:S_P}

		if Parameter_Name is not 'Null':
			self.Points = np.array([Freq,Parameter_Value])
		elif Parameter_Name is 'Null':
			self.Points = np.array([Freq])

		self.SParams = np.array([S_P])


		

	def __str__(self):
		return "Simpulation Data from %s" % (self.File_Name)	


	def add(self,S,Port_Z0,Norm_Z0,Eeff,R,C,Freq,*Parameter_Value):
		"""if self.Parameter_Name is 'Null' then Parameter_Value are all set to 0"""
		if self.Parameter_Name == 'Null':
			Parameter_Value = (0,)

		S_P = SParam(S,Port_Z0,Norm_Z0,Eeff,R,C,Freq)
		Parameter_Value = Parameter_Value[0]

		if self.Sim_Dict_F.has_key(Freq):
			 self.Sim_Dict_F[Freq][Parameter_Value]  = S_P
		else:
			self.Sim_Dict_F.update({Freq:{Parameter_Value:S_P}})

		if self.Sim_Dict_P.has_key(Parameter_Value):
			self.Sim_Dict_P[Parameter_Value][Freq] = S_P
		else:
			self.Sim_Dict_P.update({Parameter_Value:{Freq:S_P}})

		if self.Parameter_Name is not 'Null':
			self.Points = self.Points.reshape((-1,2),order = 'C')
			self.Points = np.append(self.Points, [[Freq,Parameter_Value]],axis = 0)
		elif self.Parameter_Name is 'Null':
			self.Points = self.Points.reshape((-1,1),order = 'C')
			self.Points = np.append(self.Points, [[Freq]],axis = 0)

		self.SParams = np.append(self.SParams, np.array([S_P]))
	
		

	def values(self,attribute):
		""" Created Class attribute 'Values' and sets it to the SParam Attribute 'attribute' for all points self.Points = [Freq,Parameter_Value]"""

		dt = np.dtype((getattr(self.SParams[0], attribute).dtype, getattr(self.SParams[0], attribute).shape))
		self.Values = np.empty(self.SParams.shape, dtype = dt)
		
		for i in xrange(self.SParams.shape[0]):
			self.Values[i] = getattr(self.SParams[i], attribute)

	
		self.Fmax = max(self.Sim_Dict_F.keys())
		self.Fmin = min(self.Sim_Dict_F.keys())

		self.Pmax = max(self.Sim_Dict_P.keys())
		self.Pmin = min(self.Sim_Dict_P.keys())

		self.Current_Attribute = attribute


	def interp(self,Freq,Parameter_Value = 0):
		""" Interpolates to find Values at (Freq, Parameter_Value = 0) """
		# this and other functions not testing for no Parameter_Value : self.Parameter_Name = 'Null'

		#if Freq <  self.Fmin or Freq > self.Fmax or Parameter_Value < self.Pmin or Parameter_Value > self.Pmax:
		#	warnings.warn('point (Freq,Parameter_Value) is out of bounds. returning nan.')

		return griddata(self.Points,self.Values, (Freq,Parameter_Value), method='cubic')

	def optvalues(self,Freq,value,*indices):
		"""Return the Parameter_Values that yields "value" at "Freq".  indicies are for matrix valued attributes, e.g. "Port_S". 
		So indices 2,0  <->  Port_S[2,0] which is S31. Note this function takes the absolute values of atribute!!"""
		self.Freq_In_Bound(Freq)
		if indices is not ():
			def fun(Parameter_Value): return np.absolute(self.interp(Freq,Parameter_Value)[indices]) - value
		if indices is ():
			def fun(Parameter_Value): return np.absolute(self.interp(Freq,Parameter_Value)) - value

		#x is the optimal Parameter_Value which acheives value
		x  = brentq(fun, self.Pmin, self.Pmax, args=(), xtol=1e-12, rtol=4.4408920985006262e-16, maxiter=100, full_output=False, disp=True)
		
		#xmin is the parameter values which minimizes fun 
		xmin = fminbound(fun, self.Pmin, self.Pmax)

		#xmin is the parameter values which maximizes fun
		def fun2(x): return -1*fun(x)		 
		xmax = fminbound(fun2, self.Pmin, self.Pmax)

		def fun3(Parameter_Value): return fun(Parameter_Value)+value 
		return x, xmin, xmax,fun3

	def Qmin(self, Freq):
		"""return the lowerest possible Q at Freq. This is lowest possible for any values of Parameter_Value"""
		
		self.values("Port_S")
		self.Freq_In_Bound(Freq)
		def fun(Parameter_Value): return -1*np.absolute(self.interp(Freq,Parameter_Value)[2,0])

		#xmin is the parameter values which maximizes fun	 
		xmin_at_Freq = fminbound(fun, self.Pmin, self.Pmax)

		Qmin_at_Freq = np.pi/((np.absolute(self.interp(self.Fmin,xmin_at_Freq)[2,0]))**2)
		
		# def fun(Parameter_Value): return -1*np.absolute(self.interp(self.Fmax,Parameter_Value)[2,0])

		# #xmin is the parameter values which maximizes fun	 
		# xmin_at_Fmax = fminbound(fun, self.Pmin, self.Pmax)

		# Qmin_at_Fmax = np.pi/((np.absolute(self.interp(self.Fmax,xmin_at_Fmax)[2,0]))**2)

		# return Qmin_at_Fmin,Qmin_at_Fmax
		return Qmin_at_Freq

	def Freq_In_Bound(self,Freq):
		if Freq < self.Fmin or Freq > self.Fmax: 
			#Exception('Requested frequency out of bounds')
			raise RuntimeError('Requested frequency out of bounds')

	def __del__(self):
		print("%s simulation instance over-written or deleted" % (' '*5))

	#def __cmp__(self,other): 
	# I get "IndentationError: expected an indented block" here.. Try definfing a normal function to see if this has something to do with __xx__ 
    #		#return self.__dict__ == other.__dict__
    #	print('hello')

		



