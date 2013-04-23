import numpy as np
import gdspy
import Mask_DB
import Compute_Parameters

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
        Geometry_Tuple = Mask_DB.Get_Mask_Data("SELECT Resonators.Width, Computed_Parameters.Resonator_Length, Computed_Parameters.Aux_Coupler_Length,Computed_Parameters.Coupler_Length, Resonators.Meander_Pitch, Resonators.Meander_Zone, Sensors.Pillar_Diameter, Sensors.Pillar_Grid_Spacing, Sensors.Pillar_Clearance,Sensors.Through_Line_Width FROM Resonators, Sensors,Computed_Parameters WHERE Sensors.sensor_id = Resonators.sensor_id AND Resonators.resonator_id = Computed_Parameters.resonator_id AND Resonators.resonator_id = " + str(Resonator_ID) ,'one')
        
        #print("Function %s in module %s: Resonator_Length == None.... Estimating length to be %f" % (__name__, __module__,Geometry_Tuple[1]))
    else:
       Geometry_Tuple = Geometry_Tuple[0]

    
    Resonator_Width,Resonator_Length,Aux_Coupler_Length,Coupler_Length,Meander_Pitch,Meander_Zone,Pillar_Diameter,Pillar_Spacing,Pillar_Clearance,Through_Line_Width = Geometry_Tuple

    # if Resonator_Length == None: #Resonator_Length
    #    # Resonator_Length = Compute_Parameters.Compute_Length(Resonator_ID)

    # if Aux_Coupler_Length == None or Coupler_Length == None: #Aux_Coupler_Length or Coupler_Length
    #     pass


    # Aux_Coupler_Length = 1000.0 
    # Through_Line_Width = 360 
    # Coupler_Length = 1000.0 


    
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
    resonator_cell = gdspy.Cell(Resonator_Name,exclude_from_global=True)
    
    #initialize Resonator trace object
    _y_initial = -(Pillar_Clearance+Pillar_Radius+Resonator_Width/2)
    resonator_start_point = (0, _y_initial)
    trace = gdspy.Path(Resonator_Width, (0, _y_initial)) 
    
    #########################
    # Draw Coupler
    #########################
    #Coupler_Length = 1000.0
    coupler_trace = gdspy.Path(Resonator_Width, resonator_start_point)
    coupler_trace.segment(Resonator_Trace_Layer, Coupler_Length, '-x')
    resonator_cell.add(coupler_trace)

    #Aux_Coupler_Length = 1000.0
    #Through_Line_Width = 360

    if Aux_Coupler_Length is not 0.0:
        # Find Start Point
        aux_coupler_start_point = (coupler_trace.x- 0.5*Through_Line_Width, coupler_trace.y+0.5*Resonator_Width)

        aux_coupler_trace = gdspy.Path(Through_Line_Width, aux_coupler_start_point)
        aux_coupler_trace.segment(Resonator_Trace_Layer,Aux_Coupler_Length,'-y')
        resonator_cell.add(aux_coupler_trace)
    #########################


        

    #Adjust Resonator Length
    #Resonator_Length = Resonator_Length-Coupler_Length Not Necessary!
       
    #add small section to trace to compensate for x distance of 180 degree turn
    _turn_outer_radius = Resonator_Width/2 + meander_radius
    if Resonator_Width + meander_radius  < Resonator_Length:
        trace.segment(Resonator_Trace_Layer, _turn_outer_radius, '+x')
        

           
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
                resonator_cell.add(gdspy.Round(Pillar_Layer, (_x, _y), _r))
                _x -= Pillar_Spacing
        elif (Aux_Coupler_Length != 0.0) and (Aux_Coupler_Length <= Resonator_Width) or (_fold_bundle_num ==0):# note condition _fold_bundle_num ==0 so that top row of pillars is drawn on top of Aux coupler no matter what
            #print("cond 2")
            _x_min = _x_min - Through_Line_Width
            while _x >= -(Coupler_Length+Through_Line_Width):
                resonator_cell.add(gdspy.Round(Pillar_Layer, (_x, _y), _r))
                _x -= Pillar_Spacing
        elif (Aux_Coupler_Length != 0.0) and (Aux_Coupler_Length >= Resonator_Width) and (_y > aux_coupler_trace.y- Pillar_Radius - Pillar_Clearance):#note that aux_coupler_trace may not be defined
            #print("cond 3, _y = %f" % _y)
            _x_min = _x_min - Through_Line_Width
            while _x >= -(Coupler_Length-Pillar_Clearance):
                resonator_cell.add(gdspy.Round(Pillar_Layer, (_x, _y), _r))
                _x -= Pillar_Spacing
        elif (Aux_Coupler_Length != 0.0) and (Aux_Coupler_Length >= Resonator_Width) and (_y < aux_coupler_trace.y- Pillar_Radius - Pillar_Clearance):
            #print("cond 4, _y = %f" % _y)
            _x_min = _x_min - Through_Line_Width
            while _x >= -(Coupler_Length+Through_Line_Width):
                resonator_cell.add(gdspy.Round(Pillar_Layer, (_x, _y), _r))
                _x -= 2*Pillar_Spacing
        else:
            print('encountered unknown pillar zone pillar drawn condition')

        _x += Pillar_Spacing
        if (_x - _x_min) > _r*2: # dont draw if pillars intersect
            resonator_cell.add(gdspy.Round(Pillar_Layer, (_x_min, _y), _r))
  
    rung_count = 0
    #The Resonator and its interspersed pillars are drawn here
    while trace.length <=  Resonator_Length:      
        #Draw Straight length of resonator
        if _meander_straight + trace.length <= Resonator_Length:
            trace.segment(Resonator_Trace_Layer,_meander_straight , _segment_direction[_fold_num%2])
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
                    resonator_cell.add(gdspy.Round(Pillar_Layer, (_pillar_x_index, -_pillar_y_index), Pillar_Radius))
                    _pillar_x_index += ((-1)**(_fold_bundle_num))*Pillar_Spacing  
                    _pillar_index+=1           
                _pillar_x_index += ((-1)**(_fold_bundle_num))*(-Pillar_Spacing)
                _fold_bundle_num += 1
                #Add a Pillar on left of resonator meander
                resonator_cell.add(gdspy.Round(Pillar_Layer,( -(Pillar_Clearance + Pillar_Radius),-_pillar_y_index),Pillar_Radius))
                
                #Add a Pillar on right of resonator meander
                resonator_cell.add(gdspy.Round(Pillar_Layer,(Meander_Zone+Pillar_Clearance+Pillar_Radius-_meander_zone_delta,-_pillar_y_index),Pillar_Radius))
                _pillar_index = 0
                _pillar_y_index+=_pillar_y_Spacing
            else: #This is the case where multiple rows of pillar fit between resonator rungs (within the meander pitch)
                _pillar_y_index=_current_rung_y_value+Resonator_Width/2 + Pillar_Clearance + Pillar_Radius
                for i in xrange(int(_pillar_bundle_size+1)): 

                    #Draw the pillars in the coupler zone
                    draw_coupler_zone_pillars() #must be called before _fold_bundle_num is incremented

                    while _pillar_index*Pillar_Spacing <= _pillar_straight:                        
                        resonator_cell.add(gdspy.Round(Pillar_Layer, (_pillar_x_index, _pillar_y_index), Pillar_Radius))
                        _pillar_x_index += ((-1)**(_fold_bundle_num))*Pillar_Spacing  
                        _pillar_index+=1           
                    _pillar_x_index += ((-1)**(_fold_bundle_num))*(-Pillar_Spacing)
                    _fold_bundle_num += 1
                    #Add a Pillar on left of resonator meander
                    resonator_cell.add(gdspy.Round(Pillar_Layer,( -(Pillar_Clearance + Pillar_Radius),_pillar_y_index),Pillar_Radius))

                    #Add a Pillar on right of resonator meander
                    resonator_cell.add(gdspy.Round(Pillar_Layer,(Meander_Zone+Pillar_Clearance+Pillar_Radius-_meander_zone_delta,_pillar_y_index),Pillar_Radius))
                    _pillar_index = 0
                    _pillar_y_index+=_pillar_y_Spacing
            if _break_after_pillars == 1:
                break
                
        
        #for the case that Resonator_Length < _meander_straight. This makes sure that the top row of pillars is drawn.
        if trace.length >= Resonator_Length:
            break

        #Draw 90 degree turn so that resonator path is oriented in y direction
        if trace.length + 0.5*np.pi*meander_radius <= Resonator_Length:
            trace.turn(Resonator_Trace_Layer, meander_radius, _angel_direction[_fold_num%2])
        elif _break_after_pillars is not 1:
            partial_turn(Resonator_Trace_Layer, trace, Resonator_Length, meander_radius,  _angel_direction[_fold_num%2])
            _break_after_pillars = 1
                
        #Decide if turn extension is needed, and if so, draw turn extension in y direction    
        if ((_fold_bundle_size > 0)  and  ((_fold_num+1)%(_fold_bundle_size+1) == 0.0)) or ((_turn_extension > 0) and (_fold_bundle_size == 0.0)):
            if  (trace.length + _turn_extension <= Resonator_Length):
                trace.segment(Resonator_Trace_Layer,_turn_extension, '-y')
            elif _break_after_pillars is not 1:
                partial_segment(Resonator_Trace_Layer, trace, Resonator_Length, '-y')
                _break_after_pillars = 1

        #Draw 90 degree turn so that resonator path is oriented back in x direction                      
        if trace.length + 0.5*np.pi*meander_radius <= Resonator_Length:
            trace.turn(Resonator_Trace_Layer, meander_radius, _angel_direction[_fold_num%2])
        elif _break_after_pillars is not 1:
            partial_turn(Resonator_Trace_Layer, trace, Resonator_Length, meander_radius,  _angel_direction[_fold_num%2])
            _break_after_pillars = 1
        
        _fold_num+=1
    
    _current_y_value = min(_current_rung_y_value,trace.y)

    #Draw Bottom row of Pillars no matter what
    _pillar_y_index=_current_y_value-Resonator_Width/2 - Pillar_Clearance - Pillar_Radius
    draw_coupler_zone_pillars()   
    while _pillar_index*Pillar_Spacing <= _pillar_straight:
        resonator_cell.add(gdspy.Round(Pillar_Layer, (_pillar_x_index, _pillar_y_index), Pillar_Radius))
        _pillar_x_index += ((-1)**(_fold_bundle_num))*Pillar_Spacing  
        _pillar_index+=1           
    _pillar_x_index += ((-1)**(_fold_bundle_num))*(-Pillar_Spacing)
    _fold_bundle_num += 1   
    #Add a Pillar on left of resonator meander
    resonator_cell.add(gdspy.Round(Pillar_Layer,( -(Pillar_Clearance + Pillar_Radius),_pillar_y_index),Pillar_Radius))
    #Add a Pillar on right of resonator meander
    resonator_cell.add(gdspy.Round(Pillar_Layer,(Meander_Zone+Pillar_Clearance+Pillar_Radius-_meander_zone_delta,_pillar_y_index),Pillar_Radius))
         
    #Add Resonator Label
    resonator_cell.add(gdspy.Text(Resonator_Trace_Layer, Resonator_Name, 3*Pillar_Radius, (-Pillar_Spacing/2,Pillar_Radius+5))) # -Pillar_Radius/2
    
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
    Res_Dict = {"Meander_Pitch": Meander_Pitch,"Meander_Zone":_new_meander_zone,"Meander_Length":_meander_length, "Resonator_Metal_Area":trace.area(),"Patch_Area":_meander_length*_new_meander_zone,"Turn_Extension":_turn_extension,"Rungs":rung_count}

    if Update_DB == True:
        Mask_DB.Update_Computed_Parameters(Resonator_ID, Res_Dict)
    
    return resonator_cell,_y_initial

def partial_turn(layer, trace, Resonator_Length, turn_radius, turn_direction):
    arc_angle = (Resonator_Length - trace.length)/turn_radius
    if turn_direction == 'r':
        arc_angle = -arc_angle
    trace.turn(layer, turn_radius, arc_angle)
    return trace

def partial_segment(layer, trace, Resonator_Length, direction):
    length = Resonator_Length - trace.length
    trace.segment(layer,length, direction)
    return trace


        