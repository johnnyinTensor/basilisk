﻿'''
Copyright (c) 2016, Autonomous Vehicle Systems Lab, Univeristy of Colorado at Boulder

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

'''
#Very simple simulation.  Just sets up and calls the SPICE interface.  Could
#be the basis for a unit test of SPICE
import sys, os, inspect
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy
import ctypes
import math
import csv
import logging
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
splitPath = path.split('SimCode')
sys.path.append(splitPath[0] + '/modules')
sys.path.append(splitPath[0] + '/PythonModules')

#Import all of the modules that we are going to call in this simulation
import spice_interface
import six_dof_eom
import MessagingAccess
import SimulationBaseClass
import sim_model

TestResults = {}

def LoadGravFromFile(FileName, GravBody, JParamsSelect):
   csvfile = open(FileName, 'rb')
   csvreader = csv.reader(csvfile)
   FirstLine = True
   NextJindex = 0
   AllJParams = []
   for row in csvreader:
      if(FirstLine == True):
         GravBody.mu = float(row[1])
         GravBody.radEquator = float(row[0])
         FirstLine = False
      elif(int(row[0]) == JParamsSelect[NextJindex]):
         LocalJParam = -math.sqrt(2*JParamsSelect[NextJindex]+1)*float(row[2])
         AllJParams.append(LocalJParam)
         NextJindex += 1
         if(NextJindex >= len(JParamsSelect)):
            break
   return(AllJParams)

#Define success criteria
propTime = int(3600*24*10*1E9) #Propagate for 10 days worth of nanoseconds
allowPosError = 50000 #Allow for a 50 km error over 10 days of propagation
allowVelError = 0.1 #Allow for the velocity to degrade by 10 cm/s

#Create a sim module as an empty container
TotalSim = SimulationBaseClass.SimBaseClass()
DynUnitTestProc = TotalSim.CreateNewProcess("DynUnitTestProcess")
DynUnitTestProc.addTask(TotalSim.CreateNewTask("sixDynTestTask", int(1E10)))
DynUnitTestProc.addTask(TotalSim.CreateNewTask("sixDynTestTaskMarsTime", int(5E9)), 1)
DynUnitTestProc.addTask(TotalSim.CreateNewTask("sixDynTestTaskMars", int(5E9)), 0)
TotalSim.disableTask("sixDynTestTaskMars");
TotalSim.disableTask("sixDynTestTaskMarsTime");

#Now initialize the modules that we are using.  I got a little better as I went along
VehDynObject = six_dof_eom.SixDofEOM()
spiceObject = spice_interface.SpiceInterface()

#Initialize the ephemeris module
spiceObject.ModelTag = "SpiceInterfaceData"
spiceObject.SPICEDataPath = splitPath[0] + '/External/EphemerisData/'
spiceObject.UTCCalInit = "2014 March 23, 14:00:00.0"
spiceObject.OutputBufferCount = 2
spiceObject.PlanetNames = spice_interface.StringVector(
    ["earth", "mars", "jupiter barycenter", "sun","maven"])
spiceObject.loadSpiceKernel('maven_cru_rec_131118_140923_v1.bsp', path + '/')
#spiceObject.loadSpiceKernel('jup260.bsp', path + '/')
spiceObject.zeroBase = "sun"

JParamsSelect = [2, 3, 4, 5, 6]
EarthGravFile = splitPath[0] + '/External/LocalGravData/GGM03S.txt'
MarsGravFile = splitPath[0] +'/External/LocalGravData/GGM2BData.txt'

SunGravBody = six_dof_eom.GravityBodyData()
SunGravBody.BodyMsgName = "sun_planet_data"
SunGravBody.outputMsgName = "sun_display_frame_data"
SunGravBody.mu = 1.32712440018E20 #meters!
SunGravBody.IsCentralBody = True
SunGravBody.IsDisplayBody = False
SunGravBody.UseJParams = True

