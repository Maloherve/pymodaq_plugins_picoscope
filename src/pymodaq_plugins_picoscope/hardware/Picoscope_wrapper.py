# -*- coding: utf-8 -*-
"""
Created on Mon Feb 3 2025

@author: dqml-lab
"""
import sys

import ctypes
import numpy as np
from picosdk.ps4000a import ps4000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc
from math import *



class Picoscope_Wrapper:

    ############## PMD mandatory methods

    def get_the_x_axis(self):
        return self.data_transfer.time_data().magnitude

    #def setTriggerType(self):
    #    # Channel triggering
    #    self.trigger.ch_or_mask0(self.channels[0].ch_mask())
    #    self.trigger.ch_mode(self.channels[0], spcm.SPC_TM_POS)
    #    self.trigger.ch_level0(self.channels[0], 0 * units.mV, return_unit=units.mV)

    #def start_a_grab_snap(self, card, channel, Range, postTrigEv):
    def start_a_grab_snap(self, card, channel, NumSamples, SamplesPerSegment, multiple_recording):
        '''
        # define the data buffer
        self.data_transfer = spcm.DataTransfer(card)
        self.data_transfer.duration(Range * units.us, post_trigger_duration=postTrigDur * units.us)
        # Start DMA transfer
        self.data_transfer.start_buffer_transfer(spcm.M2CMD_DATA_STARTDMA)

        # start card
        card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_DATA_WAITDMA)

        data_V = []
        for chan in channel:
            data_V.append(chan.convert_data(self.data_transfer.buffer[chan.index, :], units.V).magnitude)
        '''


        #num_samples = int(NumSamples * 1e3 /1024 *units.KiS )
        #samples_per_segment = int(SamplesPerSegment * 1e3 /1024 *units.KiS )
        #multiple_recording = spcm.Multi(card)

        #multiple_recording.memory_size(num_samples)
        #multiple_recording.allocate_buffer(samples_per_segment)
        #multiple_recording.post_trigger(samples_per_segment // 2)
        multiple_recording.start_buffer_transfer(spcm.M2CMD_DATA_STARTDMA)




        try:
            card.start(spcm.M2CMD_CARD_ENABLETRIGGER, spcm.M2CMD_DATA_WAITDMA)#, spcm.M2CMD_DATA_WAITDMA, spcm.M2CMD_CARD_WAITTRIGGER)  #or waitdma  #or waitready



            data = multiple_recording.buffer
            #time_data = multiple_recording.time_data()



            data_V = []


            for segment in range(data.shape[0]):
                #print("Segment {}".format(segment))
                for chan in channel:
                    chan_data = chan.convert_data(data[segment, :, chan], units.V).magnitude # index definition: [segment, sample, channel]
                    data_V.append(chan_data)

            #print(data_V)
        except spcm.SpcmTimeout as timeout:
            print("Timeout...")




        return data_V

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


