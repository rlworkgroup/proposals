"""Reward functions."""
import numpy as np


def sparse_goal(goal, tolerance):
    def reward(s, a, sprime):
        dist = np.linalg.norm(sprime - goal)
        return float(dist < tolerance)

    return reward


def dense_goal(goal):
    def reward(s, a, sprime):
        return -np.linalg.norm(sprime - goal)

    return reward


def mostly_dense_goal(goal, tolerance):
    def reward(s, a, sprime):
        return sparse_goal(goal, tolerance)(s, a, sprime) + dense_goal(goal)(
            s, a, sprime)

    return reward