mu_earth = 0.3986004415E+15 # [m^3/s^2]
reference_radius_earth = 0.6378136300E+07 # [m]
max_degree_earth = 10
EarthGravBody = six_dof_eom.GravityBodyData(EarthGravFile, max_degree_earth, mu_earth, reference_radius_earth)
EarthGravBody.BodyMsgName = "earth_planet_data"
EarthGravBody.outputMsgName = "earth_display_frame_data"
EarthGravBody.IsCentralBody = False
JParams = LoadGravFromFile(EarthGravFile,  EarthGravBody, JParamsSelect)
EarthGravBody.JParams = six_dof_eom.DoubleVector(JParams)   


mu_mars= 4.2828371901284001E+13 # [m^3/s^2]
reference_radius_mars = 3.3970000000000000E+06 # [m]
max_degree_mars = 30
MarsGravBody = six_dof_eom.GravityBodyData(MarsGravFile, max_degree_mars, mu_mars, reference_radius_mars)
#MarsGravBody.mu = mu_mars
MarsGravBody.BodyMsgName = "mars_planet_data"
MarsGravBody.IsCentralBody = False
JParams = LoadGravFromFile(MarsGravFile,  MarsGravBody, JParamsSelect)
MarsGravBody.JParams = six_dof_eom.DoubleVector(JParams)
MarsGravBody.UseSphericalHarmParams = False
MarsGravBody.UseJParams = False

JupiterGravBody = six_dof_eom.GravityBodyData()
JupiterGravBody.BodyMsgName = "jupiter barycenter_planet_data"
JupiterGravBody.outputMsgName = "jupiter barycenter_display_frame_data"
JupiterGravBody.mu = 1.266865349093058E17 #meters!
JupiterGravBody.IsCentralBody = False
JupiterGravBody.IsDisplayBody = False
JupiterGravBody.UseJParams = False

#MoonGravBody = six_dof_eom.GravityBodyData()
#MoonGravBody.BodyMsgName = "moon_planet_data"
#MoonGravBody.mu = 4902.799*1000*1000*1000 #meters!
#MoonGravBody.IsCentralBody = False
#MoonGravBody.IsDisplayBody = False
#MoonGravBody.UseJParams = False

#VenusGravBody = six_dof_eom.GravityBodyData()
#VenusGravBody.BodyMsgName = "venus_planet_data"
#VenusGravBody.mu = 3.257E14 #meters!
#VenusGravBody.IsCentralBody = False
#VenusGravBody.IsDisplayBody = False
#VenusGravBody.UseJParams = False

VehDynObject.ModelTag = "VehicleDynamicsData"
VehDynObject.PositionInit = six_dof_eom.DoubleVector([-1.784938418967935e+11, -1.609707049168820e+10, -1.627664958116536e+09])
VehDynObject.VelocityInit = six_dof_eom.DoubleVector([-3.120111634914843e+03, -2.471539811502987e+04, -1.119615706657671e+04])
#Note that the above position/velocity get overwritten by the ICs from the target ephemeris
VehDynObject.AttitudeInit = six_dof_eom.DoubleVector([0.4, 0.2, 0.1])
VehDynObject.AttRateInit = six_dof_eom.DoubleVector([0.0001, 0.0, 0.0])
VehDynObject.baseMass = 1500.0 - 812.3
VehDynObject.baseInertiaInit = six_dof_eom.DoubleVector([900, 0.0, 0.0,
                                                         0.0, 900.0, 0.0,
                                                         0.0, 0.0, 900.0])
VehDynObject.T_Str2BdyInit = six_dof_eom.DoubleVector([1.0, 0.0, 0.0,
                                                           0.0, 1.0, 0.0,
                                                           0.0, 0.0, 1.0])
VehDynObject.baseCoMInit = six_dof_eom.DoubleVector([0.0, 0.0, 1.0])
#Add the three gravity bodies in to the simulation
VehDynObject.AddGravityBody(SunGravBody)
VehDynObject.AddGravityBody(EarthGravBody)
#VehDynObject.AddGravityBody(MoonGravBody)
#VehDynObject.AddGravityBody(VenusGravBody)
VehDynObject.AddGravityBody(MarsGravBody)
VehDynObject.AddGravityBody(JupiterGravBody)
VehDynObject.useTranslation = True
VehDynObject.useRotation = True

