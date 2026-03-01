import gc
gc.enable()
print("Loading LighthouseMesh")
from dnet.signalling.LighthouseMesh import LighthouseMesh
print("loading Payload")
from dnet.signalling.Payload import Payload
gc.collect()

