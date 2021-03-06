#!/usr/bin/python
"""
National Instruments USB-6218 32-Input, 16-bit DAQ
"""
#from pkg_resources import resource_filename
try:
    import pkgutil
    import os
    import ctypes
    import numpy
    import math
    import sys
    import pickle
    import time
    import ni_consts as c
    import daq
    import binascii
except:
    raise

#import logging
#import logging.config
#logging.config.fileConfig("logging.conf")
#logger = logging.getLogger("daqLog")



#>>> find_library('nidaqmxbase')
#'/Library/Frameworks/nidaqmxbase.framework/nidaqmxbase'
if os.name == 'nt':
    nidaq = ctypes.windll.nicaiu # load the nidaqmx dll for windows
    #nidaq = ctypes.cdll.nidaqmxbase # load the nidaqmx base dll for windows
elif os.name == 'posix':
    # linux nidaqmx
    nidaq = ctypes.cdll.LoadLibrary("/usr/local/natinst/nidaqmx/lib/libnidaqmx.so.1.6.0")
    # mac osx nidaqmx base module
    #nidaq = ctypes.cdll.LoadLibrary('/Library/Frameworks/nidaqmxbase.framework/nidaqmxbase')
##############################

int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
#TaskHandle = uInt32
TaskHandle = ctypes.c_int32()
written = int32()
pointsRead = uInt32()

    
def CHK(err):
    #a simple error checking routine
    if err < 0:
        buf_size = 1000
        #buf = ctypes.create_string_buffer('\000' * buf_size)
        buf = ctypes.create_string_buffer(buf_size)
        nidaq.DAQmxGetErrorString(err,ctypes.byref(buf),buf_size)
        raise RuntimeError('nidaq call failed with error %d: %s'%(err,repr(buf.value)))
        


