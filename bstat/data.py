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

from collections import Counter

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
    if x == 0:
        return 0
    if tolerance is None:
        tolerance = abs(x / 10.0)
    if tolerance == 0:
        return x
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
    if x == 0:
        return 0
    if tolerance is None:
        tolerance = abs(x / 10.0)
    if tolerance == 0:
        return x
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
        self.assertAlmostEqual(0, round_down_to_nice(0))
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

class AutoBins(object):

    """
    Given a set of values, figures out a reasonable number of bins for
    a histogram over those values.  An attempt is made to make the
    bucket boundaries be nice round numbers.

    You can initialize this class with either a list of values, like
    this:

        [0, 1, 5, 7, 1, 4, 2, 2, 2, 2, 2]

    Or, if you have already summarized your data by counting the
    values, you can initialize it with a list of value_and_count
    pairs.  This is equivalent to the one above:

        [(0, 1), (1, 2), (2, 5), (4, 1), (5, 1), (6,1)]
    """

    def __init__(self, values=None, values_and_counts=None, bin_count=None):
        # Check arguments
        if (values is None) and (values_and_counts is None):
            raise ValueError('Either values or values an counts should be set')
        if (values is not None) and (values_and_counts is not None):
            raise ValueError('Only one of values or values_and_counts should be set')

        # Make sure that both values and values_and_counts are set
        if values_and_counts is None:
            values_and_counts = [(v, c) for (v, c) in Counter(values).iteritems()]
        values = set(v for (v,c) in values_and_counts)
        total_count = sum(c for (v,c) in values_and_counts)

        # With a single value, it's a degenerate case.
        if len(values) == 1:
            value = values_and_counts[0][0]
            self.lower_bound = value
            self.bin_size = 0
            self.bin_count = 1
            self.bin_boundaries = [value, value]
            self.logarithmic = False
            return

        # Figure out the number of bins.
        # This is Sturges's rule from: 
        # http://onlinestatbook.com/2/graphing_distributions/histograms.html
        low = min(values)
        high = max(values)
        span = float(high - low)
        if bin_count is None:
            bin_count = 1 + round(log2(total_count))

        # Start with a nice number in the middle, and work out from there.
        middle = round_to_nice((low + high) / 2.0, span / bin_count)

        # Pick a nice bin size, big enough to reach from the middle out to
        # both ends.
        biggest_side = max(middle - low, high - middle)
        bin_size = round_up_to_nice((biggest_side * 2.0) / bin_count)

        # Find the lower bound.  This works for both even and odd numbers
        # of bins.
        lower_bound = middle - bin_size * (bin_count / 2.0)

        # Special case for all-positive values.  In this case, we
        # don't want a lower bound that's negative because it looks
        # weird.
        if lower_bound < 0 and 0 <= low:
            lower_bound = 0

        # Compute the bin count
        bin_count = int(math.ceil((high - lower_bound) / bin_size))

        assert lower_bound <= low
        assert high <= lower_bound + bin_size * bin_count

        # Compute the bin boundaries, because they're handy
        bin_boundaries = [
            lower_bound + i * bin_size
            for i in xrange(bin_count + 1)
            ]

        # Should we switch to logarithmic?  If more than half the
        # values are NOT in the first bin, then we're good.
        number_in_first_bucket = sum(
            c
            for (v,c) in values_and_counts
            if v < bin_boundaries[1]
            )
        self.logarithmic = (
            0 < low and
            (total_count / 2 < number_in_first_bucket)
            )
        if not self.logarithmic:
            self.lower_bound = lower_bound
            self.bin_size = bin_size
            self.bin_count = bin_count
            self.bin_boundaries = bin_boundaries
            return

        # Now we'll re-do the bucketization for the logarithmic case.
        lower_bound = round_down_to_nice(low)
        upper_bound = high

        # If b is the bin count, then we want the b-th root of the
        # difference between the lower and upper bounds to be the 
        # growth factor between buckets.
        b = bin_count
        total_growth = float(upper_bound) / float(lower_bound)
        bucket_exponent = round_up_to_nice(total_growth ** (1.0 / b))
        
        self.lower_bound = lower_bound
        self.bin_count = bin_count
        self.bin_boundaries = [
            round_up_to_nice(lower_bound * (bucket_exponent ** i))
            for i in xrange(bin_count + 1)
            ]

    def is_logarithmic(self):
        return self.logarithmic
    
    def get_bin_count(self):
        return self.bin_count

    def get_bin_boundaries(self):
        """
        Returns one more number than the bin count.  The bins are the
        ranges between adjacent numbers in the list.
        """
        return self.bin_boundaries

    def get_bin_index_for_value(self, value):
        for i in xrange(self.bin_count):
            if value < self.bin_boundaries[i+1]:
                return i
        return self.bin_count - 1

    def __str__(self):
        return "<bins %s>" % (", ".join(str(b) for b in self.bin_boundaries))
    
