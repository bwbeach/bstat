######################################################################
# 
# File: bstat.py
# 
# Copyright 2013 Brian Beach, All Rights Reserved.
# 
######################################################################

import itertools
import math
import scipy.stats
import unittest

def percentile(v, p):
    v = sorted(v)
    position = (p / 100.0) * (len(v) - 1)
    index = int(position)
    next_index = min(index + 1, len(v) - 1)
    return v[index] * (next_index - position) + v[next_index] * (position - index)

def trimean(v):
    return (percentile(v, 25) + 2 * percentile(v, 50) + percentile(v, 75)) / 4.0

def mean(v):
    return float(sum(v)) / float(len(v))

def sum_of_squares(v):
    return sum(x * x for x in v)

def standard_deviation(v):
    m = mean(v)
    variance = sum_of_squares(x - m for x in v) / (len(v) - 1.0)
    return math.sqrt(variance)

def interquartile_range(v):
    q25 = percentile(v, 25)
    q75 = percentile(v, 75)
    return q75 - q25

def group_pairs(seq):
    for (i, x) in enumerate(seq):
        if i % 2 == 0:
            prev = x
        else:
            yield (prev, x)

def unzip(pairs):
    return zip(*pairs) # not very efficient

def deviations(v):
    m = mean(v)
    return [x - m for x in v]

def dot_product(x, y):
    assert len(x) == len(y)
    return sum(a * b for (a, b) in zip(x, y))

def correlation_coefficient(X, Y):
    x = deviations(X)
    y = deviations(Y)
    x_squares = sum_of_squares(x)
    y_squares = sum_of_squares(y)
    return dot_product(x, y) / math.sqrt(x_squares * y_squares)

def product(seq):
    result = 1
    for x in seq: 
        result = result * x
    return result

def factorial(n):
    return product(xrange(1, n + 1))

def binomial_probability(N, x, pi):
    return (
        (factorial(N) / float(factorial(x) * factorial(N - x))) *
        pow(pi, x) *
        pow(1.0 - pi, N - x)
        )

def binomial_probabilities(N, vx, pi):
    return sum(binomial_probability(N, x, pi) for x in vx)

def poisson_probability(mu, x):
    """
    Given a mean number of successes, mu, what is the probability of x
    successes?
    """
    return math.exp(-mu) * pow(mu, x) / factorial(x)

def multinomial_probability(v_prob, v_count):
    """
    Given a number of possible outcomes, where the probability of each
    is v_prob[i], what is the probability outcome i will happen
    v_count[i] times, for all i.
    """
    assert len(v_prob) == len(v_count)
    return (
        (float(factorial(sum(v_count))) / product(factorial(ni) for ni in v_count)) *
        product(pow(pi, ni) for (pi, ni) in zip(v_prob, v_count))
        )

def bayes(p_B_A, p_B_notA, p_A):
    """
    Return the probability of A given B:  P(A|B)   p_A_B

    Inputs:
       Probability of B given A:      P(B|A)       p_B_A
       Probability of B given not A:  P(B|A')      p_B_notA
       Probability of A:              P(A)         p_A
    """
    p_notA = 1.0 - p_A
    return (p_B_A * p_A) / (p_B_A * p_A + p_B_notA * p_notA)

def percent_in_range_normal(mean, sd, low, high):
    """
    Returns the percentage of the population between low and high,
    assuming a normal distribution.
    """
    low_sigma = float(low - mean) / sd
    high_sigma = float(high - mean) / sd
    low_percentile = scipy.stats.norm.cdf(low_sigma)
    high_percentile = scipy.stats.norm.cdf(high_sigma)
    return high_percentile - low_percentile

class TestStats(unittest.TestCase):

    def test_standard_deviation(self):
        sd = standard_deviation([6, 11, 15, 12, 3, 14, 15, 15])
        self.assertAlmostEqual(4.5650066, sd)

    def test_interquartile_range(self):
        r = interquartile_range([12, 13, 14, 15, 9, 10, 16, 10,
                                 8, 10, 11, 12, 13, 22, 23, 24, 25])
        self.assertAlmostEqual(6, r)


    def test_correlation(self):
        x = [8, 9, 10, 12, 10, 13, 8, 7, 7, 12, 
             11, 11, 9, 13, 9, 10, 11, 10, 7, 8, 8, 11, 8, 13, 9]
        y = [8, 10, 9, 12, 9, 11, 9, 10, 10, 12,
             8, 11, 9, 11, 9, 9, 11, 12, 9, 10, 8, 10, 9, 13, 13]
        r = correlation_coefficient(x, y)
        self.assertAlmostEqual(0.5427855, r)

    def test_factorial(self):
        self.assertEqual(120, factorial(5))

    def test_binomial_probability(self):
        # http://onlinestatbook.com/2/probability/binomial.html
        self.assertAlmostEqual(0.5, binomial_probability(2, 1, 0.5))
        self.assertAlmostEqual(0.25, binomial_probability(2, 0, 0.5))
        self.assertAlmostEqual(0.36, binomial_probability(2, 0, 0.4))
        self.assertAlmostEqual(0.0546875, binomial_probabilities(10, [8, 9, 10], 0.5))

    def test_poisson_probability(self):
        self.assertAlmostEqual(0.0116442, poisson_probability(21, 12))

    def test_multinomial_probability(self):
        # http://onlinestatbook.com/2/probability/multinomial.html
        self.assertAlmostEqual(0.1008, multinomial_probability([0.4, 0.1, 0.5], [4, 1, 5]))

    def test_bayes(self):
        self.assertAlmostEqual(0.4049587, bayes(0.98, 0.06, 0.04))

    def test_percent_in_range_normal(self):
        # http://onlinestatbook.com/2/normal_distribution/areas_normal.html
        self.assertAlmostEqual(0.7871163, percent_in_range_normal(38, 6, 30, 45))

print scipy.stats.norm.cdf((6.0 - 18.0) / 5.0)

data = """
          8	  8
  9	 10
 10	  9
 12	 12
 10	  9
 13	 11
  8	  9
  7	 10
  7	 10
 12	 12
 11	  8
 11	 11
  9	  9
 13	 11
  9	  9
 10	  9
 11	 11
 10	 12
  7	  9
  8	 10
  8	  8
 11	 10
  8	  9
 13	 13
  9	 13"""

data = [int(s) for s in data.split()]
(x, y) = unzip(group_pairs(data))
#print repr(list(x))
#print repr(list(y))

unittest.main()