class pynidaq(daq.daq):
    """
    Tested with National Instruments USB-6218 32-Input, 16-bit DAQ
    """
    
    def __init__(self, handle='Dev1'):
        """
        DAQ Device ID in the form Dev1, Dev2, etc.
        """
        daq.daq.__init__(self)
        class_name = self.__class__.__name__
        #print "class", class_name, "created"
        self.__fillhwinfo(handle=handle)

        handle=ctypes.create_string_buffer(handle.encode('utf-8'))

        self.bus = getproductbus(handle)
        self.dll = 'nidaqmx'
        self.numai = getnumai(handle)
        self.numao = getnumao(handle)
        self.numdi = getnumdi(handle)
        self.numdo = getnumdo(handle)
        self.numco = getnumco(handle)
        self.numci = getnumci(handle)
        self.model = getdevicenumber(handle)
        self.handle = handle

        #self.dotask = nidotask()
        #self.aitask = niaitask()
        #self.aotask = niaotask()
        #self.cotask = nicotask()
        #self.citask = nicitask()
        #self.ditask = niditask()
        
        #self.dosactive = []
    def __del__(self):
        class_name = self.__class__.__name__
             
    def __fillhwinfo(self,
                handle='Dev1'):
        deviceunplugged = 0

        handle=ctypes.create_string_buffer(handle.encode('utf-8'))
        self.simulated = ctypes.c_int32()
        
        CHK(nidaq.DAQmxGetDevIsSimulated(handle, ctypes.byref(self.simulated)))
        if(self.simulated == None):
            #print 'Simulated daq detected.\n'
            #logger.info('Simulated daq detected')
            pass
            
        else:
            #print 'Hardware daq detected.\n'
            #logger.info('Hardware daq detected.')
            pass

        self.serialnumber = ctypes.c_int32()
        
        nidaq.DAQmxGetDevSerialNum(handle, ctypes.byref(self.serialnumber))
        self.serial_number = hex(int(self.serialnumber.value))

        if (self.serialnumber == 0):
            #print 'Device Not Connected.\n'
            deviceunplugged = 1

                    
        if os.name == 'nt':
            self.category = getproductcategory(handle=handle)
        else:
            self.category = 0
        
        #print 'Product Category:', ni_cat # returns 14643 or M Series DAQ for the USB6218
        #print ''

        #documentation missing for this
        #producttype = numpy.zeros(10,dtype=numpy.uint32)
        #CHK(nidaq.DAQmxGetDevProductType('Dev2', producttype.ctypes.data, uInt32(10)))
        #print producttype




        if os.name == 'nt':
            self.cserialnumber = ctypes.c_int32()
            #don't run this through CHK just fail and move on
            
            if(nidaq.DAQmxGetCarrierSerialNum(handle, ctypes.byref(self.cserialnumber)) == 0):
                pass
            #print 'Carrier Serial Number:', hex(cserialnumber)         
            #print ""   

            #not sure what this is just returns nothing
            #print 'Chassis Modules:'
            #modules = numpy.zeros(1000,dtype=numpy.str_)
            #CHK(nidaq.DAQmxGetDevChassisModuleDevNames(daq, modules.ctypes.data, uInt32(1000)))
            #modules = ''.join(list(modules))
            #print modules + '\n'        
     
        if (deviceunplugged):
            return

        if os.name == 'nt':
            self.atrigger = ctypes.c_int32()
            nidaq.DAQmxGetDevAnlgTrigSupported(handle, ctypes.byref(self.atrigger))
            if(self.atrigger):
                pass
            #print 'Analog trigger supported.\n'


        if os.name == 'nt':    
            self.dtrigger = ctypes.c_int32()
            nidaq.DAQmxGetDevDigTrigSupported(handle, ctypes.byref(self.dtrigger))
            if(self.dtrigger):
                pass
                #print 'Digital trigger supported.\n' 

                 

        #print 'Analog In Channels:'
        #self.aichannels = numpy.zeros(1000,dtype=numpy.str_)
        self.aichannels = ctypes.create_string_buffer(1000)
        CHK(nidaq.DAQmxGetDevAIPhysicalChans(handle, ctypes.byref(self.aichannels), uInt32(1000)))
        
        self.aichannels = ''.join(list(str(self.aichannels.value,'utf-8'))).split(', ')
        #print aichannels + '\n'

        if os.name == 'nt':
            self.maxSchRate = ctypes.c_double()
            if(nidaq.DAQmxGetDevAIMaxSingleChanRate(handle, ctypes.byref(self.maxSchRate))):
                pass
            else:
                pass
                #print 'Max Single Channel Sample Rate:', maxSchRate
                #print ""

        if os.name == 'nt':
            self.maxMchRate = ctypes.c_double()
            if(nidaq.DAQmxGetDevAIMaxMultiChanRate(handle, ctypes.byref(self.maxMchRate))):
                pass
            else:
                pass
                #print 'Max Multi Channel Sample Rate:', maxMchRate
                #print ""

        if os.name == 'nt':
            self.minSamplingRate = ctypes.c_double()
            if(nidaq.DAQmxGetDevAIMinRate(handle, ctypes.byref(self.minSamplingRate))):
                pass
            else:
                pass
                #print 'Minimum Sample Rate:', minSamplingRate
                #print ""

        if os.name == 'nt':
            self.simSampling = ctypes.c_int32()
            if(nidaq.DAQmxGetDevAISimultaneousSamplingSupported(handle, ctypes.byref(self.simSampling))):
                pass
            else:
                if(self.simSampling):
                    pass
                #print 'Simultaneous sampling supported\n'

        #print 'Analog Out Channels:'
        #self.aochannels = numpy.zeros(1000,dtype=numpy.str_)
        self.aochannels = ctypes.create_string_buffer(1000)
        CHK(nidaq.DAQmxGetDevAOPhysicalChans(handle, ctypes.byref(self.aochannels), uInt32(1000)))
        self.aochannels = ''.join(list(str(self.aochannels.value,'utf-8'))).split(', ')

      

        #print aochannels, '\n'

        #print 'Digital In Lines:'
        #self.dils = numpy.zeros(1000,dtype=numpy.str_)
        self.dils = ctypes.create_string_buffer(1000)
        CHK(nidaq.DAQmxGetDevDILines(handle, ctypes.byref(self.dils), uInt32(1000)))
        self.dils = ''.join(list(str(self.dils.value,'utf-8'))).split(', ')
        #print dils, '\n'

        #print 'Digital In Ports:'
        #self.dips = numpy.zeros(1000,dtype=numpy.str_)
        self.dips = ctypes.create_string_buffer(1000)
        CHK(nidaq.DAQmxGetDevDIPorts(handle, ctypes.byref(self.dips), uInt32(1000)))
        self.dips = ''.join(list(str(self.dips.value,'utf-8'))).split(', ')
        #print dips, '\n'

        #print 'Digital Out Lines:'
        #self.dols = numpy.zeros(1000,dtype=numpy.str_)
        self.dols = ctypes.create_string_buffer(1000)
        CHK(nidaq.DAQmxGetDevDOLines(handle, ctypes.byref(self.dols), uInt32(1000)))
        self.dols = ''.join(list(str(self.dols.value,'utf-8'))).split(', ')
        #print dols, '\n'

        #print 'Digital Out Ports:'
        #self.dops = numpy.zeros(1000,dtype=numpy.str_)
        self.dops = ctypes.create_string_buffer(1000)
        CHK(nidaq.DAQmxGetDevDOPorts(handle, ctypes.byref(self.dops), uInt32(1000)))
        self.dops = ''.join(list(str(self.dops.value,'utf-8'))).split(', ')
        #print dops, '\n'


        #print 'Counter Input Channels:'
        #self.cichannels = numpy.zeros(1000,dtype=numpy.str_)
        self.cichannels = ctypes.create_string_buffer(1000)
        CHK(nidaq.DAQmxGetDevCIPhysicalChans(handle, ctypes.byref(self.cichannels), uInt32(1000)))
        self.cichannels = ''.join(list(str(self.cichannels.value,'utf-8'))).split(', ')
        #print cichannels, '\n'


        #print 'Counter Output Channels:'
        #self.cochannels = numpy.zeros(1000,dtype=numpy.str_)
        self.cochannels = ctypes.create_string_buffer(1000)
        CHK(nidaq.DAQmxGetDevCOPhysicalChans(handle, ctypes.byref(self.cochannels), uInt32(1000)))
        self.cochannels = ''.join(list(str(self.cochannels.value,'utf-8'))).split(', ')
        
        #print cochannels, '\n'
    def connect_terms(self, source_ch,destination,modifier=c.DAQmx_Val_DoNotInvertPolarity):
    #DAQmx_Val_DoNotInvertPolarity
    #DAQmx_Val_InvertPolarity 
    #int32 DAQmxConnectTerms (const char sourceTerminal[], const char destinationTerminal[], int32 signalModifiers);
        print ('source:', source_ch)
        print ('destination:', destination)
        src = ctypes.create_string_buffer(source_ch)
        dst = ctypes.create_string_buffer(destination)

        CHK(nidaq.DAQmxConnectTerms(src, dst, modifier))




    class analog_output(daq.daq.analog_output):
        def __init__(self,
                     daqclass,
                     channel=('Dev1/ao0',),
                     contfin='fin',
                     minimum=-10.0,
                     maximum=10.0,
                     timeout=10.0,
                     samplerate=10000.0,
                     samplesPerChan=2000,
                     clock='OnboardClock'):
            
            class_name = self.__class__.__name__
            self.channel = channel
            #print "class", class_name, "created"

            if (contfin == 'fin'):
                self.contfin = c.DAQmx_Val_FiniteSamps
            elif(contfin == 'cont'):
                self.contfin = c.DAQmx_Val_ContSamps
            else:
                raise            
            
            self.minimum = float64(minimum)
            self.maximum = float64(maximum)
            self.timeout = float64(timeout)
            #self.bufferSize = uInt32(10)
            #self.pointsToRead = self.bufferSize
            #self.pointsRead = uInt32()
            self.sampleRate = float64(samplerate)
            self.samplesPerChan = uInt64(samplesPerChan)
            
            self.clockSource = ctypes.create_string_buffer(clock.encode('utf-8'))         
            
            self.aotask = niaotask()
            self.aotask.create_channel(self.channel,
                                       self.contfin,
                                       self.minimum, 
                                       self.maximum,
                                       self.sampleRate,
                                       self.samplesPerChan,
                                       self.clockSource)
            
        def __del__(self):
            class_name = self.__class__.__name__
            print ("class", class_name, "destroyed")


        def output_dc(self,voltage):
            self.aotask.write_data(self.channel, voltage)
            
            #tstart = time.time()
            #if self.taskHandle.value != 0:
            #    nidaq.DAQmxStopTask(self.taskHandle)
            #return data
        def output_waveform(self, waveform):
            self.aotask.write_data(self.channel, waveform)



    def __del__(self):
        class_name = self.__class__.__name__
        #print "class", class_name, "destroyed"


    class analog_input(daq.daq.analog_input):
        def __init__(self,
                     daqclass,
                     channel=('Dev1/ai0',),
                     rsediff='rse',
                     contfin='fin',
                     minimum=-10.0,
                     maximum=10.0,
                     timeout=30.0,
                     samplerate=10000.0,
                     samplesperchan=10000,
                     clock='OnboardClock'):
            class_name = self.__class__.__name__
            #print "class", class_name, "created"

            self.chan = channel

            if (rsediff == 'diff'):
                self.rsediff = c.DAQmx_Val_Diff
            elif(rsediff == 'rse'):
                self.rsediff = c.DAQmx_Val_RSE
            else:
                raise

            if (contfin == 'fin'):
                self.contfin = c.DAQmx_Val_FiniteSamps
            elif(contfin == 'cont'):
                self.contfin = c.DAQmx_Val_ContSamps
            else:
                raise
            
            #self.parentdaq = daqclass
            self.minimum = float64(minimum)
            self.maximum = float64(maximum)
            self.timeout = float64(timeout)
            #self.bufferSize = uInt32(10)
            #self.pointsToRead = self.bufferSize
            #self.pointsRead = uInt32()
            self.sampleRate = float64(samplerate)
            self.samplesPerChan = uInt64(samplesperchan)


            self.clockSource = ctypes.create_string_buffer(clock.encode('utf-8'))
            #self.data = numpy.zeros((1000,),dtype=numpy.float64)

            self.aitask = niaitask()

            self.aitask.create_channel(self.chan,
                                                 self.rsediff,
                                                 self.contfin,
                                                 self.minimum,
                                                 self.maximum,
                                                 self.sampleRate,
                                                 self.samplesPerChan,
                                                 self.clockSource)            

        def __del__(self):
            class_name = self.__class__.__name__
            #print "class", class_name, "destroyed"


        def acquire(self,num_samples):


            #tstart = time.time()
            #data = self.parentdaq.aitask.get_data(self.chan, num_samples)
            data = self.aitask.get_data(self.chan, num_samples)
            #tstop = time.time()
            #print tstart
            #print tstop
            #acquiretime = tstop - tstart
            #print 'Total Acquisition Time:', acquiretime, 'sec'
            #print num_samples/acquiretime, 'samples/sec'

            return data
        
        def start(self):
            self.aitask.start()
        def stop(self):
            self.aitask.stop()
        def AcquireAndGraph(self,num_samples):

            try:
                import matplotlib.pyplot as plt
                #import scipy.signal.waveforms as waveforms
                import scipy
            except:
                print ('AcquireAndGraph function requires Matplotlib and Scipy.')
                return
    
    
            
                
            
            y = self.acquire(num_samples)
            #arange(start,stop,step)

            acqTime = ((num_samples)/self.sampleRate.value)*1000 # turn into ms
            t = scipy.linspace(0,acqTime,num_samples)

            print('chan', self.chan)
            if len(self.chan) == 1:
                plt.plot(t,y,label=self.chan)
            else:
                for i in range(len(self.chan)):
                    print('y',y)
                    plt.plot(t,y[i],label=self.chan[i])
            plt.legend(fontsize=8)#bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                        #ncol=2, mode="expand", borderaxespad=0.)
            plt.grid(True)
            plt.xlabel('Time(ms)')
            plt.ylabel('Volts')
            plt.title('Voltage Versus Time')
            plt.show()


            """Acquirefig = plt.figure()
            Acquireplt = Acquirefig.add_subplot(111)
            Acquireplt.plot(t,y)

            Acquireplt.grid(True)

            Acquireplt.set_xlabel('Time(ms)')
            Acquireplt.set_ylabel('Volts')
            Acquireplt.set_title('Voltage Versus Time')
            
            plt.savefig('VvsT')
            
            plt.show()   """
            
            return y


    class counter_output(daq.daq.counter_output):
        def __init__(self,
                     daqclass,
                     channel=('Dev1/actr0',),
                     frequency=100,
                     dutycycle=0.5,
                     delay=0,
                     idlestate=c.DAQmx_Val_Low):
            class_name = self.__class__.__name__
            #print "class", class_name, "created"


            
            
            self.pwmchan = channel
            print ('Channel:',self.pwmchan)
            self.pwmchan = ctypes.create_string_buffer(self.pwmchan)
            #self.parentdaq = daqclass
            self.cotask = nicotask()
        
            self.cotask.create_channel(self.pwmchan,
                                                 frequency=frequency,
                                                 dutycycle=dutycycle,
                                                 delay=delay,
                                                 idlestate=idlestate)

            

        def __del__(self):
            class_name = self.__class__.__name__
            #print "class", class_name, "destroyed"


            
        def start(self):
            self.cotask.start_channel(self.pwmchan)
            
        def stop(self):
            self.cotask.stop_channel(self.pwmchan)


        def update_pwm(self,frequency,dutycycle):
            self.cotask.update_pwm(self.pwmchan, frequency, dutycycle)              

    class counter_input(daq.daq.counter_input):
        def __init__(self,
                     daqclass,
                     channel=('Dev1/actr0',),
                     min_val=1.0,
                     max_val=10000.0,
                     edge='rising',
                     meas_method='low_freq_1_ctr',
                     meas_time=1.0,
                     divisor=1):
            
            class_name = self.__class__.__name__
            #print "class", class_name, "created"

            if (edge == 'rising'):
                ni_edge = c.DAQmx_Val_Rising
            elif (edge == 'falling'):
                ni_edge = c.DAQmx_Val_Falling
            else:
                raise

            if (meas_method == 'low_freq_1_ctr'):
                ni_meas_method = c.DAQmx_Val_LowFreq1Ctr
            elif (meas_method == 'high_freq_2_ctr'):
                ni_meas_method = c.DAQmx_Val_HighFreq2Ctr
            elif (meas_method == 'divide_2_ctr'):
                ni_meas_method = c.DAQmx_Val_LargeRng2Ctr
            else:
                raise
            
            self.cichan = channel
            print ('Channel:', self.cichan)
            #self.cichan = ctypes.create_string_buffer(self.cichan)
            #self.parentdaq = daqclass
            self.citask = nicitask()
            #create_channel(self, channel, min_val, max_val, edge, meas_method, meas_time, divisor)
            self.citask.create_channel(self.cichan,
                                                 min_val,
                                                 max_val,
                                                 ni_edge,
                                                 ni_meas_method,
                                                 meas_time,
                                                 divisor)

            

        def __del__(self):
            class_name = self.__class__.__name__
            #print "class", class_name, "destroyed"


            
        def start(self):
            self.citask.start_channel(self.cichan)
            
        def stop(self):
            self.citask.stop_channel(self.cichan)

        def get_frequency(self, num_samples):
            freq = self.citask.get_frequency(num_samples=num_samples)
            return freq

  

    class digital_output(daq.daq.digital_output):
        def __init__(self,
                     daqclass,
                     channel=('Dev1/port0/line0',),
                     group=c.DAQmx_Val_ChanPerLine,
                     samplerate=1.0,
                     samplesPerChan=1):

            class_name = self.__class__.__name__
            #print "class", class_name, "created"
            self.sampleRate = float64(samplerate)
            self.samplesPerChan = uInt64(samplesPerChan)
            #self.clockSource = ctypes.create_string_buffer(clock)

            self.value = 0

            
            #self.parentdaq.dosactive.append(self.value)            
            self.dochan = channel#self.handle + '/' + port + '/' + channel + ':' + '0' 

            self.dotask = nidotask()
            self.dotask.create_channel(self.dochan)

            #CHK(nidaq.DAQmxCreateDOChan(self.parentdaq.doTaskHandle,
            #                            self.dochan,
            #                            "",
            #                            c.DAQmx_Val_ChanForAllLines))

            #CHK(nidaq.DAQmxCfgSampClkTiming(self.PWMtaskHandle,self.clockSource,self.sampleRate,
            #                                c.DAQmx_Val_Rising,c.DAQmx_Val_FiniteSamps,self.samplesPerChan))


            
        def __del__(self):
            class_name = self.__class__.__name__
            #print "class", class_name, "destroyed"

            if self.dotask.doTaskHandle.value != 0:
                nidaq.DAQmxStopTask(self.dotask.doTaskHandle)
                nidaq.DAQmxClearTask(self.dotask.doTaskHandle)
            

        def output(self,
                   pinstate=0):
        
            if(isinstance(pinstate,int)):
                self.dotask.set_vals(self.dochan, (pinstate,))
            else:
                self.dotask.set_vals(self.dochan, pinstate)

                  
            """CHK(nidaq.DAQmxWriteDigitalScalarU32(self.PWMtaskHandle,
                                                 uInt32(1),
                                                 float64(1.0),
                                                 uInt32(pinstate),
                                                 #dataout.ctypes.data,
                                                 None))"""


    class digital_input(daq.daq.digital_input):
        def __init__(self,
                     daqclass,
                     channel='Dev1/port0/line0',
                     group=c.DAQmx_Val_ChanPerLine,
                     samplerate=1.0,
                     samplesPerChan=1):

            class_name = self.__class__.__name__
            #print "class", class_name, "created"
            self.sampleRate = float64(samplerate)
            self.samplesPerChan = uInt64(samplesPerChan)
            #self.clockSource = ctypes.create_string_buffer(clock)

            self.value = 0

            
            #self.parentdaq.dosactive.append(self.value)            
            self.dichan = channel 

            self.ditask = niditask()
            self.ditask.create_channel(self.dichan)

            #CHK(nidaq.DAQmxCreateDOChan(self.parentdaq.doTaskHandle,
            #                            self.dochan,
            #                            "",
            #                            c.DAQmx_Val_ChanForAllLines))

            #CHK(nidaq.DAQmxCfgSampClkTiming(self.PWMtaskHandle,self.clockSource,self.sampleRate,
            #                                c.DAQmx_Val_Rising,c.DAQmx_Val_FiniteSamps,self.samplesPerChan))


            
        def __del__(self):
            class_name = self.__class__.__name__
            print ("class", class_name, "destroyed")

            if self.ditask.diTaskHandle.value != 0:
                nidaq.DAQmxStopTask(self.ditask.diTaskHandle)
                nidaq.DAQmxClearTask(self.ditask.diTaskHandle)
            

        def get(self,num_points=1):
                   
            
            return self.ditask.get(self.dichan,
                                   points=num_points)
   
                
                  



