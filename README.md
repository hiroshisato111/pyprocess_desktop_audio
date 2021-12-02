# Process windows desktop audio
This tool processes stream from an output device and write to another output device by utilizing loopback mode of Windows WASAPI.
Especially, this imprementation includes compression of audio, that makes volume uniform by compressing only loud sound and do nothing for small sound.

## Requirements
- Windows Vista and above (for utilizing WASAPI). But only checked with Windows10
- python=3.7
- custom build pyaudio available at https://github.com/intxcc/pyaudio_portaudio/releases
    - This is required to use "as_loopback" option to get output stream as input.
    - direct download from: https://github.com/intxcc/pyaudio_portaudio/releases/download/1.1.1/PyAudio-0.2.11-cp37-cp37m-win_amd64.whl

## How to use
- Setup environment
    - setup python37 for Windows
    - `$ pip install PyAudio-0.2.11-cp37-cp37m-win_amd64.whl`
- Set `DUMMY_DEV_NAME` in `windows_sound_input.py`
    - The list of device names is available by executing `windows_sound_input.py` with `DUMMY_DEV_NAME = ""`
- Specify audio output device of some application (ex. zoom) as you set for `DUMMY_DEV_NAME`
- The processed sound will be output from your default output device (that must be different from `DUMMY_DEV_NAME`)

## limitation
- An audio device for "output" and "virtual output" must be different.
    - output: The device from which you actually listen to sound
    - virtual output: The device into which the application outputs audio.
        - The audio given to the "virtual output" (from some application or windows) is processed and then given to the "output" device.
- another solution
    - use windows audio mixer as input device
    - use loopback software: https://stackoverflow.com/questions/23295920/loopback-what-u-hear-recording-in-python-using-pyaudio

## references
- https://stackoverflow.com/questions/26573556/record-speakers-output-with-pyaudio
- https://www.ipride.co.jp/blog/2525
- https://apc.hatenablog.jp/entry/20180517
- https://github.com/intxcc/pyaudio_portaudio