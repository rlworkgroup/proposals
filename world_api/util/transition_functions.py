"""Transition functions."""
import numpy as np


def deterministic(s, a):
    return s + a


def epsilon_random(epsilon):
    def maybe_random(s, a):
        if np.random.rand() < epsilon:
            return s + np.random.rand() * 0.1

        return deterministic(s, a)

    return maybe_random


def walls(bounds):
    def clipped(s, a):
        sprime = deterministic(s, a)
        np.clip(sprime, *bounds)
        return sprime

    return clipped