def daqfind():
    """ Searches for NI Daqs Dev(0-127), cDAQN(0-127), Mod(0-7) 

    Returns a list of valid handles for devices currently
    found on system.
    """
    nd = 0 # number of daqs

    # load the ni device category dictionary file(translate device
    # category number to human readable words)
    #file = open(ni_cat, 'rb')
    #ni_cat = resource_filename(__name__, 'data/ni_cat.dat')
    
    
    ni_cat = pkgutil.get_data('pydaqtools', 'data/ni_cat.dat')
    #file = open('ni_cat.dat', 'rb')
    cat = pickle.loads(ni_cat)
    #file.close()

    category = numpy.zeros(1,dtype=numpy.uint32)
    #simulated = numpy.zeros(1,dtype=numpy.uint32)
    handles = []

    for i in range(0,127):
        
        # first look for ni instruments with Dev1 or Dev2 etc. Brute force but
        # I don't see any documentation to help.         
        handle = 'Dev' + str(i)
        simulated = getdevicesimulated(handle)
        # if we received a valid answer not an error
        if(simulated == None):
            #error returned just check next daq
            pass
        elif(simulated == True):
            # the device is just a software simulated device
            handles.append(handle)
            nd = nd + 1 # inc the number of valid daqs counter
        else:
            # we've found a valid hardware ni daq(just maybe not plugged in)
            #serialnumber = numpy.zeros(1,dtype=numpy.uint32)
            serialnumber = ctypes.c_int32()
            h=ctypes.create_string_buffer(handle.encode('utf-8'))
            nidaq.DAQmxGetDevSerialNum(h, ctypes.byref(serialnumber))

            # this seems to be ni's recommended method. If serial number is
            # zero then device was installed on the system at one time but
            # it is not currently. I'm just going to ignore it.
            if (serialnumber == 0):
                pass
            # finally, a valid, installed ni hardware daq 
            else:
                # add the newly found valid handle to the list
                handles.append(handle)
                nd = nd + 1 # inc the number of valid daqs counter

        # next look for compact chassis'
        handle = 'cDAQ' + str(i)
        simulated = getdevicesimulated(handle)
        if(simulated == None):
            #error returned just check next daq
            pass
        elif(simulated == True):
            # the device is just a software simulated device
            pass
        else:
            # we've found a valid hardware ni daq(just maybe not plugged in)
            #serialnumber = numpy.zeros(1,dtype=numpy.uint32)
            serialnumber = ctypes.c_int32()
            h=ctypes.create_string_buffer(handle.encode('utf-8'))
            nidaq.DAQmxGetDevSerialNum(h, ctypes.byref(serialnumber))

            # this seems to be ni's recommended method. If serial number is
            # zero then device was installed on the system at one time byt
            # it is not currently. I'm just going to ignore it.
            if (serialnumber == 0):
                pass
            # finally, a valid, installed ni hardware daq 
            else:
                # add the newly found valid handle to the list it's just a
                # chassis but add it anyways
                handles.append(handle)
                nd = nd + 1

                # found the chassis so search for modules installed              
                for j in range(0,7):
                    handle = 'cDAQ' + str(i) + 'Mod' + str(j)
                    simulated = getdevicesimulated(handle)
                    if(simulated < 0):
                        #error returned just check next daq
                        pass
                    elif(simulated == 1):
                        # the device is just a software simulated device
                        pass
                    else:
                        # we've found a valid hardware module
                        handles.append(handle)
                        
                        nd = nd + 1
    return handles

