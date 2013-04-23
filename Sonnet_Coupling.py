
import numpy as np
import fractions
from datetime import datetime as dt
import os
import io
import Mask_DB

import Sonnet_Interface


def Sonnet_Coupling(simid, Simulation_Type = 0):
    '''
    Simulati0n is a sqlite3 database with the parameters to be used in the Sonnet script
    simid is the id number for the current simulation
    Simulation_Type = "AuxCouplerSweep" is Pad Coupler, (1)
    Simulation_Type = "CouplerSweep" is Line coupler, (0)
    Simulation_Type = "PortCalc" is determine port PortCalc impedances and Eeff (2)


    returns: (sonnet_path,  F_N, Simulation_Geometry, Simulation_Type_Name, Coupler_Space) 
    File_Name looks like: CouplerSweep_TLW360TLG00RW200SG03ST500E1120_20130228_143425.son
    Simulation_Geometry looks like: TLW360TLG00RW200SG03ST500E1120
    Simulation_Type_Name looks like: 'CouplerSweep'
    '''

    simulation_parameters = Mask_DB.Get_Mask_Data("SELECT  Resonators.Width, Sensors.Through_Line_Width, Sensors.Through_Line_Gap, Sensors.X_Length FROM Resonators, Sensors, Wafer WHERE Resonators.sensor_id = Sensors.sensor_id AND Resonators.simid = " + str(simid) + " ORDER BY Sensors.X_Length ASC", 'one')


    Resonator_Width = float(simulation_parameters[0]) #micrometers
    Through_Line_Width = float(simulation_parameters[1]) #micrometers #300 for CPW 360. for microstrip
    Through_Line_CPW_Gap = float(simulation_parameters[2]) #micrometers #300 for CPW, 0. for microstrip
    Sensor_X_Length = float(simulation_parameters[3])  #micrometers

    simulation_parameters = Mask_DB.Get_Mask_Data("SELECT Thickness, Dielectric_Constant, Pillar_Height, Freq_Low,Freg_High FROM Wafer",'one')


    Substrate_Thickness = float(simulation_parameters[0]) #micrometers
    Dielectric_Constant = float(simulation_parameters[1])#11.2 parallel to C-Axis and 9.2 perpendicular to C-Axis
    Substrate_Gap = float(simulation_parameters[2]) #micrometers
    Frequency_Sweep_Start = float(simulation_parameters[3]) # GHz* 10**9 # Hertz
    Frequency_Sweep_End = float(simulation_parameters[4]) # GHz * 10**9 # Hertz

    
    Coupler_Length = 3000.# not really Coupler length. This is the max separation between throughline and edge of "couple" in the simulation 
    

    Resonator_Impedance = 50; 
    Through_Line_Impedance = 50;

    Top_Space = 1524. # space between the surface of through line layer and top of simulation box. AKA - thicnkess of Teflon Press
    Box_Head_Space = 5000. #Space between top of simpulation box and Resonator Origon


    Box_Wall_Separation_X =  10 * (Substrate_Thickness+Substrate_Gap) # Box_Size_X ~= (2*Box_Wall_Separation_X) + Through_Line_Width


    ### -- Coupling Pad Max Length
    if Simulation_Type == 1: #pad coupler
        Max_Coupler_Pad_Length = 3000+Resonator_Width
        Coupler_Zone = 3000 #Not really Coupler zone. This defines the width of the simulation box on the right side of the through line.
    elif (Simulation_Type == 0) or (Simulation_Type == 2):
        Max_Coupler_Pad_Length = 0
        Coupler_Zone = 9000 #Not really Coupler zone. This defines the width of the simulation box on the right side of the through line.
    ###

    Al_Ls = 0.201 #Superconducting Aluminum Sheet Inductance
    Nb_Ls = 0.049  #Superconducting Niobium Sheet Inductance
    Teflon_Er = 2.08
    Teflon_Loss = 0.00001
    Num_Cells_Per_Res_Width = 3.0 #Sets the number of cells that fit in width of the resonator.
    Num_Cells_Per_TL_Width = 3.0 #Sets the number of cells that fit in width of the Through Line.

    if Resonator_Width > Through_Line_Width:
        (multiple,remainder) = divmod(round(Resonator_Width),round(Through_Line_Width))
        Cell_Size_Y = Resonator_Width/(Num_Cells_Per_Res_Width*multiple)
    else:
        Cell_Size_Y = Resonator_Width/Num_Cells_Per_Res_Width


    Box_Head_Space = round(Box_Head_Space/Cell_Size_Y)*Cell_Size_Y #change to the closest multiple of Cell_Size_Y
    Box_Size_Y = round((2*Box_Head_Space+ Resonator_Width + \
    Max_Coupler_Pad_Length) /Cell_Size_Y)*Cell_Size_Y #want the closest multiple of Cell_Size_Y to (2*Box_Head_Space+ Resonator_Width) 



    if Through_Line_CPW_Gap == 0: 
        Cell_Size_X = Through_Line_Width/Num_Cells_Per_TL_Width
    else:        
        Cell_Size_X = fractions.gcd(int(Through_Line_CPW_Gap),int(Through_Line_Width))/Num_Cells_Per_TL_Width


    Box_Wall_Separation_X = round(Box_Wall_Separation_X/Cell_Size_X)*Cell_Size_X # Change to the closest multiple of Cell_Size_X to Box_Wall_Separation_X

    if Simulation_Type == 1: #pad coupler
        Box_Size_X = round((2*Box_Wall_Separation_X + Through_Line_Width + \
        Coupler_Zone)/Cell_Size_X)*Cell_Size_X # want the closest multiple of Cell_Size_X to (Box_Wall_Separation_X + Through_Line_Width + Coupler_Zone)
    elif (Simulation_Type == 0) or  (Simulation_Type == 2):
        Box_Size_X = round((Box_Wall_Separation_X + Through_Line_Width + \
        Coupler_Zone)/Cell_Size_X)*Cell_Size_X # want the closest multiple of Cell_Size_X to (Box_Wall_Separation_X + Through_Line_Width + Coupler_Zone)
        
    #Compute through line polygons ---------------------------------
    Through_Line_Polygons = {}
    Through_Line_Polygons[1] = np.array([[Box_Wall_Separation_X, Box_Wall_Separation_X, (Box_Wall_Separation_X + Through_Line_Width), (Box_Wall_Separation_X + Through_Line_Width)],[0,Box_Size_Y,Box_Size_Y,0]], float)
    if Through_Line_CPW_Gap == 0:
        Coupler_Offset_Min = Through_Line_Polygons[1][0,2]
    else: 
        Through_Line_Polygons[2] = np.array([[0,0,Through_Line_Polygons[1][0,1] - \
        Through_Line_CPW_Gap, Through_Line_Polygons[1][0,0] - Through_Line_CPW_Gap], \
        [ 0,Box_Size_Y,Box_Size_Y,0]],float)
        Through_Line_Polygons[3] = np.array([[Through_Line_Polygons[1][0,3] + \
        Through_Line_CPW_Gap, Through_Line_Polygons[1][0,2] + \
        Through_Line_CPW_Gap,Box_Size_X,Box_Size_X],[0,Box_Size_Y,Box_Size_Y,0]],float)
        Coupler_Offset_Min = Through_Line_Polygons[1][0,2]+Through_Line_CPW_Gap
    #----------------------------------------------------------------

    #Specify Through Line Polygons ----------------------------------
    Polygons = {}
    for i in Through_Line_Polygons.keys():
        Polygons[i] = {}
        Polygons[i]["Points"] =  Through_Line_Polygons[i] # is a numpy array
        Polygons[i]["Layer"] = 0
        Polygons[i]["Mesh"] = "N"
        Polygons[i]["X_Max"] = "1000"
        Polygons[i]["Y_Max"] = "1000"
     
    Polygons[1]["Ports"] = {}
    Polygons[1]["Ports"][1] = np.array([4, Through_Line_Impedance, 0, 0, 0], float)#[Point number, Resistance, Reactance, Inductance, Capacitance] 
    Polygons[1]["Ports"][2] = np.array([2, Through_Line_Impedance, 0, 0, 0], float)
    #------------------------------------------------------------------

    if Simulation_Type == 1:
        Coupler_Offset  = 0 
    elif (Simulation_Type == 0) or  (Simulation_Type == 2):
        Coupler_Offset  = round((Coupler_Zone-Coupler_Length)/Cell_Size_X)*Cell_Size_X
        Max_Coupler_Offset = round((Sensor_X_Length-Coupler_Length)/Cell_Size_X)*Cell_Size_X

    Coupler_Space = Box_Size_X - Coupler_Offset_Min # Distance from the edge of the Through line (on the coupler side) to the box wall.

    Polygons[i+1] = {}
    Polygons[i+1]["Points"] = np.array([[Box_Size_X,Coupler_Offset_Min+(Coupler_Offset),\
    Coupler_Offset_Min+(Coupler_Offset),Box_Size_X],[Box_Head_Space, Box_Head_Space,\
    Box_Head_Space+Resonator_Width,Box_Head_Space+Resonator_Width ]], float)
    Polygons[i+1]["Layer"] = 1
    Polygons[i+1]["Ports"] = {}
    Polygons[i+1]["Ports"][1] = np.array([4, Resonator_Impedance, 0, 0, 0], float)
    Polygons[i+1]["Mesh"] = 'N'
    Polygons[i+1]["X_Max"] = '1000'
    Polygons[i+1]["Y_Max"] = '100'
    i = i+1

    # --- Add Coupling Pad
    if Simulation_Type == 1:
        i = i+1 # <-- should this go at the end of the if statement
        Polygons[i] = {}
        Polygons[i]["Points"] = np.array([[Coupler_Offset_Min,(Coupler_Offset_Min-2*Through_Line_CPW_Gap-Through_Line_Width),(Coupler_Offset_Min-2*Through_Line_CPW_Gap-Through_Line_Width),Coupler_Offset_Min],[Box_Head_Space, Box_Head_Space,Box_Head_Space+Max_Coupler_Pad_Length, (Box_Head_Space+Max_Coupler_Pad_Length)]],float)
        Polygons[i]["Layer"] = 1
        Polygons[i]["Mesh"] = 'N'
        Polygons[i]["X_Max"] = '1000'
        Polygons[i]["Y_Max"] = '100'
    #--------------------
    Num_Polygons = i

    # --- Construct File Name -------------------------
    Simulation_Geometry = Get_Simulation_Geometry(Through_Line_Width, Through_Line_CPW_Gap, Resonator_Width, Substrate_Gap, Substrate_Thickness,Dielectric_Constant)
    F_N = Get_Simulation_Type(Simulation_Type) + '_' + Simulation_Geometry + '_' + dt.now().strftime('%Y%m%d_%H%M%S') 
    

    #--- Declare File Type, Sonnet version and state when file was created (last saved) in header
    SON = 'FTYP SONPROJ 3 ! Sonnet Project File\n' + 'VER 11.52\n' + 'HEADER\n' + 'DAT ' + dt.now().strftime('%m/%d/%Y %H:%M:%S') + '\n' + 'END HEADER\n'

    #--- Specify Dimensions to be used in Sonnet File.
    SON = SON + 'DIM\n' + 'FREQ GHZ\n' + 'IND NH\n' + 'LNG UM\n' +'ANG DEG\n' + 'CON /OH \n' + 'CAP PF\n' + 'RES OH\n' + 'END DIM\n'

    #--- Specify Frequency Sweep block
    SON =  SON + 'FREQ\n' + 'ABS ' + str(Frequency_Sweep_Start) + ' ' + str(Frequency_Sweep_End) + '\n'

    if Simulation_Type == 2:
        Sweep_Width = Frequency_Sweep_End - Frequency_Sweep_Start
        SON = SON + 'STEP ' + str(Frequency_Sweep_Start) + '\n' + 'STEP ' +\
        str(Frequency_Sweep_Start+0.25*Sweep_Width) +'\n'+ 'STEP ' +\
        str(Frequency_Sweep_Start+0.75*Sweep_Width) + '\n' + 'STEP ' +\
        str(Frequency_Sweep_End) + '\n'

    SON = SON + 'END FREQ\n'

    #--- Specify Control Block -- The Frequency sweep resently beig used and other run options
    SON = SON + 'CONTROL\n'
    if (Simulation_Type == 1) or (Simulation_Type == 0):
        SON = SON + 'VARSWP\n'
    elif Simulation_Type == 2:
        SON = SON +'STD\n'

    SON = SON + 'OPTIONS  -d\n' + 'SPEED 0\n' + 'CACHE_ABS 1\n' + 'TARG_ABS 300\n' + 'Q_ACC N\n' + 'END CONTROL\n'

    #--- Specify Box and Dielectric Layers
    SON = SON +  'GEO\n'+ 'TMET "Lossless" 0 SUP 0 0 0 0\n' + 'BMET "Aluminum" 1 SUP 0 0 0 ' + str(Al_Ls)+'\n'
    SON = SON + 'MET "Aluminum" 1 SUP 0 0 0 '+str(Al_Ls)+'\n' + 'MET "Niobium" 2 SUP 0 0 0 ' + str(Nb_Ls)+'\n'
    SON = SON + 'BOX 2 ' + str(int(Box_Size_X)) + ' ' +  str(int(Box_Size_Y)) + ' ' + str(int(2*Box_Size_X/Cell_Size_X)) + ' '+ str(int(np.ceil(2*Box_Size_Y/Cell_Size_Y))) + ' 20 0\n'
    SON = SON + '      ' + str(Top_Space) + ' '+ str(Teflon_Er)+' 1 '+str(Teflon_Loss)+' 0 0 0 "Teflon (PTFE)"\n'
    SON = SON + '      ' + str(Substrate_Thickness) + ' ' + str(Dielectric_Constant) + ' 1 0 0 0 0 "Dielectric"\n'
    SON = SON + '      ' + str(Substrate_Gap) + ' 1 1 0 0 0 0 "Vacuum"\n'

    #--- Specify Parameters
    if Simulation_Type == 1:
        SON = SON + 'GEOVAR Coupler_Pad_Length ANC YDIR 1\n'
        SON = SON + 'NOM ' + str(int(Max_Coupler_Pad_Length)) + '\n'
        SON = SON + 'REF1 POLY ' + str(Num_Polygons) + ' 1\n' + '1\n'
        SON = SON + 'REF2 POLY ' + str(Num_Polygons) + ' 1\n' + '3\n'
        SON = SON + 'PS1 0\n' + 'END\n' + 'PS2 1\n' +  'POLY ' + str(Num_Polygons) + ' 1\n' + '2\n' + 'END\n' + 'END\n'
    elif (Simulation_Type == 0) or  (Simulation_Type == 2):
        SON = SON + 'GEOVAR Coupler_Offset ANC XDIR -1\n'
        SON = SON + 'NOM ' + str(Coupler_Offset) + '\n'
        if Through_Line_CPW_Gap == 0:
            SON = SON + 'REF1 POLY 1 1\n' + '3\n'
        else:
            SON = SON + 'REF1 POLY 3 1\n' + '0\n'
        SON = SON + 'REF2 POLY ' + str(Num_Polygons) + ' 1\n' + '1\n'
        SON = SON + 'PS1 0\n' + 'END\n' + 'PS2 1\n' + 'POLY ' + str(Num_Polygons) + ' 1\n' + '2\n' + 'END\n' + 'END\n'

    #--- Specify Ports
    #Assuming that polygon number one (1) is the throughline
    Port_Number = 1;
    for i in Polygons.keys():
        if ('Ports' in Polygons[i]) == True:
            for k in Polygons[i]["Ports"].keys():
                SON = SON + 'POR1 STD\n' + 'POLY ' + str(i) + ' 1\n'
                Pt = Polygons[i]["Ports"][k][0]
                SON = SON + str(int(Pt-1)) + ' \n'
                Pt1 = max( divmod((Pt+1),np.shape(Polygons[i]["Points"])[1])[0] ,1) #Usually Pt+1, but is Pt+1 > Polygons{i}.Points, then wraps to 1 instead of 0
                SON = SON + str(Port_Number) + ' ' + str(Polygons[i]["Ports"][k][1]) + ' ' + str(Polygons[i]["Ports"][k][2]) + ' ' + str(int(Polygons[i]["Ports"][k][3])) + ' ' + str(int(Polygons[i]["Ports"][k][4])) + ' ' + str(int((Polygons[i]["Points"][0][Pt-1] + Polygons[1]["Points"][0][Pt1-1])/2)) + ' ' + str(int((Polygons[1]["Points"][1][Pt-1] + Polygons[1]["Points"][1][Pt1-1])/2)) + '\n' # !!! changed from Pt to Pt-1 may be wrong
                Port_Number = Port_Number + 1

    #--- Specify Polygon Points
    SON = SON + 'NUM ' + str(Num_Polygons) + '\n'

    for i in Polygons.keys():
        SON = SON + str(Polygons[i]["Layer"]) + ' ' + str(np.shape(Polygons[i]["Points"])[1]+1) + ' -1 ' + str(Polygons[i]["Mesh"]) + ' ' + str(i) + ' 1 1 ' + str(Polygons[i]["X_Max"]) + ' ' + str(Polygons[i]["Y_Max"]) + ' 0 0 0 Y' + '\n'
        for k in xrange(np.shape(Polygons[i]["Points"])[1]):
            SON = SON + str(Polygons[i]["Points"][0][k]) + ' ' + str(Polygons[i]["Points"][1][k]) + '\n'

        SON = SON + str(Polygons[i]["Points"][0][0]) + ' ' + str(Polygons[i]["Points"][1][0]) + '\n' + 'END\n'

    #--- Closing Arguements
    SON = SON + 'END GEO\n' + 'OPT\n' + 'MAX 100\n'

    #--- Declare Parameter Sweep
    if Simulation_Type == 1:
        SON = SON + 'VARS\n' + 'Coupler_Pad_Length N UNDEF UNDEF\n' + 'END OPT\n'
        if Through_Line_CPW_Gap is not 0:
            SON = SON + 'VARSWP\n' + 'LSWEEP ' + str(Frequency_Sweep_Start) + ' ' + str(Frequency_Sweep_End) + ' 25\n' 
        else:
            SON = SON + 'VARSWP\n' + 'ABS_ENTRY ' + str(Frequency_Sweep_Start) + ' ' + str(Frequency_Sweep_End) + '\n'
        
        Sweep_End = Max_Coupler_Pad_Length
        Sweep_Start = 0
        Sweep_Step = max(round(200/Cell_Size_Y)*Cell_Size_Y,Cell_Size_Y) #closest multiple of Cell_Size_X to 200
        SON = SON + 'Coupler_Pad_Length Y ' + str(Sweep_Start) + ' ' + str(Sweep_End) + ' ' + str(Sweep_Step) + '\n' + 'END VARSWP\n'
    elif (Simulation_Type == 0) or  (Simulation_Type == 2):
        SON = SON + 'VARS\n' + 'Coupler_Offset N UNDEF UNDEF\n' +'END OPT\n'
        Sweep1_End = Coupler_Offset;
        #Sweep2_End = Max_Coupler_Offset;
        Sweep1_Start =  0;
        Sweep1_Step = max(round(400/Cell_Size_X)*Cell_Size_X,Cell_Size_X) #closest multiple of Cell_Size_X to 500

        #Sweep2_Step = round(((Sweep2_End-Sweep2_End)/4)/Cell_Size_X)*Cell_Size_X; %closest multiple of Cell_Size_X to 500
        if Through_Line_CPW_Gap is not 0:
            SON = SON + 'VARSWP\n' + 'LSWEEP '  + str(Frequency_Sweep_Start) + ' ' + str(Frequency_Sweep_End) + ' 25\n'
        else:
            SON = SON + 'VARSWP\n' + 'ABS_ENTRY ' + str(Frequency_Sweep_Start) + ' ' + str(Frequency_Sweep_End) + '\n'


        SON = SON + 'Coupler_Offset Y ' + str(Sweep1_Start) + ' ' + str(Sweep1_End) + ' ' + str(Sweep1_Step) + '\n' + 'END VARSWP\n'
        
    # --- Need a large box to use the following    
    #    if Through_Line_CPW_Gap is not 0:
    #         SON = SON + 'VARSWP\n' + 'LSWEEP ' +  num2str(Frequency_Sweep_Start) + ' ' + str(Frequency_Sweep_End) + ' 20\n'
    #    else:
    #         SON = SON + 'VARSWP\n' + 'ABS_ENTRY ' + str(Frequency_Sweep_Start) + ' ' + str(Frequency_Sweep_End) + '\n'
    #    
    #     
    #    SON = SON + 'Coupler_Offset Y ' + str(Sweep1_End) + ' ' + str(Sweep2_End) ' ' + str(Sweep2_Step) + '\n'  'END VARSWP\n');

    #--- Configure Output File
    if (Simulation_Type == 1) or (Simulation_Type == 0):
        SON = SON + 'FILEOUT\n' + 'CSV D Y $BASENAME.csv IC 15 S RI R 50\n' + 'TS D Y $BASENAME.s3p IC 15 S RI R 50\n' 
        SON = SON + 'FOLDER '+ F_N +'\n' + 'END FILEOUT\n'
    elif (Simulation_Type == 2):
        pass


    SON = SON + 'QSG\n' + 'IMPORT YES\n' + 'EXTRA_METAL NO\n' + 'UNITS YES\n' + 'ALIGN NO\n' + 'REF YES\n' + 'VIEW_RES NO\n' + 'METALS NO\n' + 'USED YES\n' + 'END QSG\n' 



    #--- Change into sonnet files directory. Make this directory if it does not exist
    #current_path = os.getcwd()
    sonnet_path = 'Sonnet_Files'+ os.sep + dt.now().strftime('%Y%m%d') + os.sep

    #F_N = sonnet_path + F_N + '.son'
    #try:
    #    os.chdir('Sonnet_Files'+ os.sep + dt.now().strftime('%Y%m%d'))
    #except:
    #    #makedirs recursively creates all intermediate-level directories 
    #    #needed to contain the leaf directory
    #    os.makedirs(sonnet_path)
    #    print('Making directory Sonnet_Files'+ os.sep+ dt.now().strftime('%Y%m%d'))
    #    os.chdir(sonnet_path)  


    try:                                           
        os.makedirs(sonnet_path)
        #makedirs recursively creates all intermediate-level directories
        #needed to contain the leaf directory
    except:
        pass
    
    
    
    Sonnet_Interface.New_Proj(sonnet_path,F_N)


    File_ID = io.open(sonnet_path + F_N + '.son', 'w')
    File_ID.write(unicode(SON))
    File_ID.close()

    Sonnet_Interface.Copy_To_Remote(sonnet_path,F_N)

    return (sonnet_path,  F_N, Simulation_Geometry, Get_Simulation_Type(Simulation_Type), Coupler_Space) 

