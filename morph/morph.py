#!/usr/bin/env python

import sys
import time
sys.path.append('../sensel-api/sensel-lib-wrappers/sensel-lib-python')
import sensel
import redis
import binascii
import threading
import math

enter_pressed = False;
rc = redis.Redis()

LED_WIDTH = 6
LED_HEIGHT = 100

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


# converts force grams to a percentage 0-100
def scale(force):
    percent = min(100, force * 100 / 50)
    return int(percent)

def writeFrame(frame, info):
    global rc
    x_ratio = info.num_cols / LED_WIDTH
    y_ratio = info.num_rows / LED_HEIGHT

    key = "morph"
    h = {}
    # For each LED:
    # Map a box of coordinates from the morph and take the averages of
    # their values to determine an led's force
    for i in range(LED_HEIGHT):
        h[i] = []
        for j in range(LED_WIDTH):
            xstart = int(math.floor(j * x_ratio))
            xend = int(math.ceil((j + 1) * x_ratio))
            ystart = int(math.floor(i * y_ratio))
            yend = int(math.ceil((i + 1) * y_ratio))

            value = 0
            count = 0
            for x in range(xstart, min(xend, info.num_cols)):
                for y in range(ystart, min(yend, info.num_rows)):
                    value += frame.force_array[y * info.num_cols + x]
                    count += 1

            value /= count
            h[i].append(str(scale(value)))

        h[i] = ",".join(h[i])

    rc.hmset("morph", h)


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