def getdevicesimulated(handle='Dev1'):
    #simulated = numpy.zeros(1,dtype=numpy.uint32)
    simulated = ctypes.c_bool()    
    handle=ctypes.create_string_buffer(handle.encode('utf-8'))
    answer = nidaq.DAQmxGetDevIsSimulated(handle, ctypes.byref(simulated))
    if (int(answer) == 0): # check for a valid reply
        return bool(simulated)
    else:
        pass #invalid reply not sure what to do here

def getproductcategory(handle='Dev1'):
    #handle=ctypes.create_string_buffer(handle.encode('utf-8'))
    #ni_cat = resource_filename(__name__, 'data/ni_cat.dat')
    ni_cat = pkgutil.get_data('pydaqtools', 'data/ni_cat.dat')
    #file = open('data/ni_cat.dat', 'rb')
    ni_cat = pickle.loads(ni_cat)
    #file.close()

    category = ctypes.c_int32()
    if os.name == 'nt':
        nidaq.DAQmxGetDevProductCategory(handle, ctypes.byref(category))
    return ni_cat[str(category.value)]


def getproductbus(handle='Dev1'):
    #handle=ctypes.create_string_buffer(handle.encode('utf-8'))
    #ni_bus = resource_filename(__name__, 'data/ni_bus.dat')
    ni_bus = pkgutil.get_data('pydaqtools', 'data/ni_bus.dat')
    #file = open('data/ni_bus.dat', 'rb')
    ni_bus = pickle.loads(ni_bus)
    #file.close()

    bus = ctypes.c_int32()
    nidaq.DAQmxGetDevBusType(handle, ctypes.byref(bus))
    return ni_bus[str(bus.value)]

