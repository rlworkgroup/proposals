import gym
import gym.spaces
import numpy as np

from world import MutableDynamicsWorld
import util


class PointMutableDynamicsWorld(MutableDynamicsWorld):
    """A goal-conditioned point-mass world."""

    dynamics_space = gym.spaces.Dict({
        'mass': gym.spaces.Box(low=0.1, high=10.0, shape=(), dtype=np.float32),
        'gain': gym.spaces.Box(low=1.0, high=10.0, shape=(), dtype=np.float32),
    })

    default_dynamics = {
        'mass': 1.0,
        'gain': 1.0,
    }

    observation_space = gym.spaces.Dict({
        'position':
        gym.spaces.Box(low=-10.0, high=10.0, shape=(2, ), dtype=np.float32),
        'velocity':
        gym.spaces.Box(low=-np.inf, high=np.inf, shape=(2, ), dtype=np.float32),
        'acceleration':
        gym.spaces.Box(low=-np.inf, high=np.inf, shape=(2, ), dtype=np.float32),
    })

    action_space = gym.spaces.Dict({
        'effort':
        gym.spaces.Box(low=-1.0, high=1.0, shape=(2, ), dtype=np.float32)
    })

    goal = np.array((1., 1.), dtype=np.float32)
    goal_tolerance = 0.1

    def __init__(self):
        super().__init__()
        self.set_dynamics(self.default_dynamics)
        self._mass = 1.0
        self._gain = 1.0
        self._position = np.zeros(2, dtype=np.float32)
        self._velocity = np.zeros_like(self._position)
        self._acceleration = np.zeros_like(self._position)

    def _simulate_physics(self, action):
        force = action['effort'] * self._gain
        self._acceleration = force / self._mass
        momentum = self._mass * self._velocity
        momentum += self._acceleration
        self._velocity = momentum / self._mass
        self._position += self._velocity

    def _observe(self):
        return {
            'position': self._position,
            'velocity': self._velocity,
            'acceleration': self._acceleration,
        }

    def set_dynamics(self, parameters):
        self._mass = parameters['mass']
        self._gain = parameters['gain']

    def reset(self):
        self._position = np.zeros(2, dtype=np.float32)
        self._velocity = np.zeros_like(self._position)
        self._acceleration = np.zeros_like(self._position)
        return self._observe()

    def step(self, action):
        self._simulate_physics(action)

        dist = np.linalg.norm(self._position - self.goal)
        reward = -dist
        done = dist < np.linalg.norm(self.goal_tolerance)

        return self._observe(), reward, done, dict()

    def render(self, mode='human'):
        print(self._point)


if __name__ == '__main__':
    """Implements dynamics randomization for the Point environment"""

    # Create an instance of the world
    world = PointMutableDynamicsWorld()
    util.print_running(world)

    for _ in range(5):
        # Sample a new POMDP
        mdp = world.pomdp_space.sample()
        world.pomdp = mdp
        util.print_pomdp(mdp)

        # Reset and step the POMDP in the World
        initial_state = world.reset()
        util.print_reset(initial_state)
        for _ in range(10):
            step = world.step({'effort': np.array([0.1, 0.1])})
            util.print_step(step)