TotalSim.AddModelToTask("sixDynTestTask", spiceObject)
TotalSim.AddModelToTask("sixDynTestTask", VehDynObject)
TotalSim.AddModelToTask("sixDynTestTaskMarsTime", spiceObject)
TotalSim.AddModelToTask("sixDynTestTaskMars", VehDynObject)

TotalSim.TotalSim.logThisMessage("maven_planet_data", int(1E12))
TotalSim.TotalSim.logThisMessage("mars_planet_data", int(1E12))
TotalSim.TotalSim.logThisMessage("jupiter barycenter_planet_data", int(1E12))
TotalSim.TotalSim.logThisMessage("inertial_state_output", int(1E12))

#TotalSim.InitializeSimulation()
#TotalSim.ConfigureStopTime(60*1e9) #Just a simple run to get initial conditions from ephem
#TotalSim.ExecuteSimulation()
#
#mavenPos = TotalSim.pullMessageLogData("maven_planet_data.PositionVector",
#                                       range(3))
#sunPos = TotalSim.pullMessageLogData("sun_planet_data.PositionVector",
#                                         range(3))
#mavenVel = TotalSim.pullMessageLogData("maven_planet_data.VelocityVector",
#                                           range(3))
#sunVel = TotalSim.pullMessageLogData("sun_planet_data.VelocityVector",
#                                         range(3))
#posInit = mavenPos[0, 1:] - sunPos[0, 1:]
#velInit = mavenVel[0, 1:] - sunVel[0, 1:]
##Re-init the vehicle position/velocity to the MAVEN ephemeris data
#VehDynObject.PositionInit = six_dof_eom.DoubleVector(numpy.ndarray.tolist(posInit))
#VehDynObject.VelocityInit = six_dof_eom.DoubleVector(numpy.ndarray.tolist(velInit))
#
#TotalSim.InitializeSimulation()
#TotalSim.ConfigureStopTime(propTime)
#TotalSim.ExecuteSimulation()
#
#
#mavenPos = TotalSim.pullMessageLogData("maven_planet_data.PositionVector",
#    range(3))
#marsPos = TotalSim.pullMessageLogData("mars_planet_data.PositionVector",
#                                       range(3))
#sunPos = TotalSim.pullMessageLogData("sun_planet_data.PositionVector",
#                                          range(3))
#mavenVel = TotalSim.pullMessageLogData("maven_planet_data.VelocityVector",
#                                           range(3))
#marsVel = TotalSim.pullMessageLogData("mars_planet_data.VelocityVector",
#                                      range(3))
#sunVel = TotalSim.pullMessageLogData("sun_planet_data.VelocityVector",
#                                     range(3))
#jupiterPos = TotalSim.pullMessageLogData("jupiter_planet_data.PositionVector",
#                                     range(3))
#
#vehiclePosition = TotalSim.pullMessageLogData("inertial_state_output.r_N", range(3))
#vehicleVelocity = TotalSim.pullMessageLogData("inertial_state_output.v_N", range(3))
#
#finalPosError = mavenPos[-1, :] - vehiclePosition[-1, :]
#finalVelError = mavenVel[-1,:] - vehicleVelocity[-1,:]
#print vehiclePosition[-1,:]
#print mavenPos[-1, :]
#print sunPos[2,:]
#print finalPosError
#spiceObject.PlanetNames = spice_interface.StringVector(
#                                                       ["earth", "mars", "jupiter", "sun", "moon", "venus", "new horizons"])
#spiceObject.loadSpiceKernel('nh_pred_od077.bsp', path + '/')
#spiceObject.UTCCalInit = "2008 September 19, 04:00:00.0"
#
#TotalSim.TotalSim.logThisMessage("new horizons_planet_data", int(1E12))
#TotalSim.InitializeSimulation()
#TotalSim.ConfigureStopTime(60*1e9) #Just a simple run to get initial conditions from ephem
#TotalSim.ExecuteSimulation()
#
#newHorPos = TotalSim.pullMessageLogData("new horizons_planet_data.PositionVector",
#                                       range(3))
#sunPos = TotalSim.pullMessageLogData("sun_planet_data.PositionVector",
#                                     range(3))
#newHorVel = TotalSim.pullMessageLogData("new horizons_planet_data.VelocityVector",
#                                       range(3))
#sunVel = TotalSim.pullMessageLogData("sun_planet_data.VelocityVector",
#                                     range(3))
#posInit = newHorPos[0, 1:] - sunPos[0, 1:]
#velInit = newHorVel[0, 1:] - sunVel[0, 1:]
##Re-init the vehicle position/velocity to the MAVEN ephemeris data
#VehDynObject.PositionInit = six_dof_eom.DoubleVector(numpy.ndarray.tolist(posInit))
#VehDynObject.VelocityInit = six_dof_eom.DoubleVector(numpy.ndarray.tolist(velInit))
#
#TotalSim.InitializeSimulation()
#TotalSim.ConfigureStopTime(propTime)
#TotalSim.ExecuteSimulation()
#
#newHorPos = TotalSim.pullMessageLogData("new horizons_planet_data.PositionVector",
#                                       range(3))
#vehiclePosition = TotalSim.pullMessageLogData("inertial_state_output.r_N", range(3))
#newHorVel = TotalSim.pullMessageLogData("new horizons_planet_data.VelocityVector",
#                                        range(3))
#vehicleVelocity = TotalSim.pullMessageLogData("inertial_state_output.v_N", range(3))
#finalPosError = newHorPos[-1, :] - vehiclePosition[-1, :]
#finalVelError = newHorVel[-1,:] - vehicleVelocity[-1,:]
#initVelError = newHorVel[0,:] - vehicleVelocity[0,:]
#initPosError = newHorPos[0,:] - vehiclePosition[0,:]
#velocityDiff = newHorVel - vehicleVelocity
#print finalPosError
#print finalVelError
#print initPosError
#print vehiclePosition.shape

