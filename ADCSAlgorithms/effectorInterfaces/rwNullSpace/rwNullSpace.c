/*
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

*/

#include "effectorInterfaces/rwNullSpace/rwNullSpace.h"
#include "attControl/_GeneralModuleFiles/vehControlOut.h"
#include "SimCode/utilities/linearAlgebra.h"
#include "SimCode/utilities/rigidBodyKinematics.h"
#include "sensorInterfaces/IMUSensorData/imuComm.h"
#include "ADCSUtilities/ADCSAlgorithmMacros.h"
#include <string.h>
#include <math.h>

/*! This method initializes the ConfigData for the null space reaction wheel rejection.
 It creates the output message.
 @return void
 @param ConfigData The configuration data associated with RW null space model
 */
void SelfInit_rwNullSpace(rwNullSpaceConfig *ConfigData, uint64_t moduleID)
{
	double GsTranspose[3 * MAX_EFF_CNT];
	double GsInvHalf[3 * 3];
	double identMatrix[MAX_EFF_CNT*MAX_EFF_CNT];
	double GsTemp[MAX_EFF_CNT*MAX_EFF_CNT];
    /*! Begin method steps */
    /*! - Create output message for module */
    ConfigData->outputMsgID = CreateNewMessage(
        ConfigData->outputControlName, sizeof(vehEffectorOut),
        "vehEffectorOut", moduleID);

	mTranspose(ConfigData->GsMatrix, 3, ConfigData->numWheels, GsTranspose);
	mMultM(ConfigData->GsMatrix, 3, ConfigData->numWheels, GsTranspose, 
		ConfigData->numWheels, 3, GsInvHalf);
	m33Inverse(RECAST3X3 GsInvHalf, RECAST3X3 GsInvHalf);
	mMultM(GsInvHalf, 3, 3, ConfigData->GsMatrix, 3, ConfigData->numWheels,
		ConfigData->GsInverse);
	mMultM(GsTranspose, ConfigData->numWheels, 3, ConfigData->GsInverse, 3,
		ConfigData->numWheels, GsTemp);
	mSetIdentity(identMatrix, ConfigData->numWheels, ConfigData->numWheels);
	mSubtract(identMatrix, ConfigData->numWheels, ConfigData->numWheels,
		GsTemp, ConfigData->GsInverse);
	
}

/*! This method performs the second stage of initialization for the RW null space control
 interface.  It's primary function is to link the input messages that were
 created elsewhere.
 @return void
 @param ConfigData The configuration data associated with the sun safe ACS control
 */
void CrossInit_rwNullSpace(rwNullSpaceConfig *ConfigData, uint64_t moduleID)
{
    /*! - Get the control data message ID*/
    ConfigData->inputRWCmdsID = subscribeToMessage(ConfigData->inputRWCommands,
        sizeof(vehControlOut), moduleID);
	/*! - Get the RW speeds ID*/
	ConfigData->inputSpeedsID = subscribeToMessage(ConfigData->inputRWSpeeds,
		sizeof(RWSpeedData), moduleID);
    
}

/*! This method takes the input reaction wheel commands as well as the observed 
    reaction wheel speeds and balances the commands so that the overall vehicle 
	momentum is minimized.
 @return void
 @param ConfigData The configuration data associated with the null space control
 @param callTime The clock time at which the function was called (nanoseconds)
 */
void Update_rwNullSpace(rwNullSpaceConfig *ConfigData, uint64_t callTime,
    uint64_t moduleID)
{
    
    uint64_t ClockTime;
    uint32_t ReadSize;
    vehEffectorOut cntrRequest;
	RWSpeedData rwSpeeds;
	vehEffectorOut finalControl;
	double dVector[MAX_EFF_CNT];
    
    /*! Begin method steps*/
    /*! - Read the input RW commands to get the raw RW requests*/
    ReadMessage(ConfigData->inputRWCmdsID, &ClockTime, &ReadSize,
                sizeof(vehEffectorOut), (void*) &(cntrRequest));
	ReadMessage(ConfigData->inputSpeedsID, &ClockTime, &ReadSize,
		sizeof(RWSpeedData), (void*)&(rwSpeeds));
    
	memset(&finalControl, 0x0, sizeof(vehEffectorOut));
	vScale(-ConfigData->OmegaGain, rwSpeeds.wheelSpeeds,
		ConfigData->numWheels, dVector);
	mMultV(ConfigData->GsInverse, ConfigData->numWheels, ConfigData->numWheels,
		dVector, finalControl.effectorRequest);
	vAdd(finalControl.effectorRequest, ConfigData->numWheels,
		cntrRequest.effectorRequest, finalControl.effectorRequest);

	WriteMessage(ConfigData->outputMsgID, callTime, sizeof(vehEffectorOut),
		&finalControl, moduleID);

    return;
}