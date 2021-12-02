#!/usr/bin/env python3

# this program only work with custom built pyaudio https://github.com/intxcc/pyaudio_portaudio/releases that is compatible only with python 3.7
# specify dummy output device as Windows audio output.

import pyaudio
import numpy as np
import queue

DUMMY_DEV_NAME = "3-4 (QUAD-CAPTURE)"
RATE = 48000
CHUNK = 128
CHANNEL_IN = 2
CHANNEL_OUT = 2
RMS_AVERAGE_CHUNK = 5

RMS_history = np.ones(RMS_AVERAGE_CHUNK)
Previous_gain = 1

def signal_proc_buff(input_buff, RMS_history, Previous_gain):
    # input_buff: stream input
    # RMS_history: rms history stored over cycles(chunks)
    # Previous_gain: gain of previous cycle(chunk)

    # Convert framebuffer into nd-array
    input_data = np.fromstring(input_buff, dtype=np.int16).reshape(CHUNK, CHANNEL_IN)
    
    # Signal processing
    output_data, RMS_history, Previous_gain = signal_proc(input_data, RMS_history, Previous_gain)

    # Convert nd-array into framebuffer
    output_buff = output_data.astype(np.int16).tostring()
    return output_buff, RMS_history, Previous_gain

def signal_proc(input_audio, RMS_history, Previous_gain):
    # input_audio: ndarray (len, ch)
    # output_audio: ndarray (len, ch)
    thres = 0.025
    makeup = 4
    transition = 128

    # normalize (to calc rms)
    input_audio_float = input_audio/(2**16/2)
    
    rms = np.sqrt(np.sum(input_audio_float ** 2) / len(input_audio_float.reshape(-1)))

    # update gain history
    for i in range(len(RMS_history)):
        if i != len(RMS_history) - 1:
            RMS_history[i] = RMS_history[i+1]
        else:
            RMS_history[i] = rms

    # weighted_rms = RMS_history * np.arange(len(RMS_history)) / sum(np.arange(len(RMS_history)))

    Target_gain = makeup * thres / max(thres, np.mean(RMS_history))
    
    # to prevent discoutinuous of audio, linearly interporate gain from previous gain to target gain
    gain = np.hstack([np.linspace(Previous_gain, Target_gain, transition), np.ones(CHUNK - transition)*Target_gain])[:,None]

    output_audio = gain * input_audio

    if Target_gain/makeup < 1:
        print(f"compress: {- 20 * np.log10(Target_gain/makeup):.02f} dB")

    Previous_gain = Target_gain
    return output_audio, RMS_history, Previous_gain


### Initialization ###
# get wasapi device
useloopback = False
p = pyaudio.PyAudio()
for i_api in range(p.get_host_api_count()):
    if 'Windows WASAPI' in p.get_host_api_info_by_index(i_api).get('name'): # use WASAPI
        InputDeviceID = p.get_host_api_info_by_index(i_api).get('defaultInputDevice') # use WASAPI default input 
        OutputDeviceID = p.get_host_api_info_by_index(i_api).get('defaultOutputDevice') # use WASAPI default output

        for i_dev in range(p.get_host_api_info_by_index(i_api)["deviceCount"]): # use DUMMY_DEV_NAME output device as virtual output

            dev_info = p.get_device_info_by_host_api_device_index(host_api_device_index= i_dev, host_api_index = i_api)
            print(dev_info["name"])
            if dev_info["name"] == DUMMY_DEV_NAME and dev_info["maxOutputChannels"] > 0:
                dummyOutputDeviceID = dev_info["index"]
                break
        else:
            raise RuntimeError(f"Cannot find specified dummy device: {DUMMY_DEV_NAME}")
        
        useloopback = True
        break
else:
    raise RuntimeError("No wasapi device available, thus not able to capture application/desktop audio")

# get input, output, virtual output device
input_device_info = p.get_device_info_by_index(InputDeviceID) # currently not used
output_device_info = p.get_device_info_by_index(OutputDeviceID)
dummy_output_device_info = p.get_device_info_by_index(dummyOutputDeviceID)
print(f"Use {dummy_output_device_info['name']} as virtual input")
print(f"Use {input_device_info['name']} as input")
print(f"Use {output_device_info['name']} as output")

# input device (not used)
stream_in = p.open( 
        format=pyaudio.paInt16,
        channels=CHANNEL_IN,
        rate = RATE,
        frames_per_buffer=CHUNK,
        input_device_index=input_device_info["index"],
        input = True,
        output = False,
    )

# virtual input device (used as input of signal processing)
stream_virtualout = p.open(    
        format=pyaudio.paInt16,
        channels=CHANNEL_OUT,
        rate=RATE,
        frames_per_buffer=CHUNK,
        input_device_index=dummy_output_device_info["index"], # use output device as input device by as_loopback=True
        input=True,
        as_loopback = useloopback,  
    )

# output device to give audio
stream_out = p.open(    
        format=pyaudio.paInt16,
        channels=CHANNEL_OUT,
        rate=RATE,
        frames_per_buffer=CHUNK,
        output_device_index=output_device_info["index"],
        input=False,
        output=True,
    )

### Loop ###
while stream_in.is_active() and stream_out.is_active() and stream_virtualout.is_active():
    # get audio
    input_buff = stream_virtualout.read(CHUNK)

    # process audio
    output_buff, RMS_history, Previous_gain = signal_proc_buff(input_buff, RMS_history, Previous_gain)
    
    # write audio
    stream_out.write(output_buff)

### End ###
stream_in.stop_stream()
stream_in.close() 
stream_out.stop_stream()
stream_out.close()
p.terminate()