class TestAutoBins(unittest.TestCase):

    def test_single_value(self):
        bins = AutoBins([1])
        self.assertEqual([1, 1], bins.get_bin_boundaries())
    
    def test_linear(self):
        bins = AutoBins([1.2 + i/5.0 for i in range(16)])
        self.assertAlmostEqual(0.75, bins.get_bin_boundaries()[0])
        self.assertAlmostEqual(1.45, bins.get_bin_boundaries()[1])
        self.assertAlmostEqual(5, bins.get_bin_count())

    def test_manual_bin_count(self):
        bins = AutoBins([1.2 + i/5.0 for i in range(16)], bin_count=4)
        self.assertAlmostEqual(1.2, bins.get_bin_boundaries()[0])
        self.assertAlmostEqual(2.1, bins.get_bin_boundaries()[1])
        self.assertAlmostEqual(4, bins.get_bin_count())

    def test_logarithmic(self):
        values = [1.1 ** i for i in range(100)]
        bins = AutoBins(values)
        self.assertEqual(True, bins.is_logarithmic())
        self.assertAlmostEqual(1, bins.get_bin_boundaries()[0])
        self.assertAlmostEqual(4.0, bins.get_bin_boundaries()[1])

    def test_regress_1(self):
        values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
        15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
        30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44,
        45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
        60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74,
        75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89,
        90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 110, 120, 130,
        140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250,
        260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370,
        380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490,
        500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600, 610,
        620, 630, 640, 650, 660, 670, 680, 690, 700, 710, 720, 730,
        740, 750, 760, 770, 780, 790, 800, 810, 820, 830, 840, 850,
        860, 870, 880, 890, 900, 910, 920, 930, 940, 950, 960, 970,
        980, 990, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700,
        1800, 1900, 2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700,
        2800, 2900, 3000, 3100, 3200, 3300, 3400, 3500, 3600, 3700,
        3800, 3900, 4000, 4100, 4200, 4300, 4400, 4500, 4600, 4700,
        4800, 4900, 5000, 5100, 5200, 5300, 5400, 5500, 5600, 5700,
        5800, 5900, 6000, 6100, 6200, 6300, 6400, 6600, 6700, 6800,
        6900, 7000, 7100, 7200, 7300, 7400, 7500, 7600, 7700, 7800,
        7900, 8000, 8100, 8200, 8300, 8400, 8500, 8600, 8700, 8800,
        8900, 9000, 9100, 9300, 9400, 9500, 9600, 9700, 10000, 11000,
        12000, 13000, 14000, 15000, 16000, 17000, 18000, 19000, 20000,
        21000, 22000, 23000, 24000, 25000, 26000, 27000, 28000, 29000,
        30000, 31000, 32000, 33000, 34000, 35000, 36000, 37000, 38000,
        39000, 40000, 41000, 42000, 43000, 44000, 45000, 46000, 47000,
        48000, 49000, 50000, 51000, 52000, 53000, 54000, 55000, 56000,
        57000, 58000, 59000, 60000, 61000, 62000, 63000, 64000, 65000,
        66000, 67000, 68000, 69000, 70000, 71000, 72000, 73000, 74000,
        75000, 76000, 77000, 78000, 79000, 80000, 81000, 82000, 83000,
        84000, 85000, 86000, 87000, 88000, 89000, 90000, 91000, 92000,
        93000, 94000, 95000, 96000, 97000, 98000, 99000, 100000,
        110000, 120000, 130000, 140000, 150000, 160000, 170000,
        180000, 190000, 200000, 210000, 220000, 230000, 240000,
        250000, 260000, 270000, 280000, 290000, 300000, 310000,
        320000, 330000, 340000, 350000, 360000, 370000, 380000,
        390000, 400000, 410000, 420000, 430000, 440000, 450000,
        460000, 470000, 480000, 490000, 500000, 510000, 520000,
        530000, 540000, 550000, 560000, 570000, 580000, 590000,
        600000, 610000, 620000, 630000, 640000, 650000, 660000,
        670000, 680000, 690000, 700000, 710000, 720000, 730000,
        740000, 750000, 760000, 770000, 780000, 790000, 800000,
        810000, 820000, 830000, 840000, 850000, 860000, 870000,
        880000, 890000, 900000, 910000, 920000, 930000, 940000,
        950000, 960000, 970000, 980000, 990000, 1000000, 1100000,
        1200000, 1300000, 1400000, 1500000, 1600000, 1700000, 1800000,
        1900000, 2000000, 2100000, 2200000, 2300000, 2400000, 2500000,
        2600000, 2700000, 2800000, 2900000, 3000000, 3100000, 3200000,
        3300000, 3400000, 3500000, 3600000, 3700000, 3800000, 3900000,
        4000000, 4100000, 4200000, 4300000, 4400000, 4500000, 4600000,
        4700000, 4800000, 4900000, 5000000, 5100000, 5200000, 5300000,
        5400000, 5500000, 5600000, 5700000, 5800000, 5900000, 6000000,
        6100000, 6200000, 6300000, 6400000, 6500000, 6600000, 6700000,
        6800000, 6900000, 7000000, 7100000, 7200000, 7300000, 7400000,
        7500000, 7600000, 7700000, 7800000, 7900000, 8000000, 8100000,
        8200000, 8300000, 8400000, 8500000, 8600000, 8700000, 8800000,
        8900000, 9000000, 9100000, 9200000, 9300000, 9400000, 9500000,
        9600000, 9700000, 9800000, 9900000, 10000000, 11000000,
        12000000, 13000000, 14000000, 15000000, 16000000, 17000000,
        18000000, 19000000, 20000000, 21000000, 22000000, 23000000,
        24000000, 25000000, 26000000, 27000000, 28000000, 29000000,
        30000000, 31000000, 32000000, 33000000, 34000000, 35000000,
        36000000, 37000000, 38000000, 39000000, 40000000, 41000000,
        42000000, 43000000, 44000000, 45000000, 46000000, 47000000,
        48000000, 49000000, 50000000, 51000000, 52000000, 53000000,
        54000000, 55000000, 56000000, 57000000, 58000000, 59000000,
        60000000, 61000000, 62000000, 63000000, 64000000, 65000000,
        66000000, 67000000, 68000000, 69000000, 70000000, 71000000,
        72000000, 73000000, 74000000, 75000000, 76000000, 77000000,
        78000000, 79000000, 80000000, 81000000, 82000000, 83000000,
        84000000, 85000000, 86000000, 87000000, 88000000, 89000000,
        90000000, 91000000, 92000000, 93000000, 94000000, 95000000,
        96000000, 97000000, 98000000, 99000000, 100000000, 110000000,
        120000000, 130000000, 140000000, 150000000, 160000000,
        170000000, 180000000, 190000000, 200000000, 210000000,
        220000000, 230000000, 240000000, 250000000, 260000000,
        270000000, 280000000, 290000000, 300000000, 310000000,
        320000000, 330000000, 340000000, 350000000, 360000000,
        370000000, 380000000, 390000000, 400000000, 410000000,
        420000000, 430000000, 440000000, 450000000, 460000000,
        470000000, 480000000, 490000000, 500000000, 510000000,
        520000000, 530000000, 540000000, 550000000, 560000000,
        570000000, 580000000, 590000000, 600000000, 610000000,
        620000000, 630000000, 640000000, 650000000, 660000000,
        670000000, 680000000, 690000000, 700000000, 710000000,
        720000000, 730000000, 740000000, 750000000, 760000000,
        770000000, 780000000, 790000000, 800000000, 810000000,
        820000000, 830000000, 840000000, 850000000, 860000000,
        870000000, 880000000, 890000000, 900000000, 920000000,
        930000000, 940000000, 950000000, 960000000, 970000000,
        980000000, 990000000, 1000000000, 1100000000, 1200000000,
        1300000000, 1400000000, 1500000000, 1600000000, 1700000000,
        1800000000, 1900000000, 2000000000, 2100000000, 2200000000,
        2300000000, 2400000000, 2500000000, 2600000000, 2900000000,
        3000000000, 4300000000, 180000000000, 6600000000000]
        bins = AutoBins(values, bin_count=8)
        self.assertLessEqual(0, bins.get_bin_boundaries()[0])

    def test_regress_2(self):
        values_and_counts = [(1, 6221), (2, 1310), (3,
        801), (4, 876), (5, 434), (6, 285), (7, 47), (8, 304), (9,
        143), (10, 52), (11, 93), (12, 256), (13, 223), (14, 63), (15,
        133), (16, 71), (17, 153), (18, 76), (19, 49), (20, 124), (21,
        87), (22, 36), (23, 13), (24, 73), (25, 44), (26, 53), (27,
        76), (28, 73), (29, 36), (30, 28), (31, 47), (32, 10), (33,
        9), (34, 16), (35, 47), (36, 109), (37, 51), (38, 54), (39,
        2), (40, 5), (41, 101), (42, 18), (43, 28), (44, 30), (45,
        11), (46, 43), (47, 36), (48, 10), (49, 15), (50, 21), (51,
        115), (52, 49), (53, 52), (54, 31), (55, 42), (56, 50), (57,
        29), (58, 174), (59, 24), (60, 11), (61, 9), (62, 22), (63,
        7), (64, 5), (65, 9), (66, 22), (67, 19), (68, 22), (69, 81),
        (70, 11), (71, 14), (72, 10), (73, 9), (74, 33), (75, 8), (76,
        26), (77, 9), (78, 13), (79, 11), (80, 7), (81, 15), (82, 23),
        (83, 8), (84, 18), (85, 25), (86, 39), (87, 10), (88, 34),
        (89, 7), (90, 10), (91, 11), (92, 17), (93, 18), (94, 7), (95,
        10), (96, 13), (97, 34), (98, 19), (99, 15), (100, 122), (110,
        132), (120, 264), (130, 241), (140, 189), (150, 183), (160,
        162), (170, 61), (180, 74), (190, 75), (200, 81), (210, 86),
        (220, 54), (230, 33), (240, 36), (250, 131), (260, 53), (270,
        103), (280, 106), (290, 33), (300, 31), (310, 42), (320, 33),
        (330, 29), (340, 19), (350, 9), (360, 5), (370, 6), (380, 11),
        (390, 13), (400, 15), (410, 13), (420, 17), (430, 43), (440,
        53), (450, 33), (460, 41), (470, 41), (480, 40), (490, 33),
        (500, 34), (510, 35), (520, 39), (530, 54), (540, 79), (550,
        74), (560, 22), (570, 15), (580, 12), (590, 15), (600, 22),
        (610, 13), (620, 19), (630, 16), (640, 17), (650, 15), (660,
        21), (670, 20), (680, 22), (690, 19), (700, 27), (710, 55),
        (720, 48), (730, 19), (740, 16), (750, 12), (760, 12), (770,
        11), (780, 11), (790, 14), (800, 15), (810, 15), (820, 14),
        (830, 13), (840, 15), (850, 17), (860, 17), (870, 16), (880,
        22), (890, 26), (900, 21), (910, 28), (920, 25), (930, 31),
        (940, 34), (950, 31), (960, 27), (970, 27), (980, 11), (990,
        11), (1000, 65), (1100, 151), (1200, 193), (1300, 175), (1400,
        185), (1500, 133), (1600, 94), (1700, 121), (1800, 64), (1900,
        45), (2000, 12), (2100, 11), (2200, 8), (2300, 10), (2400, 6),
        (2500, 8), (2600, 5), (2700, 8), (2800, 7), (2900, 7), (3000,
        6), (3100, 9), (3200, 9), (3300, 3), (3400, 10), (3500, 6),
        (3600, 6), (3700, 9), (3800, 5), (3900, 7), (4000, 6), (4100,
        9), (4200, 3), (4300, 8), (4400, 5), (4500, 8), (4600, 4),
        (4700, 5), (4800, 6), (4900, 3), (5000, 5), (5100, 4), (5200,
        2), (5300, 5), (5400, 2), (5500, 3), (5600, 6), (5700, 1),
        (5800, 4), (5900, 4), (6000, 3), (6100, 4), (6200, 5), (6300,
        1), (6400, 4), (6500, 4), (6600, 2), (6700, 4), (6800, 2),
        (6900, 4), (7000, 3), (7100, 4), (7200, 4), (7300, 4), (7400,
        3), (7500, 4), (7600, 2), (7700, 3), (7800, 5), (7900, 2),
        (8000, 2), (8100, 3), (8200, 3), (8300, 3), (8400, 3), (8500,
        4), (8600, 3), (8700, 1), (8800, 3), (8900, 3), (9000, 2),
        (9100, 2), (9200, 3), (9300, 2), (9400, 3), (9500, 2), (9600,
        2), (9700, 2), (9800, 3), (9900, 2), (10000, 11), (11000, 19),
        (12000, 16), (13000, 14), (14000, 14), (15000, 11), (16000,
        6), (17000, 6), (18000, 7), (19000, 7), (20000, 6), (21000,
        3), (370000, 15)]
        bins = AutoBins(values_and_counts=values_and_counts)
        self.assertTrue(bins.is_logarithmic())

