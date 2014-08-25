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

class AutoBins(object):

    """
    Given a set of values, figures out a reasonable number of bins for
    a histogram over those values.  An attempt is made to make the
    bucket boundaries be nice round numbers.
    """

    def __init__(self, values, bin_count=None):
        # Figure out the number of bins.
        # This is Sturges's rule from: 
        # http://onlinestatbook.com/2/graphing_distributions/histograms.html
        low = min(values)
        high = max(values)
        span = float(high - low)
        if bin_count is None:
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

        # Compute the bin boundaries, because they're handy
        bin_boundaries = [
            lower_bound + i * bin_size
            for i in xrange(bin_count + 1)
            ]

        # Should we switch to logarithmic?  If more than half the
        # values are NOT in the first bin, then we're good.
        number_in_first_bucket = len([
            value 
            for value in values
            if value < bin_boundaries[1]
            ])
        self.logarithmic = (
            0 < min(values) and
            (len(values) / 2 < number_in_first_bucket)
            )
        if not self.logarithmic:
            self.lower_bound = lower_bound
            self.bin_size = bin_size
            self.bin_count = bin_count
            self.bin_boundaries = bin_boundaries
            return

        # Now we'll re-do the bucketization for the logarithmic case.
        lower_bound = round_down_to_nice(min(values))
        upper_bound = max(values)

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

    def test_logrithmic(self):
        values = [1.1 ** i for i in range(100)]
        bins = AutoBins(values)
        self.assertEqual(True, bins.is_logarithmic())
        self.assertAlmostEqual(1, bins.get_bin_boundaries()[0])
        self.assertAlmostEqual(3.5, bins.get_bin_boundaries()[1])

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
