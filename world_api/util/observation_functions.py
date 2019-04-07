"""Observation functions."""


def identity(s):
    return s


def gaussian_noise(stddev):
    def gaussian(s):
        return np.random.normal(loc=s, scale=stddev)

    return gaussian


def gumbel_noise(scale):
    def gumbel(s):
        return np.random.gumbel(loc=s, scale=scale)

    return gumbel