class Histogram(object):

    def __init__(self, name, values):
        self.name = name
        self.values = values
        self.bins = AutoBins(values)

        # Count the values in each bin
        bin_count = self.bins.get_bin_count()
        self.counts = [0] * bin_count
        for v in values:
            bin_index = self.bins.get_bin_index_for_value(v)
            self.counts[bin_index] += 1

    def __str__(self):
        # Figure out the scale-down factor (if needed) for an
        # 80-column display.  Leaving 5 on the left (for spaces and
        # the axis) and 5 on the right (for good measure), that leaves
        # room for 70 stars.
        scale = 1.0
        biggest_count = max(self.counts)
        if 70 < biggest_count:
            scale = round_up_to_nice(biggest_count / 70.0)

        # get some info
        bin_count = self.bins.get_bin_count()
        bin_boundaries = self.bins.get_bin_boundaries()

        # Build the display string.
        result = []
        result.append('#\n')
        result.append('# Histogram of %s:\n' % self.name)
        result.append('#\n')
        if scale != 1.0:
            result.append('# One star = %s\n' % scale)
            result.append('#\n')
        result.append('\n')
        for i in range(bin_count):
            result.append(str(bin_boundaries[i]))
            result.append('\n')
            result.append('    |')
            result.append('*' * int(round(self.counts[i] / scale)))
            result.append('\n')
        result.append(str(bin_boundaries[-1]))
        result.append('\n')
        return ''.join(result)

