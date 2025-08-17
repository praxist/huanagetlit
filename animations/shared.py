import math
import redis
import time

# Create a Redis client compatible with redis-py >=4.x.
# The 'charset' kwarg was removed; default encoding is utf-8.
rc = redis.Redis(host="localhost", decode_responses=True)

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
