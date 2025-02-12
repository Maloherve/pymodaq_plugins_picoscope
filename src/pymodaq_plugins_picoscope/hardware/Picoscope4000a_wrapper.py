# -*- coding: utf-8 -*-
"""
Created on Mon Feb 3 2025

@author: dqml-lab
"""
import ctypes
import numpy as np
from picosdk.ps4000a import ps4000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc
from math import *


class Picoscope_Wrapper:

    ############## My methods

    def __init__(self, aquire_time=.5, sampling_freq=0.20, trigger=500, trigger_chan=1) -> None:
        """
        Max Sampling Freq = 80 MHz
        """

        self.aquire_time = aquire_time
        self.num_points = sampling_freq*1e6 *aquire_time 
        self.sampling_frequency = sampling_freq
    
        self.preTriggerSamples = 100
        self.postTriggerSamples = int( self.num_points - self.preTriggerSamples)
        self.trigger_chan_number = trigger_chan

        self.maxSamples = int(self.preTriggerSamples + self.postTriggerSamples)
        self.timebase = int( 80/sampling_freq - 1 )  # Page 24 of PG

        self.chandle = ctypes.c_int16()
        self.status = {}
        self.maxADC = ctypes.c_int16(32767)

        self.timeIntervalns = None

        self.trigger_threshold = trigger  # mV
        self.bufferA = None
        self.bufferB = None
        self.chARange = None
        self.chBRange = None
        
        print()
        print("----- Setting up Picoscope with parameters : ")
        print("Aquire Time = ", aquire_time, "s")
        print("Sampling Frequency = ", 80 / (self.timebase+1), "MHz,  Step size = ", (self.timebase+1)*12.5, " ns" )
        print("Total Points = ", self.maxSamples)
        print("Timebase = ", self.timebase)
        print("----------")
        print()

        self.initialize_picoscope()


    def __del__(self):
        print("Stopping Picoscope")
        
        # Stop the scope
        handle = self.chandle
        self.status["stop"] = ps.ps4000aStop(handle)
        assert_pico_ok(self.status["stop"])

        # Close unit / Disconnect the scope
        handle = self.chandle
        self.status["close"] = ps.ps4000aCloseUnit(handle)
        assert_pico_ok(self.status["close"])


    def initialize_picoscope(self):

        # ----------
        # Initialise Device
        # ----------

        # Open 4000 series PicoScope
        # Returns handle to chandle for use in future API functions
        self.status["openunit"] = ps.ps4000aOpenUnit(ctypes.byref(self.chandle), None)

        # Check power Status
        try:
            assert_pico_ok(self.status["openunit"])
        except: # PicoNotOkError:
            powerStatus = self.status["openunit"]

            if powerStatus == 286:
                self.status["changePowerSource"] = ps.ps4000aChangePowerSource(self.chandle, powerStatus)
            elif powerStatus == 282:
                self.status["changePowerSource"] = ps.ps4000aChangePowerSource(self.chandle, powerStatus)
            else:
                raise

            assert_pico_ok(self.status["changePowerSource"])

        # ----------
        # Setup Channels, Trigger, Time
        # ----------

        # ----- Set up channel A
        handle = self.chandle
        channel = PS4000a_CHANNEL_A = 0
        enabled = 1
        coupling_type = PS4000a_DC = 1
        analogOffset = 0
        self.chARange = 7
        self.status["setChA"] = ps.ps4000aSetChannel(handle, channel, enabled, coupling_type, self.chARange, analogOffset)
        assert_pico_ok(self.status["setChA"])

        # ----- Set up channel B
        handle = self.chandle
        channel = PS4000a_CHANNEL_B = 1
        enabled = 1
        coupling_type = PS4000a_DC = 1
        analogOffset = 0
        self.chBRange = 7
        self.status["setChB"] = ps.ps4000aSetChannel(handle, channel, enabled, coupling_type, self.chBRange, analogOffset)
        assert_pico_ok(self.status["setChB"])

        # ----- Set up simple Trigger
        handle = self.chandle
        enabled = 1
        # source = PS4000a_CHANNEL_B
        source = self.trigger_chan_number
        threshold = mV2adc(self.trigger_threshold, self.chBRange, self.maxADC)
        direction = PS4000a_RISING = 2
        delay = 0 # s
        autoTrigger_ms = 1 # ms  #TODO: Autotriggers after some time ?
        self.status["trigger"] = ps.ps4000aSetSimpleTrigger(handle, enabled, source, threshold, direction, delay, autoTrigger_ms )
        assert_pico_ok(self.status["trigger"])

        # ----- Setup Timebase
        handle = self.chandle
        self.timebase = self.timebase
        noSamples = self.maxSamples
        self.timeIntervalns = ctypes.c_float()
        pointer_to_timeIntervalNanoseconds = ctypes.byref(self.timeIntervalns)
        returnedMaxSamples = ctypes.c_int32()
        pointer_to_maxSamples = ctypes.byref(returnedMaxSamples)
        segment_index = 0
        self.status["getTimebase2"] = ps.ps4000aGetTimebase2(handle, self.timebase, noSamples, pointer_to_timeIntervalNanoseconds, pointer_to_maxSamples, segment_index)
        assert_pico_ok(self.status["getTimebase2"])

        # ----------
        # Setup Memory and Buffers
        # ----------

        # ----- Set  up memory segments
        handle = self.chandle
        nSegments = 10
        nMaxSamples = ctypes.c_int32(0)
        self.status["setMemorySegments"] = ps.ps4000aMemorySegments(self.chandle, 10, ctypes.byref(nMaxSamples))
        assert_pico_ok(self.status["setMemorySegments"])

        # ----- Set number of captures
        handle = self.chandle
        nCaptures = 1
        self.status["SetNoOfCaptures"] = ps.ps4000aSetNoOfCaptures(handle, nCaptures)
        assert_pico_ok(self.status["SetNoOfCaptures"])

        # ----- Create buffers
        self.bufferA = (ctypes.c_int16 * self.maxSamples)()
        self.bufferB = (ctypes.c_int16 * self.maxSamples)()

        # ----- Assign buffers
        handle = self.chandle
        channelA = PS4000A_CHANNEL_A = 0
        channelB = PS4000A_CHANNEL_B = 1
        bufferLength = self.maxSamples
        mode = PS4000A_RATIO_MODE_NONE = 0

        self.status["setDataBufferA"] = ps.ps4000aSetDataBuffer(handle, PS4000A_CHANNEL_A, ctypes.byref(self.bufferA), bufferLength, 0, mode)
        self.status["setDataBufferB"] = ps.ps4000aSetDataBuffer(handle, PS4000A_CHANNEL_B, ctypes.byref(self.bufferB), bufferLength, 0, mode)



    ############## PMD mandatory methods

    def get_the_x_axis(self):
        print("Tut")
        return 0
        # return self.data_transfer.time_data().magnitude


    def start_a_grab_snap(self):

        # ----------
        # Get Data
        # ----------

        # ----- Run Block Capture
        # This will continue to run until buffer is full, then ps4000aIsReady gives a "go"
        handle = self.chandle
        noOfPreTriggerSamples = self.preTriggerSamples
        noOfPostTriggerSamples = self.postTriggerSamples
        timebase = self.timebase
        timeIndisposedMs = None # not needed here
        segment_index = 0
        lpReady = None # using ps4000aIsReady rather than ps4000aBlockReady
        pParameter = None

        self.status["runBlock"] = ps.ps4000aRunBlock(handle, noOfPreTriggerSamples, noOfPostTriggerSamples, timebase, timeIndisposedMs, segment_index, lpReady, pParameter)
        assert_pico_ok(self.status["runBlock"])


        # --- Check for end of capture
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps.ps4000aIsReady(self.chandle, ctypes.byref(ready))

        # Creates a overflow location for data
        overflow = (ctypes.c_int16 * 10)()
        # Creates converted types maxsamples
        cmaxSamples = ctypes.c_int32(self.maxSamples)


        # ---- Collect data from buffer
        handle = self.chandle
        start_index = 0
        pointer_to_number_of_samples = ctypes.byref(cmaxSamples)
        downsample_ratio = 0
        downsample_ratio_mode = PS4000a_RATIO_MODE_NONE = 0
        segmentIndex = 0
        pointer_to_overflow = ctypes.byref(overflow)

        self.status["getValues"] = ps.ps4000aGetValues(self.chandle, start_index, pointer_to_number_of_samples, downsample_ratio, downsample_ratio_mode, segmentIndex, pointer_to_overflow)
        assert_pico_ok(self.status["getValues"])

        # # convert from adc to mV
        channelA_data =  adc2mV(self.bufferA, self.chARange, self.maxADC)
        channelB_data =  adc2mV(self.bufferB, self.chBRange, self.maxADC)

        # Create time data
        time = np.linspace(0, ((cmaxSamples.value)-1) * self.timeIntervalns.value * 1e-9, cmaxSamples.value)

        return time, [np.array(channelA_data), np.array(channelB_data)]

    def set_timebase(self, aquire_time=None, sampling_freq=None):
        if aquire_time: self.num_points = self.sampling_frequency*1e6 *aquire_time
        elif sampling_freq: self.num_points = sampling_freq*1e6 *self.aquire_time

        self.postTriggerSamples = int( self.num_points - self.preTriggerSamples)
        self.maxSamples = int(self.preTriggerSamples + self.postTriggerSamples)


    def terminate_the_communication(self, manager, hit_except):
        try:
            print('Communication terminated')
            exit(manager)
            manager.close()

        except:
            hit_except = True
            #if not exit(manager, *sys.exc_info()):

                #raise
        #finally:
        #    if not hit_except:
        #        exit(manager)
        #        manager.close()