class TestHistogram(unittest.TestCase):

    def test_regress_1(self):
        # The outlier value was ending up outside the range of all of
        # the bins.
        h = Histogram('test', [28, 27, 27, 24, 27, 24, 28, 27, 26,
                               27, 28, 25, 25, 27, 24, 28, 27, 25, 
                               24, 26, 26, 24, 26, 25, 27, 35, 26, 
                               25, 27, 27, 28, 27, 28, 27, 26, 27,
                               24, 24, 25, 27, 27, 25, 24, 27, 25])

def is_number(x):
    return isinstance(x, float) or isinstance(x, int)

def make_formatter(values):
    """
    Returns a function that can be used to format the values in the
    list.  Picks a reasonable number of digits of accuracy.
    """
    # Get the ranges of the values.
    max_string_length = 0
    biggest_abs = 0
    all_numbers_ints = True
    any_numbers = False
    for v in values:
        if isinstance(v, basestring):
            max_string_length = max(max_string_length, len(v))
        elif is_number(v):
            any_numbers = True
            biggest_abs = max(biggest_abs, abs(v))
            if v != int(v):
                all_numbers_ints = False
        else:
            max_string_length = max(max_string_length, len(str(v)))

    # Make a format string for string values
    if any_numbers:
        string_format = '%%%ds' % max_string_length
    else:
        string_format = '%%-%ds' % max_string_length

    # Make a format string for numeric values.
    if biggest_abs < 1.0:
        left_of_decimal = 1
    else:
        left_of_decimal = int(2 + math.floor(math.log10(biggest_abs)))
    if all_numbers_ints:
        right_of_decimal = 0
    else:
        right_of_decimal = max(0, 5 - left_of_decimal)
    total_size = 2 + left_of_decimal + right_of_decimal
    number_format = '%%%d.%df' % (total_size, right_of_decimal)

    # Make the format function
    def formatter(v):
        if isinstance(v, basestring):
            return string_format % v
        elif is_number(v):
            return number_format % v
        else:
            return string_format % str(v)
    return formatter