def Get_Simulation_Geometry(*Geometry, **simid):
    """ Take either Get_Simulation_Geometry(simid = X) or
    Get_Simulation_Geometry(Through_Line_Width, Through_Line_CPW_Gap, Resonator_Width, Substrate_Gap, Substrate_Thickness,Dielectric_Constant)"""
    if Geometry is not () and len(Geometry) == 6 and simid == {}:
        Through_Line_Width, Through_Line_CPW_Gap, Resonator_Width, Substrate_Gap, Substrate_Thickness,Dielectric_Constant = Geometry
        
    elif Geometry is () and simid is not {}:
        simid = simid['simid']
        
        simulation_parameters = Mask_DB.Get_Mask_Data("SELECT  Resonators.Width, Sensors.Through_Line_Width, Sensors.Through_Line_Gap FROM Resonators, Sensors, Wafer WHERE Resonators.sensor_id = Sensors.sensor_id AND Resonators.simid = " + str(simid) + " ORDER BY Sensors.X_Length ASC", 'one')

        Resonator_Width,Through_Line_Width,Through_Line_CPW_Gap = simulation_parameters 
        simulation_parameters = Mask_DB.Get_Mask_Data("SELECT Thickness, Dielectric_Constant,Pillar_Height FROM Wafer",'one')
        Substrate_Thickness,Dielectric_Constant, Substrate_Gap = simulation_parameters

    else:
        raise RuntimeError('Cannot Generate Simulation_Geometry sting')

    return 'TLW%03dTLG%03dRW%03dSG%02dST%03dE%04d' % (Through_Line_Width, Through_Line_CPW_Gap, Resonator_Width, Substrate_Gap, Substrate_Thickness,Dielectric_Constant*100)  


def Get_Simulation_Type(Simulation_Type):

    Simulation_Type_Names = {0:"CouplerSweep",1:"AuxCouplerSweep",2:"PortCalc"}
    if isinstance(Simulation_Type,int):
        return  Simulation_Type_Names[Simulation_Type]
    elif isinstance(Simulation_Type,str):
        Simulation_Type_Names = dict([[v,k] for k,v in Simulation_Type_Names.items()])
    else:
        raise RuntimeError('Unrecognized Simulation Type')
    
    return  Simulation_Type_Names[Simulation_Type]
    
