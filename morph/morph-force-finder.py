#!/usr/bin/env python

import sys
import time
sys.path.append('../sensel-api/sensel-lib-wrappers/sensel-lib-python')
import sensel
import binascii
import threading
import math

enter_pressed = False;

def waitForEnter():
    global enter_pressed
    raw_input("Press Enter to exit...")
    enter_pressed = True
    return

def openSensel():
    handle = None
    (error, device_list) = sensel.getDeviceList()
    if device_list.num_devices != 0:
        (error, handle) = sensel.openDeviceByID(device_list.devices[0].idx)
    return handle

def initFrame():
    error = sensel.setFrameContent(handle, sensel.FRAME_CONTENT_PRESSURE_MASK)
    (error, frame) = sensel.allocateFrameData(handle)
    error = sensel.startScanning(handle)
    return frame

def scanFrames(frame, info):
    error = sensel.readSensor(handle)
    (error, num_frames) = sensel.getNumAvailableFrames(handle)
    for i in range(num_frames):
        error = sensel.getFrame(handle, frame)
        writeFrame(frame, info)

def writeFrame(frame, info):
    m = 0
    xmax = 0
    ymax = 0
    for x in range(info.num_cols):
        for y in range(info.num_rows):
            f = frame.force_array[y * info.num_cols + x]
            if f > m:
                xmax = x
                ymax = y
                m = f
    print("X: %s, Y: %s, F: %s" % (xmax, ymax, m))

def closeSensel(frame):
    error = sensel.freeFrameData(handle, frame)
    error = sensel.stopScanning(handle)
    error = sensel.close(handle)

if __name__ == "__main__":
    handle = openSensel()
    if handle != None:
        (error, info) = sensel.getSensorInfo(handle)
        print(info.num_rows)
        print(info.num_cols)
        frame = initFrame()

        t = threading.Thread(target=waitForEnter)
        t.start()
        while(enter_pressed == False):
            scanFrames(frame, info)
            time.sleep(0.01)
        closeSensel(frame)
