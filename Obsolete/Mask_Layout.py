import os
import Draw_Resonator
reload(Draw_Resonator)
import gdspy

## Start a path from the origin with width 1.
Resonator_Width = 20.#170. #34.
Vacuum_Gap = 3.
Resonator_Length = 100000.  #300000.
Meander_Pitch =  800.#Vacuum_Gap*5
Meander_Zone = 20000.
Resonator_Trace_Layer = 1
Pillar_Layer = 2
Pillar_Diameter = 20.
Pillar_Spacing = 400. # 600.
Pillar_Clearance = Vacuum_Gap*5
Aux_Coupler_Length = 1000.0 
Through_Line_Width = 360 
Coupler_Length = 1000.0 

Geometry_Tuple = (Resonator_Width,Resonator_Length,Aux_Coupler_Length,Coupler_Length,Meander_Pitch,Meander_Zone,Pillar_Diameter,Pillar_Spacing,Pillar_Clearance,Through_Line_Width )
##Clear cell_dict to avoid naming conflict
gdspy.Cell.cell_dict = {}

Res_Name = 'My_Resonator'
#resonator_cell 

#to use the geometry from Geometry_Tuple
#Res_Tuple,_y_initial= Draw_Resonator.Draw_Resonator(Res_Name,1,1,2,True, True,False,Geometry_Tuple)

#to use the geometry from Resonator_ID = 1 in Mask_DB.. 
#Res_Tuple= Draw_Resonator(Resonator_Name=Res_Name,Resonator_ID=1, Resonator_Trace_Layer = 1, Pillar_Layer = 2, Y_Pitch_Tight = False, X_Pitch_Tight = False,Update_DB = True)
#use Res 9 for pad over lap and Res16 for piller intersecting bend
Res_Tuple,_y_initial = Draw_Resonator.Draw_Resonator(Res_Name,16, Resonator_Trace_Layer = 1, Pillar_Layer = 2, Y_Pitch_Tight = True, X_Pitch_Tight = True,Update_DB = False)

my_res_cell = gdspy.Cell('My_Resonator')
my_res_cell.add(gdspy.CellReference(Res_Tuple))


name = os.path.abspath(os.path.dirname(os.sys.argv[0])) + os.sep + 'single_resonator'

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
gdsii = gdspy.GdsImport(name + '.gds',
                        rename={Res_Name:'IMPORT_RESONATOR'},
                        layers={Resonator_Trace_Layer:3})

## Now we extract the cells we want to actually include in our current
## structure. Note that the referenced cells will be automatically
## extracted as well.
#gdsii.extract('IMPORT_REFS')
    
## View the layout using a GUI.  Full description of the controls can
## be found in the online help at http://gdspy.sourceforge.net/
gdspy.LayoutViewer(colors=[None] * 64)