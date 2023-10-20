#!/usr/bin/env python

import sys
import time
sys.path.append('sensel-api/sensel-lib-wrappers/sensel-lib-python')
import sensel
import redis
import binascii
import threading
import math

import overlay as o

DEBUG = False
OVERLAY = True

enter_pressed = False;
rc = redis.Redis()

LED_WIDTH = 100
LED_HEIGHT = 2

FLIP_X = True

INTERACTIVE_TIMEOUT=2
last_interactive = time.time() - INTERACTIVE_TIMEOUT

def waitForEnter():
    global enter_pressed
    input("Press Enter to exit...")
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
    global button_states
    global last_interactive
    x_padding = 0
    y_padding = 0
    if OVERLAY:
        x_padding = o.OVERLAY_X_PADDING
        y_padding = o.OVERLAY_X_PADDING

    x_ratio = (info.num_cols - x_padding * 2) / LED_WIDTH
    y_ratio = (info.num_rows - y_padding * 2) / LED_HEIGHT
    interactive = False

    if OVERLAY:
        button_dat, slider_dat, interactive = o.get_overlay_states(frame, info, DEBUG)

    # Mapping each morph "force pixel" to actual LEDs
    # For each LED:
    # Map a box of coordinates from the morph and take the averages of
    # their values to determine an led's force
    h = {}
    for i in range(LED_HEIGHT):
        h[i] = []
        for j in range(LED_WIDTH):
            if FLIP_X:
                xstart = int(math.floor((LED_WIDTH - j - 1) * x_ratio)) + x_padding
                xend = int(math.ceil((LED_WIDTH - j) * x_ratio)) + x_padding
            else:
                xstart = int(math.floor(j * x_ratio)) + x_padding
                xend = int(math.ceil((j + 1) * x_ratio)) + x_padding
            ystart = int(math.floor(i * y_ratio)) + y_padding
            yend = int(math.ceil((i + 1) * y_ratio)) + y_padding

            value = 0
            count = 0
            for x in range(xstart, min(xend, info.num_cols)):
                for y in range(ystart, min(yend, info.num_rows)):
                    value += frame.force_array[y * info.num_cols + x]
                    count += 1

            value = scale(value / count)
            if value > INTERACTIVE_TIMEOUT:
                interactive = True
            h[i].append(str(value))

        h[i] = ",".join(h[i])

    # set total force separately (cribbed from example)
    total_force = 0.0
    for n in range(info.num_rows * info.num_cols):
        total_force += frame.force_array[n]

    rc.hmset("morph", h)
    rc.set("morph_total_force", int(total_force))
    rc.set("buttons", button_dat)
    rc.set("sliders", slider_dat)
    if interactive:
        rc.set("interactive", "1")
        last_interactive = time.time()
    # Considered not interactive if not touched in 10 seconds
    elif time.time() - last_interactive > 10:
        rc.set("interactive", "0")


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

