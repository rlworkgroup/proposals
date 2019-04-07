"""Termination functions."""
import numpy as np


def never(s):
    return False


def goal_state(goal, tolerance):
    def distance_tolerance(s):
        return np.linalg.norm(s - goal) < tolerance

    return distance_tolerance


def noisy_goal_state(goal, tolerance, epsilon):
    def noisy_tolerance(s):
        return goal_state(goal, tolerance)(s) and np.random.rand() > epsilon

    return noisy_tolerance