def getdevicenumber(handle='Dev1'):
    #handle=ctypes.create_string_buffer(handle.encode('utf-8'))
    #ni_dev = resource_filename(__name__, 'data/ni_dev.dat')
    ni_dev = pkgutil.get_data('pydaqtools', 'data/ni_dev.dat')
    #file = open('data/ni_dev.dat', 'rb')
    ni_dev = pickle.loads(ni_dev)
    #file.close()

    device = ctypes.c_int32()
    nidaq.DAQmxGetDevProductNum(handle, ctypes.byref(device))
    return ni_dev[str(device.value)]

def getnumai(handle='Dev1'):
    aichannels = ctypes.create_string_buffer(1000)
    CHK(nidaq.DAQmxGetDevAIPhysicalChans(handle, ctypes.byref(aichannels), uInt32(1000)))          # not supported for this device
        #return int(0)
    aichannels = ''.join(list(str(aichannels.value)))
    if (len(aichannels) <= 3):
        return 0
    aichannels = aichannels.rsplit(', ')
    return len(aichannels)

def getnumao(handle='Dev1'):
    aochannels = ctypes.create_string_buffer(1000)
    CHK(nidaq.DAQmxGetDevAOPhysicalChans(handle, ctypes.byref(aochannels), uInt32(1000)))
        # not supported for this device          
        #return int(0)
    
    aochannels = ''.join(list(str(aochannels.value)))
    if (len(aochannels) <= 3):
        return 0
    aochannels = aochannels.rsplit(', ')
    return len(aochannels)

def getnumdi(handle='Dev1'):
    dichannels = ctypes.create_string_buffer(1000)
    if(nidaq.DAQmxGetDevDILines(handle, ctypes.byref(dichannels), uInt32(1000))):
        # not supported for this device
        return int(0)
    dichannels = ''.join(list(str(dichannels.value)))
    if (len(dichannels) <= 3):
        return 0        
    dichannels = dichannels.rsplit(', ')
    return len(dichannels)

def getnumdo(handle='Dev1'):
    dochannels = ctypes.create_string_buffer(1000)
    if(nidaq.DAQmxGetDevDOLines(handle, ctypes.byref(dochannels), uInt32(1000))):
        # not supported for this device          
        return int(0)
    dochannels = ''.join(list(str(dochannels.value)))
    if (len(dochannels) <= 3):
        return 0        
    dochannels = dochannels.rsplit(', ')
    return len(dochannels)

def getnumco(handle='Dev1'):
    cochannels = ctypes.create_string_buffer(1000)
    if(nidaq.DAQmxGetDevCOPhysicalChans(handle, ctypes.byref(cochannels), uInt32(1000))):
        # not supported for this device          
        return int(0)
    cochannels = ''.join(list(str(cochannels.value)))
    if (len(cochannels) <= 3):
        return 0        
    cochannels = cochannels.rsplit(', ')
    return len(cochannels)

