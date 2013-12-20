######################################################################
# 
# File: bdata.py
# 
# Copyright 2013 Brian Beach, All Rights Reserved.
# 
######################################################################

"""
This module deals with the data structures I like to use in Python for
holding data.  I haven't looked at SciPy much yet, so theirs might be
better.

The goal of this module is to make it easy to do simple things with
these data structures, like display graphs of them.

STRUCTURE: Homogeneous list of dicts.

This structure is a list of dicts, where each dict contains exactly
the same keys.  You can think of it as a table, where each key is a
column, and each of the dicts is a row.

STRUCTURE: Columns
"""

import math
import unittest

def log2(x):
    return math.log(x) / math.log(2)

def in_range(x, low, high):
    return (low <= x) and (x <= high)

def round_up_to_nice(x):
    """
    Given a number, round it up to a 'nice' number that is 'close'.
    In this sense, a nice number is one with fewer significant digits,
    and close is within 10%.
    """
    below = math.pow(10, math.floor(math.log10(x)))
    increment = below
    result = below
    while not in_range(result / x, 0.9999, 1.1):
        if x < result:
            result = result - increment
            increment = increment / 10.0
        else:
            result += increment
    return result

def round_down_to_nice(x):
    """
    Given a number, round it down to a 'nice' number that is 'close'.
    In this sense, a nice number is one with fewer significant digits,
    and close is within 10%.
    """
    below = math.pow(10, math.floor(math.log10(x)))
    increment = below
    result = below
    while not in_range(result / x, 0.9, 1.0001):
        if result < x:
            result += increment
        else:
            result -= increment
            increment /= 10.0
    return result

def nearest(x, values):
    """
    Returns the value that in closest to x.  If there is a tie, the
    result is arbitrary.
    """
    result = values[0]
    for v in values:
        if abs(v - x) < abs(result - x):
            result = v
    return result

def round_to_nice(x):
    """
    Given a number, returns a 'nice' number that is near it.  The
    result could be less than or greater than x.
    """
    return nearest(x, [round_down_to_nice(x), round_up_to_nice(x)])

class TestUtilities(unittest.TestCase):

    def test_log2(self):
        self.assertAlmostEqual(10, log2(1024))

    def test_round_up_to_nice(self):
        self.assertAlmostEqual(90, round_up_to_nice(85))
        self.assertAlmostEqual(12, round_up_to_nice(11.8))
        self.assertAlmostEqual(0.8, round_up_to_nice(0.799))
        self.assertAlmostEqual(0.8, round_up_to_nice(0.8))
        
    def test_round_down_to_nice(self):
        self.assertAlmostEqual(80, round_down_to_nice(85))
        self.assertAlmostEqual(11, round_down_to_nice(11.8))
        self.assertAlmostEqual(0.8, round_down_to_nice(0.8))
        self.assertAlmostEqual(0.8, round_down_to_nice(0.801))

    def test_nearest(self):
        self.assertEqual(1, nearest(1.3, [1, 2, 3]))
        self.assertEqual(2, nearest(1.8, [1, 2, 3]))
        self.assertEqual(2, nearest(2.4, [1, 2, 3]))
        
    def round_to_nice(self):
        self.assertAlmostEqual(3.1, round_to_nice(math.pi))

def histogram_bins(values):
    """
    Given a list of values, returns:

        (lower_bound, bin_size, bin_count)
        
    It's guaranteed that:

        lower_bound <= min(values)
        max(values) <= lower_bound + bin_size * bin_count

    This function attempts to make lower_bound and bin_size be 'nice'
    values (with few significant digits), and to set bin_count near a
    'good' number for the number of values.
    """
    # This is Sturges's rule from: 
    # http://onlinestatbook.com/2/graphing_distributions/histograms.html
    low = min(values)
    high = max(values)
    target_bin_count = 1 + round(log2(len(values)))

    # Pick a lower bound
    lower_bound = round_down_to_nice(low)

    # Pick a nice bucket size
    bin_size = round_up_to_nice((high - lower_bound) / target_bin_count)
    print lower_bound, low, high, target_bin_count, (high - low) / target_bin_count, bin_size

    # Compute the bin count
    bin_count = int(math.ceil((high - lower_bound) / bin_size))

    assert lower_bound <= min(values)
    assert max(values) <= lower_bound + bin_size * bin_count
    return (lower_bound, bin_size, bin_count)

class TestHistogram(unittest.TestCase):

    def test_bins(self):
        (lb, bs, bc) = histogram_bins([1.2 + i/5.0 for i in range(16)])
        self.assertAlmostEqual(1.0, lb)
        self.assertAlmostEqual(0.6, bs)
        self.assertAlmostEqual(5, bc)

def histogram(values):
    # Find the bins
    (lower_bound, bin_size, bin_count) = histogram_bins(values)

    # Count the values in each bin
    counts = [0] * bin_count
    for v in values:
        i = int((v - lower_bound) / bin_size)
        counts[i] += 1

    # Show the results    
    for i in xrange(bin_count):
        print lower_bound + i * bin_size, lower_bound + (i+1) * bin_size, counts[i]

class Facet(object):

    def __init__(self, list_of_dicts, key):
        self.name = key
        self.values = [item[key] for item in each_dict(list_of_dicts)]

    def histogram(self):
        # How many buckets?  This 
        pass

if __name__ == '__main__':
    unittest.main()
