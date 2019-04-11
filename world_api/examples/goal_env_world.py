import warnings
import pprint

import gym.spaces
from multiworld.core.multitask_env import MultitaskEnv

from world import ParametricWorld


class MultiworldMultitaskWorld(ParametricWorld, gym.Wrapper):
    """
    World interface
    """

    def __init__(self, env):
        assert isinstance(env, MultitaskEnv), (
            'This class only supports wrapping '
            'multiworld.core.multitask_env.MultitaskEnv')
        super().__init__(env)

        self.pomdp_space = gym.spaces.Dict({
            k: self.env.observation_space.spaces[k]
            for k in ['desired_goal', 'state_desired_goal']
        })

    @property
    def pomdp(self):
        return self.env.get_goal()

    @pomdp.setter
    def pomdp(self, pomdp_descriptor):
        self._validate_descriptor(pomdp_descriptor)
        if hasattr(self.env, 'set_goal'):
            self.env.set_goal(pomdp_descriptor)
        elif hasattr(self.env, 'set_to_goal'):
            self.env.set_to_goal(pomdp_descriptor)
        else:
            warnings.warn('{} does not implement "set_goal" or "set_to_goal".'
                          'Not able to change the POMDP')


    """
    gym.Wrapper interface
    """
    def step(self, action):
        return self.env.step(action)

    def reset(self):
        return self.reset()


class WorldWrapperWarning:
    """Warning class for World wrappers."""
    pass


if __name__ == '__main__':
    import time

    from multiworld.envs.mujoco.sawyer_xyz.sawyer_reach import SawyerReachXYZEnv

    env = SawyerReachXYZEnv()
    world = MultiworldMultitaskWorld(env)
    world.reset()
    world.render()

    for _ in range(10):
        p = world.pomdp_space.sample()
        world.pomdp = p

        print('Choosing new POMDP (goal): {}'.format(pprint.pformat(p)))

        for _ in range(100):
            world.step(world.action_space.sample())
            world.render()
            time.sleep(0.05)