def getnumci(handle='Dev1'):
    cichannels = ctypes.create_string_buffer(1000)
    if(nidaq.DAQmxGetDevCIPhysicalChans(handle, ctypes.byref(cichannels), uInt32(1000))):
        # not supported for this device          
        return int(0)
    cichannels = ''.join(list(str(cichannels.value)))
    if (len(cichannels) <= 3):   # this is just an empty binary
        return 0        
    cichannels = cichannels.rsplit(', ')
    return len(cichannels)     

    


    
class niditask:
    def __init__(self):
        #self.diTaskHandle = TaskHandle(0)
        self.diTaskHandle = ctypes.c_void_p()
        CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.diTaskHandle)))
        self.numch = 0
        self.ch = {}
        self.datain = []
        
      
        
    def create_channel(self, channel):
        
        #for ch in channel:
        #    chan = ctypes.create_string_buffer(ch)
        #    print (chan.value)        
        chan = ','.join(channel)
        chan = ctypes.create_string_buffer(chan.encode('utf-8'))
        print(chan.value)        
        CHK(nidaq.DAQmxCreateDIChan(self.diTaskHandle,
                                    chan,
                                    "",
                                    c.DAQmx_Val_GroupByChannel))
        
    def get(self, channel, points):
        
        #self.start()
        bufferSize=uInt32(points*len(channel))

        samps_read = uInt32()
        bytes_per_sample = uInt32()
        #self.data = numpy.zeros((points*len(channel),),dtype=numpy.uint8)
        self.samples = (ctypes.c_uint8 * len(channel) * points)()
        #self.samples = (ctypes.c_double * len(channel) * points)()
        #self.pointsRead = uInt32()

        CHK(nidaq.DAQmxReadDigitalLines(self.diTaskHandle,
                                        uInt32(points), #c.DAQmx_Val_Auto,  # samples per channel
                                        float64(10.0),     # timeout
                                        c.DAQmx_Val_GroupByChannel,    # fill mode
                                        ctypes.byref(self.samples),
                                        #self.data.ctypes.data,    # read array
                                        uInt32(bufferSize.value), # size of read array
                                        ctypes.byref(samps_read),    # actual num of samples read
                                        ctypes.byref(bytes_per_sample),     # actual number of bytes per sample
                                        None))
                                        
        self.stop()
        #print 'Samples read: ', samps_read
        #print 'Bytes per Sample: ', bytes_per_sample
        
        
        for i in range(len(channel)):
            print('i',i)
            print('points',points)
            q=numpy.frombuffer(self.samples,'uint8')
            
            q=q.reshape(len(channel),points)
            print (q)        
        
        
        
        #q=numpy.frombuffer(self.samples,dtype="uint8")
        #q=numpy.frombuffer(self.samples,dtype="bool")
        return q

    def start(self):
        CHK(nidaq.DAQmxStartTask(self.diTaskHandle))
    def stop(self):
        if self.diTaskHandle.value != 0:
            nidaq.DAQmxStopTask(self.diTaskHandle)
            

class nidotask:
    def __init__(self):
        #self.doTaskHandle = TaskHandle(0)
        self.doTaskHandle = ctypes.c_void_p()
        CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.doTaskHandle)))
        self.numch = 0
        self.ch = {}
        self.dataout = []
    def create_channel(self, channel):

        #for ch in channel:
        #    chan = ctypes.create_string_buffer(ch)
        #    print (chan.value)        
        chan = ','.join(channel)
        chan = ctypes.create_string_buffer(chan.encode('utf-8'))
        CHK(nidaq.DAQmxCreateDOChan(self.doTaskHandle,
                                    chan,
                                    "",
                                    c.DAQmx_Val_ChanForAllLines))

    def set_vals(self, channel, output):
        
        #self.data = numpy.array(output,dtype=numpy.uint8)
        #self.data = ctypes.c_int8(output)
        self.data = (ctypes.c_int8 * 1)(*output)
        self.sampleswritten = uInt32()        

        CHK(nidaq.DAQmxWriteDigitalLines(self.doTaskHandle,
                                         uInt32(int(len(output)/len(channel))),            # samples per channel
                                         uInt32(1),            # auto start
                                         float64(10.0),        # timeout
                                         c.DAQmx_Val_GroupByChannel,
                                         ctypes.byref(self.data),
                                         #self.data.ctypes.data,
                                         ctypes.byref(self.sampleswritten),
                                         None))
        #print 'Samples Written per Channel:', self.sampleswritten
    def start(self):
        CHK(nidaq.DAQmxStartTask(self.doTaskHandle))
    def stop(self):
        if self.doTaskHandle.value != 0:
            nidaq.DAQmxStopTask(self.doTaskHandle)        

