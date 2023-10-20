import math
import redis
import time

rc = redis.Redis('localhost', charset="utf-8", decode_responses=True)

def fade_pixel(fade, layout, i, j):
    old = layout.get(i, j)
    if old != (0,0,0):
        layout.set(
            i, j,
            [math.floor(x * fade) for x in old]
        )

def interactive():
    return True
    #return rc.get("interactive") == "1"
