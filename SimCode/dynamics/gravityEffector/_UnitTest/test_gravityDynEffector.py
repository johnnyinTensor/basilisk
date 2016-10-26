'''
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
import sys, os, inspect
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy
import pytest
import math

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
splitPath = path.split('SimCode')
sys.path.append(splitPath[0] + '/modules')
sys.path.append(splitPath[0] + '/PythonModules')
sys.path.append(splitPath[0] + '/Utilities/pyswice/_UnitTest')

import SimulationBaseClass
import unitTestSupport  # general support file with common unit test functions
import macros
import gravityEffector
import spice_interface
import sim_model
import ctypes
import pyswice
import pyswice_ck_utilities
import stateArchitecture

# uncomment this line is this test is to be skipped in the global unit test run, adjust message as needed
# @pytest.mark.skipif(conditionstring)
# uncomment this line if this test has an expected failure, adjust message as needed
# @pytest.mark.xfail() # need to update how the RW states are defined
# provide a unique test method name, starting with test_
def gravityEffectorAllTest(show_plots):
    [testResults, testMessage] = test_sphericalHarmonics(show_plots)
    assert testResults < 1, testMessage
    [testResults, testMessage] = test_singleGravityBody(show_plots)
    assert testResults < 1, testMessage
    [testResults, testMessage] = test_multiBodyGravity(show_plots)
    assert testResults < 1, testMessage

def test_sphericalHarmonics(show_plots):
    # The __tracebackhide__ setting influences pytest showing of tracebacks:
    # the mrp_steering_tracking() function will not be shown unless the
    # --fulltrace command line option is specified.
    __tracebackhide__ = True

    testFailCount = 0  # zero unit test result counter
    testMessages = []  # create empty list to store test log messages
    
    spherHarm = gravityEffector.SphericalHarmonics()
    
    testHarm = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    
    spherHarm.cBar = gravityEffector.MultiArray(testHarm)
    
    vecCheckSuccess = True
    for i in range(len(spherHarm.cBar)):
        for j in range(len(spherHarm.cBar[i])):
            if spherHarm.cBar[i][j] != testHarm[i][j]:
                vecCheckSuccess = False

    
    if(vecCheckSuccess != True):
        testFailCount += 1
        testMessages.append("2D vector not input appropriately to spherical harmonics")

    gravityEffector.loadGravFromFile(path + '/GGM03S.txt', spherHarm, 20)
    spherHarm.initializeParameters()
    gravOut = spherHarm.computeField([[0.0], [0.0], [(6378.1363)*1.0E3]], 20, True)
    gravMag = numpy.linalg.norm(numpy.array(gravOut))
    
    if gravMag > 9.9 or gravMag < 9.7:
        testFailCount += 1
        testMessages.append("Gravity magnitude not within allowable tolerance")

    gravOutMax = spherHarm.computeField([[0.0], [0.0], [(6378.1363)*1.0E3]], 100, True)

    if gravOutMax != gravOut:
        testFailCount += 1
        testMessages.append("Gravity ceiling not enforced correctly")

    if testFailCount == 0:
        print "PASSED: " + " Spherical Harmonics"
    # return fail count and join into a single string all messages in the list
    # testMessage
    return [testFailCount, ''.join(testMessages)]

def test_singleGravityBody(show_plots):
    # The __tracebackhide__ setting influences pytest showing of tracebacks:
    # the mrp_steering_tracking() function will not be shown unless the
    # --fulltrace command line option is specified.
    __tracebackhide__ = True
    
    testFailCount = 0  # zero unit test result counter
    testMessages = []  # create empty list to store test log messages
    
    # Create a sim module as an empty container
    unitTaskName = "unitTask"  # arbitrary name (don't change)
    unitProcessName = "TestProcess"  # arbitrary name (don't change)
    DateSpice = "2015 February 10, 00:00:00.0 TDB"

    # Create a sim module as an empty container
    TotalSim = SimulationBaseClass.SimBaseClass()
    TotalSim.TotalSim.terminateSimulation()

    DynUnitTestProc = TotalSim.CreateNewProcess(unitProcessName)
    # create the dynamics task and specify the integration update time
    DynUnitTestProc.addTask(TotalSim.CreateNewTask(unitTaskName, macros.sec2nano(0.1)))

    # Initialize the modules that we are using.
    SpiceObject = spice_interface.SpiceInterface()

    SpiceObject.ModelTag = "SpiceInterfaceData"
    SpiceObject.SPICEDataPath = splitPath[0] + '/External/EphemerisData/'
    SpiceObject.OutputBufferCount = 10000
    SpiceObject.PlanetNames = spice_interface.StringVector(["earth", "mars barycenter", "sun"])
    SpiceObject.UTCCalInit = DateSpice
    TotalSim.AddModelToTask(unitTaskName, SpiceObject)
    SpiceObject.UTCCalInit = "1994 JAN 26 00:02:00.184"
    

    earthGravBody = gravityEffector.GravBodyData()
    earthGravBody.bodyMsgName = "earth_planet_data"
    earthGravBody.outputMsgName = "earth_display_frame_data"
    earthGravBody.isCentralBody = False
    earthGravBody.useSphericalHarmParams = True
    gravityEffector.loadGravFromFile(path + '/GGM03S.txt', earthGravBody.spherHarm, 60)
    
    pyswice.furnsh_c(splitPath[0] + '/External/EphemerisData/de430.bsp')
    pyswice.furnsh_c(splitPath[0] + '/External/EphemerisData/naif0011.tls')
    pyswice.furnsh_c(splitPath[0] + '/External/EphemerisData/de-403-masses.tpc')
    pyswice.furnsh_c(splitPath[0] + '/External/EphemerisData/pck00010.tpc')
    pyswice.furnsh_c(path + '/hst_edited.bsp')
    
    SpiceObject.UTCCalInit = "2012 MAY 1 00:02:00.184"
    stringCurrent = SpiceObject.UTCCalInit
    et = pyswice.new_doubleArray(1)
    dt = 1.0
    pyswice.str2et_c(stringCurrent, et)
    etCurr = pyswice.doubleArray_getitem(et, 0)
    normVec = []
    gravErrNorm = []
    SpiceObject.UTCCalInit = stringCurrent
    TotalSim.InitializeSimulation()
    earthGravBody.initBody(0)
    SpiceObject.UpdateState(0)
    for i in range(2*3600):
        stateOut = pyswice_ck_utilities.spkRead('HUBBLE SPACE TELESCOPE', stringCurrent, 'J2000', 'EARTH')
        etPrev =etCurr - 2.0
        stringPrev = pyswice.et2utc_c(etPrev, 'C', 4, 1024, "Yo")
        statePrev = pyswice_ck_utilities.spkRead('HUBBLE SPACE TELESCOPE', stringPrev, 'J2000', 'EARTH')
        etNext =etCurr + 2.0
        stringNext = pyswice.et2utc_c(etNext, 'C', 4, 1024, "Yo")
        stateNext = pyswice_ck_utilities.spkRead('HUBBLE SPACE TELESCOPE', stringNext, 'J2000', 'EARTH')
        gravVec = (stateNext[3:6] - statePrev[3:6])/(etNext - etPrev)
        normVec.append(numpy.linalg.norm(stateOut[0:3]))
        
        stateOut*=1000.0
        SpiceObject.J2000Current = etCurr;SpiceObject.UpdateState(0)
        earthGravBody.loadEphemeris(0)
        gravOut = earthGravBody.computeGravityInertial(stateOut[0:3].reshape(3,1).tolist(), 0)
 
        gravErrNorm.append(numpy.linalg.norm(gravVec*1000.0 - numpy.array(gravOut).reshape(3))/
            numpy.linalg.norm(gravVec*1000.0))
        
        pyswice.str2et_c(stringCurrent, et)
        etCurr = pyswice.doubleArray_getitem(et, 0)
        etCurr += dt;
        stringCurrent = pyswice.et2utc_c(etCurr, 'C', 4, 1024, "Yo")
    

    
    for gravErr in gravErrNorm:
        if gravErr > 1.0e-4:
            testFailCount += 1
            testMessages.append("Gravity numerical error too high for kernel comparison")
            break
    
    pyswice.unload_c(splitPath[0] + '/External/EphemerisData/de430.bsp')
    pyswice.unload_c(splitPath[0] + '/External/EphemerisData/naif0011.tls')
    pyswice.unload_c(splitPath[0] + '/External/EphemerisData/de-403-masses.tpc')
    pyswice.unload_c(splitPath[0] + '/External/EphemerisData/pck00010.tpc')
    pyswice.unload_c(path + '/hst_edited.bsp')

    if testFailCount == 0:
        print "PASSED: " + " Single body with spherical harmonics"
    # return fail count and join into a single string all messages in the list
    # testMessage
    
    return [testFailCount, ''.join(testMessages)]

def test_multiBodyGravity(show_plots):
    # The __tracebackhide__ setting influences pytest showing of tracebacks:
    # the mrp_steering_tracking() function will not be shown unless the
    # --fulltrace command line option is specified.
    __tracebackhide__ = True
    
    testFailCount = 0  # zero unit test result counter
    testMessages = []  # create empty list to store test log messages
    
    # Create a sim module as an empty container
    unitTaskName = "unitTask"  # arbitrary name (don't change)
    unitProcessName = "TestProcess"  # arbitrary name (don't change)
    DateSpice = "2015 February 10, 00:00:00.0 TDB"

    # Create a sim module as an empty container
    TotalSim = SimulationBaseClass.SimBaseClass()
    TotalSim.TotalSim.terminateSimulation()

    DynUnitTestProc = TotalSim.CreateNewProcess(unitProcessName)
    # create the dynamics task and specify the integration update time
    DynUnitTestProc.addTask(TotalSim.CreateNewTask(unitTaskName, macros.sec2nano(1000.0)))

    # Initialize the modules that we are using.
    SpiceObject = spice_interface.SpiceInterface()

    SpiceObject.ModelTag = "SpiceInterfaceData"
    SpiceObject.SPICEDataPath = splitPath[0] + '/External/EphemerisData/'
    SpiceObject.OutputBufferCount = 10000
    SpiceObject.PlanetNames = spice_interface.StringVector(["earth", "mars barycenter", "sun"])
    SpiceObject.UTCCalInit = DateSpice
    TotalSim.AddModelToTask(unitTaskName, SpiceObject)
    SpiceObject.UTCCalInit = "1994 JAN 26 00:02:00.184"

    TotalSim.earthGravBody = gravityEffector.GravBodyData()
    TotalSim.earthGravBody.bodyMsgName = "earth_planet_data"
    TotalSim.earthGravBody.outputMsgName = "earth_display_frame_data"
    TotalSim.earthGravBody.isCentralBody = False
    TotalSim.earthGravBody.useSphericalHarmParams = True
    gravityEffector.loadGravFromFile(path + '/GGM03S.txt', TotalSim.earthGravBody.spherHarm, 60)
    
    TotalSim.marsGravBody = gravityEffector.GravBodyData()
    TotalSim.marsGravBody.bodyMsgName = "mars barycenter_planet_data"
    TotalSim.marsGravBody.outputMsgName = "mars_display_frame_data"
    TotalSim.marsGravBody.mu = 4.305e4*1000*1000*1000 # meters!
    TotalSim.marsGravBody.isCentralBody = False
    TotalSim.marsGravBody.useSphericalHarmParams = False
    
    TotalSim.jupiterGravBody = gravityEffector.GravBodyData()
    TotalSim.jupiterGravBody.bodyMsgName = "jupiter barycenter_planet_data"
    TotalSim.jupiterGravBody.outputMsgName = "jupiter_display_frame_data"
    TotalSim.jupiterGravBody.mu = 4.305e4*1000*1000*1000 # meters!
    TotalSim.jupiterGravBody.isCentralBody = False
    TotalSim.jupiterGravBody.useSphericalHarmParams = False
    
    TotalSim.sunGravBody = gravityEffector.GravBodyData()
    TotalSim.sunGravBody.bodyMsgName = "sun_planet_data"
    TotalSim.sunGravBody.outputMsgName = "sun_display_frame_data"
    TotalSim.sunGravBody.mu = 1.32712440018E20  # meters!
    TotalSim.sunGravBody.isCentralBody = True
    TotalSim.sunGravBody.useSphericalHarmParams = False
    
    TotalSim.newManager = stateArchitecture.DynParamManager()
    positionName = "hubPosition"
    stateDim = [3, 1]
    posState = TotalSim.newManager.registerState(stateDim[0], stateDim[1], positionName)
    TotalSim.newManager.createProperty("systemTime", [[0], [0.0]])
    
    allGrav = gravityEffector.GravityEffector()
    allGrav.gravBodies = gravityEffector.GravBodyVector([TotalSim.earthGravBody, TotalSim.sunGravBody, TotalSim.marsGravBody, TotalSim.jupiterGravBody])
    allGrav.linkInStates(TotalSim.newManager)
    allGrav.registerProperties(TotalSim.newManager)
    TotalSim.AddModelToTask(unitTaskName, allGrav)
    
    
    pyswice.furnsh_c(splitPath[0] + '/External/EphemerisData/de430.bsp')
    pyswice.furnsh_c(splitPath[0] + '/External/EphemerisData/naif0011.tls')
    pyswice.furnsh_c(splitPath[0] + '/External/EphemerisData/de-403-masses.tpc')
    pyswice.furnsh_c(splitPath[0] + '/External/EphemerisData/pck00010.tpc')
    pyswice.furnsh_c(path + '/dawn_rec_081022_081109_090218_v1.bsp')
    
    SpiceObject.UTCCalInit = "2008-10-24T00:00:00"
    stringCurrent = SpiceObject.UTCCalInit
    TotalSim.InitializeSimulation()
    dtVal = 1000.0
    gravErrVec = []
    for i in range(1300):
        stateOut = pyswice_ck_utilities.spkRead('DAWN', stringCurrent, 'J2000', 'SUN')*1000.0
        posState.setState(stateOut[0:3].reshape(3,1).tolist())
        TotalSim.newManager.setPropertyValue("systemTime", [[i*1000*1e9], [i*1000.0]])
        TotalSim.ConfigureStopTime(macros.sec2nano(i*1000.0)+10)
        TotalSim.ExecuteSimulation()
        allGrav.computeGravityField()
        etPrev =SpiceObject.J2000Current - 2.0
        stringPrev = pyswice.et2utc_c(etPrev, 'C', 4, 1024, "Yo")
        statePrev = pyswice_ck_utilities.spkRead('DAWN', stringPrev, 'J2000', 'SUN')*1000.0
        etNext =SpiceObject.J2000Current + 2.0
        stringNext = pyswice.et2utc_c(etNext, 'C', 4, 1024, "Yo")
        stateNext = pyswice_ck_utilities.spkRead('DAWN', stringNext, 'J2000', 'SUN')*1000.0
        gravVec = (stateNext[3:6] - statePrev[3:6])/(etNext - etPrev)
        gravErrVec.append(numpy.linalg.norm(gravVec.reshape(3,1) - numpy.array(TotalSim.newManager.getPropertyReference("g_N"))))
    
    for gravMeas in gravErrVec:
        if gravMeas > 5.0e-4:
            print gravMeas
            testFailCount += 1
            testMessages.append("Gravity multi-body error too high for kernel comparison")
            break

    
    if testFailCount == 0:
        print "PASSED: " + " Multi gravitational bodies"
    # return fail count and join into a single string all messages in the list
    # testMessage
    
    return [testFailCount, ''.join(testMessages)]

if __name__ == "__main__":
    gravityEffectorAllTest(False)
    