class niaitask:
    def __init__(self):
        #self.aiTaskHandle = TaskHandle
        self.aiTaskHandle = ctypes.c_void_p()
        CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.aiTaskHandle)))

        
    def create_channel(self, 
                       channel, 
                       rsediff, 
                       contfin, 
                       minimum, 
                       maximum, 
                       samplerate, 
                       samplesperchannel, 
                       clocksource):


        chan=''   
        
        #chan = ctypes.create_string_buffer(channel[:].encode('utf-8'))      
        chan = ','.join(channel)
        #print(chan)
        #for ch in channel:
            #print(channel)
            #print(ch)
            
            #chan = ctypes.create_string_buffer(ch[:].encode('utf-8'))
            
            #print (str(chan.value,'utf-8'))
        chan = ctypes.create_string_buffer(chan.encode('utf-8'))
        print(chan)
        CHK(nidaq.DAQmxCreateAIVoltageChan(self.aiTaskHandle,chan,"",rsediff,minimum,maximum,
                c.DAQmx_Val_Volts,None))
        #print(chan.value)
        self.pointsToRead = samplesperchannel
        CHK(nidaq.DAQmxCfgSampClkTiming(self.aiTaskHandle,
                                        clocksource,
                                        samplerate,
                                        c.DAQmx_Val_Rising,
                                        contfin,
                                        self.pointsToRead))

        #CHK(nidaq.DAQmxCfgInputBuffer(self.aiTaskHandle,200000))

        

        self.minimum = minimum
        self.maximum = maximum
        self.samplerate = samplerate
        self.samplesperchannel = samplesperchannel
        self.clocksource = clocksource
        self.rsediff = rsediff
        self.contfin = contfin

    def start(self):
        CHK(nidaq.DAQmxStartTask(self.aiTaskHandle))
    def stop(self):
        if self.aiTaskHandle.value != 0:
            nidaq.DAQmxStopTask(self.aiTaskHandle)
            #nidaq.DAQmxClearTask(self.aiTaskHandle)       
        
    def get_data(self, channel, points):        
        # with multiple channels in the task the buffer needs to
        # be increased (bufferSize = pointsToRead * numchannelsInTask)
        self.bufferSize = uInt32(int(points*len(channel)))

        

        #this data array as well needs to be scaled by the number of channels in task
        #self.data = numpy.zeros((points*len(channel),),dtype=numpy.float64)
        #self.data = ctypes.c_double()
        self.samples = (ctypes.c_double * len(channel) * points)()

        self.pointsRead = uInt32()
        
        
        CHK(nidaq.DAQmxReadAnalogF64(self.aiTaskHandle,
                                     uInt32(int(points)),#c.DAQmx_Val_Auto (Auto means read all available)
                                     float64(10.0),       # timeout
                                     c.DAQmx_Val_GroupByChannel,
                                     #self.data.ctypes.data,
                                     ctypes.byref(self.samples),
                                     uInt32(self.bufferSize.value),
                                     ctypes.byref(self.pointsRead),None))
                                     
        print ("Acquired %d point(s)"%(self.pointsRead.value))
        #self.samples = self.samples.reshape(len(channel),points)
        #print (self.samples)        
        #print (self.samples[0][0],self.samples[0][1],self.samples[1][0],self.samples[1][1])
        
        #for i in range(len(channel)):
            #print('i',i)
            #print('points',points)
        q=numpy.frombuffer(self.samples)
            #print (q)
        #q=q.reshape(len(channel),points)
        if len(channel) > 1:
            q=q.reshape(len(channel),points)
            #samp[i]=[self.samples[i][j] for j in range(points)]
        #samp=[self.samples[i] for i in range(self.pointsRead.value)]
        
        #list = [weights[i] for i in xrange(ARRAY_SIZE_I_KNOW_IN_ADVANCE)]
        if self.contfin == c.DAQmx_Val_FiniteSamps:
            self.stop()

        return q




class niaotask:
    def __init__(self):
        #self.aoTaskHandle = TaskHandle(0)
        self.aoTaskHandle = ctypes.c_void_p()
        CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.aoTaskHandle)))
        self.ch = {}
        self.dataout = []


    def create_channel(self, 
                       channel,
                       contfin,
                       minimum, 
                       maximum,
                       samplerate,
                       samplesperchannel,
                       clocksource):

        chan = ','.join(channel)
        chan = ctypes.create_string_buffer(chan.encode('utf-8'))
        #for ch in channel:
        #    chan = ctypes.create_string_buffer(ch)
        #    print (chan.value)
        print(chan.value)
            
            
        CHK(nidaq.DAQmxCreateAOVoltageChan(self.aoTaskHandle,
                                           chan,
                                           "",
                                           minimum,
                                           maximum,
                                           c.DAQmx_Val_Volts,None))
               
        self.pointsToWrite = samplesperchannel
        CHK(nidaq.DAQmxCfgSampClkTiming(self.aoTaskHandle,
                                        '',#clocksource,#clock source default to internal
                                        samplerate,
                                        c.DAQmx_Val_Rising,
                                        contfin,
                                        self.pointsToWrite.value))            
        
        self.minimum = minimum
        self.maximum = maximum
        self.samplerate = samplerate
        self.samplesperchannel = samplesperchannel
        self.clocksource = clocksource
        self.contfin = contfin        

    def write_data(self, channel, waveform):



        # The minimum samples per channel is 2 this gives a
        # bit of a problem for output_dc

        self.stop()

        try:
            # the data needs to be in the right format here
            # need to do a reshape
            waveform.reshape(len(waveform)*len(waveform[0]) )            
            samplesperchannel = uInt32(len(waveform))
            #data = numpy.array(waveform, dtype=numpy.float64)
            #self.samples = (ctypes.c_double * len(channel) * points)()
            data = (ctypes.c_double * len(waveform))()
            
        except:
            # this is a little dangerous but if the above fails just load
            # a 2 datapoint array
            data = numpy.array([waveform,waveform], dtype=numpy.float64)
            
            data = (ctypes.c_double * 2)(*[waveform,waveform])
            #data[0]=1.0
            #data[1]=1.0
            #lll = [4,7,2,8]
            #lll_c = (ctypes.c_int * len(lll))(*lll)

        

        #y = numpy.zeros(1000,dtype=numpy.float64)

        # create 1000 evenly spaced values from time=0 to x
        #t = scipy.linspace(0,0.01,1000)
        #f = 1000
        #A = 3

        #y = A*waveforms.square(2*math.pi*f*t,duty=0.5)
        #y = A*waveforms.sawtooth(2*math.pi*f*t,width=0.5)

        
        #for i in numpy.arange(1000):
        #    y[i] = 9.95*math.sin(i*2.0*math.pi*1000.0/16000.0)
        #print len(data)
        #print data


        CHK(nidaq.DAQmxWriteAnalogF64(self.aoTaskHandle,
                                      uInt32(len(data)),  #number of samples per channel
                                      uInt32(1),  #autostart task
                                      float64(10.0), #timeout
                                      c.DAQmx_Val_GroupByChannel,
                                      ctypes.byref(data),
                                      None,None))
        #self.start()

    def start(self):
        CHK(nidaq.DAQmxStartTask(self.aoTaskHandle))
    def stop(self):
        if self.aoTaskHandle.value != 0:
            nidaq.DAQmxStopTask(self.aoTaskHandle)
            
            
