import gym

from world import ParametricWorld


class MultiTaskWorld(ParametricWorld):
    """A World whose POMDP is characterized by a discrete set of reward
    functions.

    Args:
        *reward_functions (``Callable``): A variable-length argument list of
            one or more reward functions.
    """

    def __init__(self, *reward_functions):
        self._reward_functions = reward_functions
        self.pomdp_space = gym.spaces.Discrete(len(self._reward_functions))

    @property
    def _reward(self):
        return self._reward_functions[self._pomdp]


class GoalConditionedWorld(ParametricWorld):
    """A World whose POMDP is characterized by a start state and a goal
    state.

    Args:
        start_space (:obj:`gym.Space`): A space representing valid start
            states.
        goal_space (:obj:`gym.Space`): A space represnting valid goal states.
    """

    def __init__(self, start_space, goal_space):
        self.pomdp_space = gym.spaces.Dict({
            'start': start_space,
            'goal': goal_space,
        })


class MutableDynamicsWorld(ParametricWorld):
    """A World whose POMDP is characterized by a set of mutable dynamics
    parameters.

    Attributes:
        dynamics_space: (:obj:`gym.spaces.Dict`): A :obj:`gym.spaces.Dict`
            whose keys represent dynamics parameters, with corresponding spaces
            for their valid values.
    """
    def __init__(self):
        self.pomdp_space = self.dynamics_space

    def set_dynamics(self, parameters):
        """Set the dynamic parameters of the simulation.

        Args:
            parameters (dict): A dictionary whose keys are parameter
                identifiers and whose values are parameter values.
        """
        pass

    @property
    def pomdp(self):
        return self._pomdp

    @pomdp.setter
    def pomdp(self, pomdp):
        self.set_dynamics(pomdp)

