import redis
import time

rc = redis.Redis('localhost', charset="utf-8", decode_responses=True)

while True:
    h = rc.hgetall("morph")
    for i in range(len(h.keys())):
        v = h[str(i)]
        a = v.split(",")
        s = ""
        for i in a:
            if float(i) > 50:
                s += "+"
            else:
                s += "O"
        print(s)
    #print(h)
    time.sleep(0.25)