class nicotask:
    def __init__(self):
        #self.coTaskHandle = TaskHandle(0)
        self.coTaskHandle = ctypes.c_void_p()
        CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.coTaskHandle)))
        
        self.numch = 0
        self.ch = {}
        self.dataout = []
       
    def create_channel(self, channel, frequency, dutycycle, delay, idlestate):


        nidaq.DAQmxStopTask(self.coTaskHandle)
        CHK(nidaq.DAQmxCreateCOPulseChanFreq(self.coTaskHandle,channel,"",
                                              c.DAQmx_Val_Hz,
                                              idlestate,
                                              float64(delay), # delay
                                              float64(frequency), # frequency
                                              float64(dutycycle))) # duty cycle
        CHK(nidaq.DAQmxCfgImplicitTiming(self.coTaskHandle,c.DAQmx_Val_ContSamps,uInt64(1000)))        
        #CHK(nidaq.DAQmxStartTask(self.coTaskHandle))

        freq = numpy.zeros(1,dtype=numpy.float64)
        duty = numpy.zeros(1,dtype=numpy.float64)
        freq = frequency
        duty = dutycycle
        self.ch[str(channel)] = self.numch
        self.dataout.append((freq,duty))
        self.numch = self.numch + 1

    def update_pwm(self, channel, frequency, dutycycle):
        index = self.ch[str(channel)]
        self.dataout[index] = (frequency, dutycycle)

        frequency = self.get_task_frequency()
        print (frequency)
        dutycycle = self.get_task_dutycycle()
        print (dutycycle)
        self.sampsWritten = uInt32()
        
        CHK(nidaq.DAQmxWriteCtrFreq(self.coTaskHandle,
                                          uInt32(1), #numSampsPerChan
                                          uInt32(1), #autostart task
                                          c.DAQmx_Val_WaitInfinitely,
                                          c.DAQmx_Val_GroupByChannel,
                                          frequency.ctypes.data,
                                          dutycycle.ctypes.data,
                                          ctypes.byref(self.sampsWritten),
                                          None))
        
    def stop_channel(self, channel):
        CHK(nidaq.DAQmxStopTask(self.coTaskHandle))


    def start_channel(self, channel):
        CHK(nidaq.DAQmxStartTask(self.coTaskHandle))
        
    def get_task_frequency(self):
        
        dataout = numpy.zeros(self.numch,dtype=numpy.float64)
        for i in range(self.numch):
            dataout[i]=self.dataout[i][0]
        return dataout
    def get_task_dutycycle(self):
        
        dataout = numpy.zeros(self.numch,dtype=numpy.float64)
        for i in range(self.numch):
            dataout[i]=self.dataout[i][1]
        return dataout      


class nicitask:
    def __init__(self):
        #self.ciTaskHandle = TaskHandle(0)
        self.ciTaskHandle = ctypes.c_void_p()
        CHK(nidaq.DAQmxCreateTask("",ctypes.byref(self.ciTaskHandle)))
        
        self.numch = 0
        self.ch = {}
        self.dataout = []
       
    def create_channel(self, channel, min_val, max_val, edge, meas_method, meas_time, divisor):

        chan=''
        chan = ','.join(channel)
        chan = ctypes.create_string_buffer(chan.encode('utf-8'))
        #for ch in channel:
        #    chan = ctypes.create_string_buffer(ch)
        #    print (chan.value)
        print(chan.value)
        
        
        
        handle='Dev1'
        handle=ctypes.create_string_buffer(handle.encode('utf-8'))
        measuretypes = ctypes.create_string_buffer(1000)
        #CHK(nidaq.DAQmxGetDevAIPhysicalChans(handle, ctypes.byref(aichannels), uInt32(1000)))          # not supported for this device
        #return int(0)
        
        #nidaq.DAQmxStopTask(self.ciTaskHandle)
        #DAQmxGetDevCISupportedMeasTypes(const char device[], int32 *data, uInt32 arraySizeInElements)
        CHK(nidaq.DAQmxGetDevCISupportedMeasTypes(handle,ctypes.byref(measuretypes),uInt32(1000)))
        print(measuretypes)
        print(binascii.hexlify(measuretypes.value))
        """int32 DAQmxCreateCIFreqChan (TaskHandle taskHandle,
                                      const char counter[],
                                      const char nameToAssignToChannel[],
                                      float64 minVal,
                                      float64 maxVal,
                                      int32 units,
                                      int32 edge,
                                      int32 measMethod,
                                      float64 measTime,
                                      uInt32 divisor,
                                      const char customScaleName[]);
        """
        '''CHK(nidaq.DAQmxCreateCIFreqChan(self.ciTaskHandle,
                                        chan,
                                        '', # name to assign to virtual channel
                                        float64(min_val),
                                        float64(max_val),
                                        c.DAQmx_Val_Hz,
                                        edge,
                                        meas_method,
                                        float64(meas_time),
                                        uInt32(divisor),
                                        ''))
        CHK(nidaq.DAQmxCfgImplicitTiming(self.ciTaskHandle,c.DAQmx_Val_FiniteSamps,uInt64(1000)))
        '''                                
        #DAQmxCreateCICountEdgesChan (TaskHandle taskHandle, const char counter[], const char nameToAssignToChannel[], int32 edge, uInt32 initialCount, int32 countDirection)
        CHK(nidaq.DAQmxCreateCICountEdgesChan(self.ciTaskHandle,
                                        chan,
                                        '',
                                        edge,
                                        0,
                                        c.DAQmx_Val_CountUp))                                      
               
        #CHK(nidaq.DAQmxStartTask(self.ciTaskHandle))
        
    def stop_channel(self):
        CHK(nidaq.DAQmxStopTask(self.ciTaskHandle))


    def start_channel(self):
        CHK(nidaq.DAQmxStartTask(self.ciTaskHandle))

    def get_frequency(self, num_samples):
        """int32 DAQmxReadCounterF64 (TaskHandle taskHandle,
                                    int32 numSampsPerChan,
                                    float64 timeout,
                                    float64 readArray[],
                                    uInt32 arraySizeInSamps,
                                    int32 *sampsPerChanRead,
                                    bool32 *reserved);
        """

        self.data = (ctypes.c_double * num_samples)()
        #self.data = numpy.zeros((num_samples,),dtype=numpy.float64)
        self.pointsRead = uInt32()
        CHK(nidaq.DAQmxReadCounterF64(self.ciTaskHandle,
                                      num_samples,
                                      float64(10.0), #self.timeout,
                                      ctypes.byref(self.data),
                                      uInt32(num_samples),
                                      ctypes.byref(self.pointsRead),None))
        q=numpy.frombuffer(self.data)
        self.stop_channel()
        return q


