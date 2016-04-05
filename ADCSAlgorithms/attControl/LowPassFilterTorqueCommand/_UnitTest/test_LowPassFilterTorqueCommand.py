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
#
#   Unit Test Script
#   Module Name:        LowPassFilterTorqueCommand
#   Author:             Hanspeter Schaub
#   Creation Date:      December 9, 2015
#
import pytest
import sys, os, inspect
import matplotlib.pyplot as plt
import math
# import packages as needed e.g. 'numpy', 'ctypes, 'math' etc.

filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
splitPath = path.split('ADCSAlgorithms')
sys.path.append(splitPath[0] + '/modules')
sys.path.append(splitPath[0] + '/PythonModules')


#   Import all of the modules that we are going to call in this simulation
import MessagingAccess
import SimulationBaseClass
import sim_model
import alg_contain
import unitTestSupport                  # general support file with common unit test functions
import LowPassFilterTorqueCommand       # import the module that is to be tested
import MRP_Steering                     # import a sample module that creates the neede input message declaration



# uncomment this line is this test is to be skipped in the global unit test run, adjust message as needed
# @pytest.mark.skipif(conditionstring)
# uncomment this line if this test has an expected failure, adjust message as needed
# @pytest.mark.xfail(conditionstring)
# provide a unique test method name, starting with test_
def test_lowPassFilterControlTorque(show_plots):     # update "subModule" in this function name to reflect the module name
    [testResults, testMessage] = subModuleTestFunction(show_plots)
    assert testResults < 1, testMessage

def subModuleTestFunction(show_plots):
    #   zero all unit test result gather variables
    testFailCount = 0                       # zero unit test result counter
    testMessages = []                       # create empty array to store test log messages
    unitTaskName = "unitTask"               # arbitrary name (don't change)
    unitProcessName = "TestProcess"         # arbitrary name (don't change)

    #   Create a sim module as an empty container
    unitTestSim = SimulationBaseClass.SimBaseClass()
    unitTestSim.TotalSim.terminateSimulation()          # this is needed if multiple unit test scripts are run
                                                        # this create a fresh and consistent simulation environment for each test run

    #   Create test thread
    testProcessRate = unitTestSupport.sec2nano(0.5)         # process rate update time
    testProc = unitTestSim.CreateNewProcess(unitProcessName)
    testProc.addTask(unitTestSim.CreateNewTask(unitTaskName, testProcessRate))


    #   Construct algorithm and associated C++ container
    moduleConfig = LowPassFilterTorqueCommand.lowPassFilterTorqueCommandConfig()
    moduleWrap = alg_contain.AlgContain(moduleConfig,
                                        LowPassFilterTorqueCommand.Update_LowPassFilterTorqueCommand,
                                        LowPassFilterTorqueCommand.SelfInit_LowPassFilterTorqueCommand,
                                        LowPassFilterTorqueCommand.CrossInit_LowPassFilterTorqueCommand)
    moduleWrap.ModelTag = "LowPassFilterTorqueCommand"      # python name of test module.

    #   Add test module to runtime call list
    unitTestSim.AddModelToTask(unitTaskName, moduleWrap, moduleConfig)

    #   Initialize the test module configuration data
    moduleConfig.inputDataName  = "controlTorqueRaw"
    moduleConfig.outputDataName = "controlTorqueFiltered"
    moduleConfig.wc = 0.1*math.pi*2                 #   [rad/s] continous time critical filter frequency
    moduleConfig.h = 0.5                            #   [s]     filter time step
    moduleConfig.reset = 1                          #           flag to initialize module states on first run


    #   Create input message and size it because the regular creator of that message
    #   is not part of the test.
    inputMessageSize = 3*8                          # 3 doubles
    unitTestSim.TotalSim.CreateNewMessage(unitProcessName,
                                          moduleConfig.inputDataName,
                                          inputMessageSize,
                                          2)        # number of buffers (leave at 2 as default, don't make zero)

    inputMessageData = MRP_Steering.vehControlOut() # Create a structure for the input message
    torqueRequest = [1.0, -0.5, 0.7]                # Set up a list as a 3-vector
    SimulationBaseClass.SetCArray(torqueRequest,                        # specify message variable
                                  'double',                             # specify message variable type
                                  inputMessageData.torqueRequestBody)   # Write torque request to input message
    unitTestSim.TotalSim.WriteMessageData(moduleConfig.inputDataName,
                                          inputMessageSize,
                                          0,
                                          inputMessageData)             # write data into the simulator

    #   Setup logging on the test module output message so that we get all the writes to it
    unitTestSim.TotalSim.logThisMessage(moduleConfig.outputDataName, testProcessRate)
    #unitTestSim.AddVariableForLogging(moduleWrap.ModelTag + ".reset", testProcessRate)

    #   Need to call the self-init and cross-init methods
    unitTestSim.InitializeSimulation()

    #   Step the simulation to 3*process rate so 4 total steps including zero
    unitTestSim.ConfigureStopTime(unitTestSupport.sec2nano(1.1))    # seconds to stop simulation
    unitTestSim.ExecuteSimulation()

    #   This pulls the actual data log from the simulation run.
    #   Note that range(3) will provide [0, 1, 2]  Those are the elements you get from the vector (all of them)
    moduleOutputName = "torqueRequestBody"
    LrF = unitTestSim.pullMessageLogData(moduleConfig.outputDataName + '.' + moduleOutputName,
                                                    range(3))

    #   set the filtered output truth states
    LrFtrue = [
               [0.2734574719946391,-0.1367287359973196,0.1914202303962474],
               [0.4721359549995794,-0.2360679774997897,0.3304951684997055],
               [0.6164843223022588,-0.3082421611511294,0.4315390256115811]
               ]


    #   compare the module and truth results
    for i in range(0,len(LrFtrue)):
        if not unitTestSupport.isArrayEqual(LrF[i],LrFtrue[i],3,1e-12):
            testFailCount += 1
            testMessage.append("FAILED: " + moduleWrap.ModelTag + " Module failed " + moduleOutputName + " unit test at t=" + str(LrF[i,0]*unitTestSupport.NANO2SEC) + "sec\n")



    # If the argument provided at commandline "--show_plots" evaluates as true,
    # plot all figures
    if show_plots:
          plt.show()

    #   print out success message if no error were found
    if testFailCount == 0:
        print   "PASSED: " + moduleWrap.ModelTag


    # each test method requires a single assert method to be called
    # this check below just makes sure no sub-test failures were found
    return [testFailCount, ''.join(testMessages)]


#
# This statement below ensures that the unitTestScript can be run as a
# stand-along python script
#
if __name__ == "__main__":
    test_lowPassFilterControlTorque()