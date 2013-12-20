import bdata
import random

values = [random.gauss(0, 1) for i in xrange(1000)]
h = bdata.Histogram('random', values)
print h