class Table(object):

    """
    Knows how to display a table of data.

    The data is in the form of a list of dicts:
        [ { 'a' : 4, 'b' : 8 },
          { 'a' : 5, 'b' : 9 } ]
    """

    def __init__(self, data, column_names=None, sort_key=None, reverse=False,
                 default_value=None, formatters=None, titles=None):

        if formatters is None:
            formatters = {}
        
        if column_names is None:
            column_names = sorted(data[0].keys())

        if sort_key is None:
            self.data = data
        else:
            self.data = sorted(data, key=(lambda item: item[sort_key]), reverse=reverse)
        self.column_names = column_names
        self.default_value = default_value
        self.formatters = [
            self._make_formatter(col, formatters)
            for col in column_names
            ]
        
        if titles is None:
            titles = {}
        self.column_titles = [
            titles.get(column_name, column_name)
            for column_name in column_names
            ]
        
        first_values = [data[0].get(col, self.default_value) for col in column_names]
        first_row = [
            formatter(v)
            for (formatter, v) in zip(self.formatters, first_values)
            ]
        self.column_widths = [
            max(len(col), len(val))
            for (col, val) in zip(self.column_titles, first_row)
            ]

    def _make_formatter(self, column_name, explicit_formatters):
        if column_name in explicit_formatters:
            formatter = explicit_formatters[column_name]
            if isinstance(formatter, basestring):
                def format_string(v):
                    return formatter % v
                return format_string
            else:
                return formatter
        else:
            values = [item.get(column_name, self.default_value) 
                      for item in self.data]
            return make_formatter(values)

    def __str__(self):
        result = []

        # Title row
        total_width = 1 + sum(3 + w for w in self.column_widths)
        result.append('|')
        result.append('=' * (total_width - 2))
        result.append('|')
        result.append('\n')
        result.append('| ')
        for (col, w) in zip(self.column_titles, self.column_widths):
            result.append(self.pad(col, w))
            result.append(' | ')
        result.append('\n')
        result.append('|')
        result.append('-' * (total_width - 2))
        result.append('|')
        result.append('\n')

        # Data rows
        for item in self.data:
            result.append('| ')
            for (col, formatter, w) in zip(self.column_names, self.formatters, self.column_widths):
                result.append(self.pad(formatter(item.get(col, self.default_value)), w))
                result.append(' | ')
            result.append('\n')
        result.append('|')
        result.append('=' * (total_width - 2))
        result.append('|')
        result.append('\n')

        return ''.join(result)

    def csv(self):
        result = []
        result.append(','.join(self.column_titles))
        for item in self.data:
            result.append(','.join(
                formatter(item.get(col, self.default_value)).strip()
                for (col, formatter) in zip(self.column_names, self.formatters)
                ))
        return '\n'.join(result) + '\n'

    def html(self):
        result = []
        result.append('<table>')
        result.append('  <tbody>')
        result.append('    <tr>')
        for col in self.column_titles:
            result.append('      <th>%s</th>' % col)
        result.append('    </tr>')
        for item in self.data:
            result.append('    <tr>')
            for (col, formatter) in zip(self.column_names, self.formatters):
                value = formatter(item.get(col, self.default_value)).strip()
                result.append('      <td>%s</td>' % value)
            result.append('    </tr>')
        result.append('  <tbody>')
        result.append('</table>')
        return '\n'.join(result) + '\n'
        
    def pad(self, s, width):
        if len(s) < width:
            return (' ' * (width - len(s))) + s
        else:
            return s[:width]