VehDynObject.GravData[0].IsCentralBody = False
VehDynObject.GravData[0].IsDisplayBody = False
VehDynObject.GravData[2].IsDisplayBody = True
VehDynObject.GravData[2].IsCentralBody = True
spiceObject.loadSpiceKernel('m01_ext42.bsp', path + '/')
spiceObject.UTCCalInit = "2015 January 19, 02:00:00.0"

spiceObject.PlanetNames = spice_interface.StringVector(
                                                       ["earth", "mars", "jupiter barycenter", "sun", "mars odyssey"])

TotalSim.disableTask("sixDynTestTask")
TotalSim.enableTask("sixDynTestTaskMarsTime")
TotalSim.enableTask("sixDynTestTaskMars")

#TotalSim.InitializeSimulation()
TotalSim.TotalSim.logThisMessage("maven_planet_data", int(1E10))
TotalSim.TotalSim.logThisMessage("mars_planet_data", int(1E10))
TotalSim.TotalSim.logThisMessage("jupiter barycenter_planet_data", int(1E10))
TotalSim.TotalSim.logThisMessage("inertial_state_output", int(1E10))
TotalSim.TotalSim.logThisMessage("mars odyssey_planet_data", int(1E10))
TotalSim.InitializeSimulation()
TotalSim.ConfigureStopTime(60*1e9) #Just a simple run to get initial conditions from ephem
TotalSim.ExecuteSimulation()

mavenPos = TotalSim.pullMessageLogData("mars odyssey_planet_data.PositionVector",
                                        range(3))
marsPos = TotalSim.pullMessageLogData("mars_planet_data.PositionVector",
                                     range(3))
mavenVel = TotalSim.pullMessageLogData("mars odyssey_planet_data.VelocityVector",
                                        range(3))
marsVel = TotalSim.pullMessageLogData("mars_planet_data.VelocityVector",
                                     range(3))

posInit = mavenPos[0, 1:] - marsPos[0, 1:]
velInit = mavenVel[0, 1:] - marsVel[0, 1:]

#Re-init the vehicle position/velocity to the MAVEN ephemeris data
VehDynObject.PositionInit = six_dof_eom.DoubleVector(numpy.ndarray.tolist(posInit))
VehDynObject.VelocityInit = six_dof_eom.DoubleVector(numpy.ndarray.tolist(velInit))

modysseyPropTime = int((86400*7)*1E9)
spiceObject.zeroBase = "mars"

