# Does not work yet

class MorphClient:
    def __init__(self, redis, width, height, namespace="morph"):
        self.namespace = namespace
        self.rc = redis.Redis('localhost', charset="utf-8", decode_responses=True)
        self.width = width
        self.height = height

        # some error checking for matching width, height
        w =  self.rc.get(namespace + "/width")
        h =  self.rc.get(namespace + "/height")
        if w != self.width:
            pass
        if h != self.height:
            pass

        self.force_array = []
        for i in range(self.width):
            self.force_array.append([])
            for j in range(self.height):
                self.force_array[i].append(0)


    def get_events(self):
        pass
        # trackpad activity, button press, button hold, button release

    def get_forces(self):
        h = self.rc.hgetall(namespace + "/forces")
        for i in range(self.height):
            v = h[str(i)]
            a = v.split(",")
            for j in range(self.width):
                self.force_array[j][i] = int(a[j])
        return self.force_array