class TestTable(unittest.TestCase):

    def test_formatter(self):
        data = [ { 'a' : 1, 'b' : 2, 'c' : 3 } ]
        table = Table(data, formatters={'b' : '%02d', 'c' : (lambda x : 'n')})
        self.assertEqual(
            '|===============|\n' +
            '|    a |  b | c | \n' +
            '|---------------|\n' +
            '|    1 | 02 | n | \n' +
            '|===============|\n',
            str(table)
            )

    def test_titles(self):
        data = [ { 'a' : 1, 'b' : 2, 'c' : 3 } ]
        table = Table(data, titles={'a':'A', 'c':'foo'})
        self.assertEqual(
            '|====================|\n' +
            '|    A |    b |  foo | \n' +
            '|--------------------|\n' +
            '|    1 |    2 |    3 | \n' +
            '|====================|\n',
            str(table)
            )

    def test_html(self):
        data = [ { 'a' : 1, 'b' : 2 }, { 'a' : 3, 'b' : 4 } ]
        table = Table(data)
        self.assertEqual(
            '<table>\n' +
            '  <tbody>\n' +
            '    <tr>\n' + 
            '      <th>a</th>\n' +
            '      <th>b</th>\n' +
            '    </tr>\n' +
            '    <tr>\n' +
            '      <td>1</td>\n' +
            '      <td>2</td>\n' +
            '    </tr>\n' +
            '    <tr>\n' +
            '      <td>3</td>\n' + 
            '      <td>4</td>\n' + 
            '    </tr>\n' + 
            '  <tbody>\n' +
            '</table>\n',
            table.html()
            )

class Facet(object):

    def __init__(self, list_of_dicts, key):
        self.name = key
        self.values = [item[key] for item in each_dict(list_of_dicts)]

    def histogram(self):
        # How many buckets?  This 
        pass

if __name__ == '__main__':
    unittest.main()