VehDynObject.GravData[2].UseSphericalHarmParams = False
VehDynObject.GravData[2].UseJParams = False
TotalSim.InitializeSimulation()
TotalSim.ConfigureStopTime(modysseyPropTime)
TotalSim.ExecuteSimulation()

print "Case 1 complete"

mavenPos = TotalSim.pullMessageLogData("mars odyssey_planet_data.PositionVector",
                                       range(3))
mavenVel = TotalSim.pullMessageLogData("mars odyssey_planet_data.VelocityVector",
                                       range(3))

vehiclePosition = TotalSim.pullMessageLogData("inertial_state_output.r_N", range(3))
vehicleVelocity = TotalSim.pullMessageLogData("inertial_state_output.v_N", range(3))

velocityDiffsph = mavenVel - vehicleVelocity
positionDiffsph = mavenPos - vehiclePosition

VehDynObject.GravData[2].UseSphericalHarmParams = False
VehDynObject.GravData[2].UseJParams = True
TotalSim.InitializeSimulation()
TotalSim.ConfigureStopTime(modysseyPropTime)
TotalSim.ExecuteSimulation()

print "Case 2 complete"

vehiclePosition = TotalSim.pullMessageLogData("inertial_state_output.r_N", range(3))
vehicleVelocity = TotalSim.pullMessageLogData("inertial_state_output.v_N", range(3))

velocityDiffjPar = mavenVel - vehicleVelocity
positionDiffjPar = mavenPos - vehiclePosition

VehDynObject.GravData[2].UseSphericalHarmParams = True
VehDynObject.GravData[2].UseJParams = False
TotalSim.InitializeSimulation()
TotalSim.ConfigureStopTime(modysseyPropTime)
TotalSim.ExecuteSimulation()

vehiclePosition = TotalSim.pullMessageLogData("inertial_state_output.r_N", range(3))
vehicleVelocity = TotalSim.pullMessageLogData("inertial_state_output.v_N", range(3))

velocityDiffsHar = mavenVel - vehicleVelocity
positionDiffsHar = mavenPos - vehiclePosition

plt.figure()
plt.subplot(3,1,1)
plt.plot(vehiclePosition[:,0]*1.0E-9, positionDiffsph[:,1])
plt.plot(vehiclePosition[:,0]*1.0E-9, positionDiffjPar[:,1])
plt.plot(vehiclePosition[:,0]*1.0E-9, positionDiffsHar[:,1])
plt.subplot(3,1,2)
plt.plot(vehiclePosition[:,0]*1.0E-9, positionDiffsph[:,2])
plt.plot(vehiclePosition[:,0]*1.0E-9, positionDiffjPar[:,2])
plt.plot(vehiclePosition[:,0]*1.0E-9, positionDiffsHar[:,2])
plt.subplot(3,1,3)
plt.plot(vehiclePosition[:,0]*1.0E-9, positionDiffsph[:,3])
plt.plot(vehiclePosition[:,0]*1.0E-9, positionDiffjPar[:,3])
plt.plot(vehiclePosition[:,0]*1.0E-9, positionDiffsHar[:,3])

plt.figure()
plt.subplot(3,1,1)
plt.plot(vehiclePosition[:,0]*1.0E-9, velocityDiffsph[:,1])
plt.plot(vehiclePosition[:,0]*1.0E-9, velocityDiffjPar[:,1])
plt.plot(vehiclePosition[:,0]*1.0E-9, velocityDiffsHar[:,1])
plt.subplot(3,1,2)
plt.plot(vehiclePosition[:,0]*1.0E-9, velocityDiffsph[:,2])
plt.plot(vehiclePosition[:,0]*1.0E-9, velocityDiffjPar[:,2])
plt.plot(vehiclePosition[:,0]*1.0E-9, velocityDiffsHar[:,2])
plt.subplot(3,1,3)
plt.plot(vehiclePosition[:,0]*1.0E-9, velocityDiffsph[:,3])
plt.plot(vehiclePosition[:,0]*1.0E-9, velocityDiffjPar[:,3])
plt.plot(vehiclePosition[:,0]*1.0E-9, velocityDiffsHar[:,3])

plt.show()