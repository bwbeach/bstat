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

import itertools
import math
import unittest

def log2(x):
    return math.log(x) / math.log(2)

def in_range(x, low, high):
    return (low <= x) and (x <= high)

def round_up_to_nice(x, tolerance=None):
    """
    Given a number, round it up to a 'nice' number that is 'close'.
    In this sense, a nice number is one with fewer significant digits,
    and close is within +/- tolerance.
    """
    if tolerance is None:
        tolerance = abs(x / 10.0)
    quantum = math.pow(10, math.ceil(math.log10(tolerance)))
    for divisor in itertools.cycle([2, 5]):
        result = math.ceil(x / quantum) * quantum
        assert x <= result
        if result - x <= tolerance:
            return result
        quantum /= divisor

def round_down_to_nice(x, tolerance=None):
    """
    Given a number, round it down to a 'nice' number that is 'close'.
    In this sense, a nice number is one with fewer significant digits,
    and close is within 10%.
    """
    if tolerance is None:
        tolerance = abs(x / 10.0)
    assert 0 < tolerance
    quantum = math.pow(10, math.ceil(math.log10(tolerance)))
    for divisor in itertools.cycle([2, 5]):
        result = math.floor(x / quantum) * quantum
        assert result <= x
        if x - result <= tolerance:
            return result
        quantum /= divisor

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

def round_to_nice(x, tolerance=None):
    """
    Given a number, returns a 'nice' number that is near it.  The
    result could be less than or greater than x.
    """
    choices = [
        round_down_to_nice(x, tolerance),
        round_up_to_nice(x, tolerance)
        ]
    return nearest(x, choices)

class TestUtilities(unittest.TestCase):

    def test_log2(self):
        self.assertAlmostEqual(10, log2(1024))

    def test_round_up_to_nice(self):
        self.assertAlmostEqual(90, round_up_to_nice(85))
        self.assertAlmostEqual(12, round_up_to_nice(11.8))
        self.assertAlmostEqual(0.8, round_up_to_nice(0.799))
        self.assertAlmostEqual(0.8, round_up_to_nice(0.8))
        self.assertAlmostEqual(-1.0, round_up_to_nice(-1.1))
        self.assertAlmostEqual(-0.75, round_up_to_nice(-0.799))
        
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

class Histogram(object):

    def __init__(self, name, values):
        self.name = name
        self.values = values

        # Figure out the number of bins.
        # This is Sturges's rule from: 
        # http://onlinestatbook.com/2/graphing_distributions/histograms.html
        low = min(values)
        high = max(values)
        span = float(high - low)
        bin_count = 1 + round(log2(len(values)))

        # Start with a nice number in the middle, and work out from there.
        middle = round_to_nice((low + high) / 2.0, span / bin_count)

        # Pick a nice bin size, big enough to reach from the middle out to
        # both ends.
        biggest_side = max(middle - low, high - middle)
        bin_size = round_up_to_nice((biggest_side * 2.0) / bin_count)

        # Find the lower bound.  This works for both even and odd numbers
        # of bins.
        lower_bound = middle - bin_size * (bin_count / 2.0)

        # Compute the bin count
        bin_count = int(math.ceil((high - lower_bound) / bin_size))

        assert lower_bound <= min(values)
        assert max(values) <= lower_bound + bin_size * bin_count

        # Save the info
        self.lower_bound = lower_bound
        self.bin_size = bin_size
        self.bin_count = bin_count

        # Compute the bin boundaries, because they're handy
        self.bin_boundaries = [
            lower_bound + i * bin_size
            for i in xrange(bin_count + 1)
            ]

        # Count the values in each bin
        self.counts = [0] * bin_count
        for v in values:
            i = int((v - lower_bound) / bin_size)
            self.counts[i] += 1

    def __str__(self):
        # Figure out the scale-down factor (if needed) for an
        # 80-column display.
        scale = 1.0
        biggest_count = max(self.counts)
        if 70 < biggest_count:
            scale = round_up_to_nice(biggest_count / 70.0)

        # Build the display string.
        result = []
        result.append('#\n')
        result.append('# Histogram of %s:\n' % self.name)
        result.append('#\n')
        if scale != 1.0:
            result.append('# One star = %s\n' % scale)
            result.append('#\n')
        result.append('\n')
        for i in range(self.bin_count):
            result.append(str(self.bin_boundaries[i]))
            result.append('\n')
            result.append('    |')
            result.append('*' * int(round(self.counts[i] / scale)))
            result.append('\n')
        result.append(str(self.bin_boundaries[-1]))
        result.append('\n')
        return ''.join(result)

class TestHistogram(unittest.TestCase):

    def test_bins(self):
        h = Histogram('test', [1.2 + i/5.0 for i in range(16)])
        self.assertAlmostEqual(0.75, h.lower_bound)
        self.assertAlmostEqual(0.7, h.bin_size)
        self.assertAlmostEqual(5, h.bin_count)

class Facet(object):

    def __init__(self, list_of_dicts, key):
        self.name = key
        self.values = [item[key] for item in each_dict(list_of_dicts)]

    def histogram(self):
        # How many buckets?  This 
        pass

if __name__ == '__main__':
    unittest.main()
