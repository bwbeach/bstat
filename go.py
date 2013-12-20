import bdata
import random

def show_histogram():
    values = [random.gauss(0, 1) for i in xrange(1000)]
    h = bdata.Histogram('random', values)
    print h

def show_table():
    def make_item():
        return {
            'alfa' : random.randint(0, 100000),
            'bravo' : random.random(),
            'charlie' : 'a' * random.randint(1, 10),
            'delta' : pow(10.0, 2 * random.random())
            }
    data = [make_item() for i in xrange(10)]
    t = bdata.Table(data, sorted(data[0].keys()), 'delta')
    print t

show_table()

