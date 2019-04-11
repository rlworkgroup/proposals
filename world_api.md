# Title
| Author | Date Proposed | Last Updated |
|---|---|---|
| Ryan Julian | 4/6/2019 | 4/11/2019 |

## Background

### Context
While `gym.Env` provides a good abstraction for defining a single POMDP, the API lacks a good way of defining a meta-RL environment, which is a family of related POMDPs/environments.

### Problem Statement
Defining a meta-RL environment using `gym.Env` is cumbersome, and there exists no standard API for defining them. On GitHub and in the literature there exist many examples of general multi-task, goal-conditioned, and meta-RL environments based on `gym.Env`. Each author chooses her own method of defining these environments on top of the `gym.Env` interface. This lack of standardization needlessly harms reproducibility and research velocity. It makes it difficult for different research groups and individual to reuse the work of their colleagues, and difficult to compare the performance of an algorithm from one paper to the experiments from another. 

### Scope
The scope of this proposal is to define a single API for defining `gym.Env`-based meta-RL environments.

### Goals
* Establish an API for defining a meta-RL environment
* Ensure that API is useful for defining meta-RL benchmarks

### Non-Goals
* Designing particularly-useful meta-RL environments -- establish the API only
* Provide tools for defining meta-RL environments, other than the base interface
* Prescribe good benchmark sets of meta-RL environments -- the API should be useful for describing these, but this proposal does not concern exactly what benchmarks the community should use for meta-RL.

## Design Overview
The design relies on the composition pattern. It creates a new API called `World`, which implements the `gym.Env` interface, with one additional property: there is a field on `World` which allows the user to mutate the POMDP executed by the environment at any time.

The POMDP is described by a POMDP descriptor, which summarizes how environments in this `World` differ. This descriptor can be any object, but we require that it be pickleable and have a useful equality operator. It's preferable (but not required) that the descriptor also be serializable to text and even immutable. How the descriptor is used is entirely up to the author of a `World`, though the descriptor should be the **only** way to modify the POMDP behavior of a `World`.

```python
class World(gym.Env, metaclass=abc.ABCMeta):
    """Represents a family of (PO)MDPs implementing the :obj:`gym.Env`
    interface.
    """

    @property
    def pomdp(self):
        """The descriptor representing the POMDP currently being executed by
        this :obj:`World`.

        Setting this property changes the current descriptor, and therefore the
        :obj:`World`'s POMDP behavior, immediately.
        """
        pass

    @pomdp.setter
    def pomdp(self, pomdp_descriptor):
        pass
```

This design allows resource allocation to still happen in the constructor. A `World` is a more general environment: it's an enviroment whose POMDP can change.

### Parametric Worlds
An interesting class of worlds is those POMDPs we can directly parameterize -- for instance a goal-conditioned world can be described by parameters `start` and `goal` specify the start and end states, and a multi-task world can be described by a discrete variable specifying which task (reward function) is active at any time. `gym.Spaces` makes it easy to create a descriptor for these kinds of worlds.

```python
class ParametricWorld(World, metaclass=abc.ABCMeta):
    """A :obj:`World` whose POMDPs can be described by a :obj:`gym.Space`
    object.
    """

    @property
    def pomdp_space(self):
        """A :obj:`gym.Space` which describes POMDP descriptors for this
        :obj:`ParametricWorld`."""
        return self._pomdp_space

    @property
    def pomdp(self):
        return self._pomdp

    @pomdp.setter
    def pomdp(self, pomdp_descriptor):
        if not self.pomdp_space.contains(pomdp_descriptor):
            raise ValueError('descriptor must be in the space:\n'
                             '\t{}\n'
                             '\t...but you provided: \n'
                             '\t{}'.format(
                                 pprint.pformat(self.pomdp_space),
                                 pprint.pformat(pomdp_descriptor)))
        self._pomdp = pomdp_descriptor
```

## Common Meta-RL Scenarios
Below are some examples of common meta-RL scenarios, as implemented under this interface. All of them can be sampled using example the same training loop:
```python
from some.where import MostExcellentWorld

world = MostExcellentWorld()
world.reset()

for _ in range(num_batches):
    batch_samples = []
    for _ in range(envs_per_batch)
        pomdp = world.pomdp_space.sample()
        env_samples = sample_environment(env)
        batch_samples.append(env_samples)

    algo.train_batch(batch_samples)
```
### Goal-Conditioned Worlds
```python
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
```

### Multi-Task Learinng (with arbitrary reward functions)
```python
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
```

### Dynamics Transfer
Note that using the training loop above with this `World` implements dynamics randomization.

```python
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
```

## Detailed Design
### From `gym.Env` to `World`
Lets take a look a how we can turn a simple point-mass environment into a `World`.

We begin with the lowly point-mass environment.
```python
class PointEnv(gym.Env):
    """A simple point mass environment."""
    observation_space = gym.spaces.Box(
        low=-np.inf, high=np.inf, shape=(2, ), dtype=np.float32)
    action_space = gym.spaces.Box(
        low=-0.1, high=0.1, shape=(2, ), dtype=np.float32)
    start = np.array((0., 0.), dtype=np.float32)
    goal = np.array((1., 1.), dtype=np.float32)
    goal_tolerance = np.linalg.norm(action_space.low)

    def __init__(self):
        self._point = np.copy(self.start)

    def reset(self):
        self._point = np.copy(self.start)
        return np.copy(self._point)

    def step(self, action):
        self._point = self._point + action
        dist = np.linalg.norm(self._point - self.goal)
        reward = -dist
        done = dist < np.linalg.norm(self.goal_tolerance)
        return np.copy(self._point), reward, done, dict()

    def render(self, mode='human'):
        print(self._point)


if __name__ == '__main__':
    """Constructs and steps the Point environment."""
    # Create environment
    env = PointEnv()
    # Reset and step environment
    for _ in range(5):
        env.reset()
        env.render()
        for _ in range(10):
            step = env.step(env.action_space.high)
            env.render()
```


#### Goal-Conditioned
We decide that we'd like to turn it instead into a goal-conditioned point environment. `World` provides a straightforward way of doing this which gets out of the way. All we have to do is encode the parameters of the POMDP which vary -- the start and goal locations -- in our POMDP descriptor.

```python
class PointGoalWorld(ParametricWorld):
	observation_space = gym.spaces.Box(
        low=-10.0, high=10.0, shape=(2, ), dtype=np.float32)
    action_space = gym.spaces.Box(
        low=-0.1, high=0.1, shape=(2, ), dtype=np.float32)
    goal_tolerance = action_space.low
    pomdp_space = gym.spaces.Dict({
    	'start': observation_space,
    	'goal': observation_space,
    })
    default_pomdp = {
        'start': np.array((0., 0.), dtype=np.float32),
        'goal': np.array((1., 1.), dtype=np.float32),
    }

    def __init__(self):
        self.pomdp = self.default_pomdp
        self._point = np.copy(self._pomdp['start'])

    def reset(self):
        self._point = np.copy(self._pomdp['start'])
        return np.copy(self._point)

    def step(self, action):
        self._point = self._point + action
        dist = np.linalg.norm(self._point - self._pomdp['goal'])
        reward = -dist
        done = dist < np.linalg.norm(self.goal_tolerance)
        return np.copy(self._point), reward, done, dict()

    def render(self, mode='human'):
        print(self._point)


if __name__ == '__main__':
	import json
	import pickle

     # Create an instance of the world
    world = PointGoalWorld()
    for _ in range(5):
        # Sample a new POMDP
        mdp = world.pomdp_space.sample()
        mdp = pickle.loads(pickle.dumps(mdp))  # the POMDP is pickleable!
        mdp = json.loads(json.dumps(mdp)) # if you're lucky, it might even be JSON-able!
        world.pomdp = mdp
        # Reset and step the POMDP in the World
		world.reset()
		world.render()
        for _ in range(10):
            step = world.step(world.action_space.low)
```

In fact, all goal-conditioned worlds are basically the same, making it even easier to define our `World`. We can just pass the valid `start` and `goal` spaces to the `GoalConditionedWorld` constructor.
```python
class GoalConditionedWorld(ParametricWorld):
    def __init__(self, start_space, goal_space):
        self._pomdp_space = gym.spaces.Dict({
            'start': start_space,
            'goal': goal_space,
        })

class PointGoalWorld(GoalConditionedWorld):
	"""A goal-conditioned point-mass world."""
    observation_space = gym.spaces.Box(
        low=-10.0, high=10.0, shape=(2, ), dtype=np.float32)
    action_space = gym.spaces.Box(
        low=-0.1, high=0.1, shape=(2, ), dtype=np.float32)
    goal_tolerance = action_space.low
    default_pomdp = {
        'start': np.array((0., 0.), dtype=np.float32),
        'goal': np.array((1., 1.), dtype=np.float32),
    }

    def __init__(self):
        super().__init__(self.observation_space, self.observation_space)
        self.pomdp = self.default_pomdp
        self._point = np.copy(self._pomdp['start'])

    def reset(self):
        self._point = np.copy(self._pomdp['start'])
        return np.copy(self._point)

    def step(self, action):
        self._point = self._point + action
        dist = np.linalg.norm(self._point - self._pomdp['goal'])
        reward = -dist
        done = dist < np.linalg.norm(self.goal_tolerance)
        return np.copy(self._point), reward, done, dict()

    def render(self, mode='human'):
        print(self._point)
```

#### Multi-Task
What if we'd like something more general, like a multi-task point-mass environment which can have any reward function? That's straight-forward too. Here's what it looks like.

```python
from util.reward_functions import sparse_goal, dense_goal, mostly_dense_goal

_START = start = np.array((0., 0.), dtype=np.float32)
_GOAL = np.array((1., 1.), dtype=np.float32)
_GOAL_TOLERANCE = 0.1
_DEFAULT_POMDP = 0

class MultiTaskWorld(ParametricWorld):
    def __init__(self, *reward_functions):
        self._reward_functions = reward_functions
        self._pomdp_space = gym.spaces.Discrete(len(self._reward_functions))

    @property
    def _reward(self):
        return self._reward_functions[self._pomdp]

class MultiTaskPointWorld(MultiTaskWorld):
    """A general multi-task point-mass world."""
    action_space = gym.spaces.Box(
        low=-0.1, high=0.1, shape=(2, ), dtype=np.float32)
    observation_space = gym.spaces.Box(
        low=-np.inf, high=np.inf, shape=(2, ), dtype=np.float32)

    def __init__(self):
        super().__init__(
            sparse_goal(_GOAL, _GOAL_TOLERANCE), dense_goal(_GOAL),
            mostly_dense_goal(_GOAL, _GOAL_TOLERANCE))
        self._point = np.copy(_START)
        self.pomdp = _DEFAULT_POMDP

    def reset(self):
        self._point = np.copy(_START)
        return np.copy(self._point)

    def step(self, action):
        point_old = np.copy(self._point)
        self._point = self._point + action
        reward = self._reward(point_old, action, self._point)
        dist = np.linalg.norm(self._point - _GOAL)
        done = dist < _GOAL_TOLERANCE
        return np.copy(self._point), reward, done, dict()

    def render(self, mode='human'):
        print(self._point)


if __name__ == '__main__':
    # Create an instance of the world
    world = MultiTaskPointWorld()
    for _ in range(5):
        # Sample a new POMDP
        world.pomdp = world.pomdp_space.sample()
        # Reset and step the POMDP in the World
        world.reset()
        world.render()
        for _ in range(10):
            step = world.step(world.action_space.high)
            world.render()
```

### `MetaWorld`s
So far we have described how to define a `World`, which is a `gym.Env` whose POMDP behavior can change. We haven't described how the behavior will change over time. Luckly, the API makes that pretty easy to model: we just define another (PO)MDP whose states are POMDPs for an inner `World`! Because the POMDP of the inner `World` is mutable, evolving the inner world requires only an assignment operation.

```python
class MetaWorld(ParametricWorld):
    """A :obj:`World` whose state space is a :obj:`POMDPDescriptor`."""
    def __init__(self, pomdp_space):
        self.observation_space = pomdp_space

    def render(self, mode='human'):
        print(self.pomdp)
```

Here's what a `MetaWorld` looks like for our goal-conditioned example from before, assuming you want to sample random goals:
```python
class UniformRandomMetaWorld(MetaWorld):
    action_space = gym.spaces.Discrete(0)

    def reset(self):
        return self.observation_space.sample()

    def step(self, action):
        return self.observation_space.sample(), None, False, dict()

# Create an instance of the world
world = PointGoalWorld()

# Create a metaworld to control the world
meta = UniformRandomMetaWorld(world.pomdp_space)
world.pomdp = meta.reset()

for _ in range(5):
    # Reset and step the POMDP in the World
    world.reset()
    world.render()
    for _ in range(10):
        world.step(world.action_space.low)
        world.render()

    # Sample a new POMDP
    world.pomdp, _, _, _ = meta.step(None)
```

A `MetaWorld` is a full environment. It can have an action space, hidden state, and even rewards!

Here's what the multi-task example looks like. Here we want to visit a discrete set of tasks in round-robin order.

```python
class RoundRobinMetaWorld(MetaWorld):
    action_space = gym.spaces.Discrete(0)

    def __init__(self, pomdp_space):
        if not isinstance(pomdp_space, gym.spaces.Discrete):
            raise ValueError('pomdp_space must be `gym.spaces.Discrete, but '
                             '{} provided.'.format(pomdp_space))

        super().__init__(pomdp_space)
        self._state = 0

    def reset(self):
        self._state = 0
        return self._state

    def step(self, action):
        self._state = (self._state + 1) % self.observation_space.n
        return self._state, None, False, dict()

# Create an instance of the world
world = MultiTaskPointWorld()

# Create a metaworld to control the world
meta = RoundRobinMetaWorld(world.pomdp_space)
world.pomdp = meta.reset()

for _ in range(5):
    # Reset and step the POMDP in the World
    world.reset()
    world.render()
    for _ in range(10):
        world.step(world.action_space.high)
        world.render()

    # Sample a new POMDP
    world.pomdp, _, _, _ = meta.step(None)
```

## Additional Resources Needed
**Skip this section in your first draft**

What new machines, people, money, etc. are needed to complete implementation?

## Cross-Cutting Concerns
**Skip this section in your first draft**

How your design affects other teams or parts of the software. Very project-specific. This includes API changes you might need, disruptions of others' work, etc.

## Alternatives Considered

### Enviroment Factory
This is perhaps the most straightforward way of defining a meta-RL environment, but in practice is has a big downside.

**Many environments allocate non-trivial resources in their constructors (e.g. large simulations, image buffers, etc.)**. Usually we'd like these resources to be shared by the meta-RL environments we are executing, for instance a MuJoCo-based multi-task RL environment can use the same MuJoCo simulation for all tasks, and only change reward functions. Avoiding re-creating these resources under the factory pattern forces us to rewrite environments to either (a) move resource allocation out of the constructor or (b) use some other more complex way of injecting resources into an environment.

If we were to rewrite most enviroment libraries from scratch today, we might use this option. For a great example of an enviroment library which doesn't suffer from this problem, see [dm_control](https://github.com/deepmind/dm_control)

```python
from some.where import MetaPointEnv
from some.where import MetaSawyerEnv

# Okay, this seems fine...
for _ in range(num_batches):
	batch_samples = []
	for _ in range(envs_per_batch)
		env = MetaPointEnv.build(start=sample_start(), goal=sample_goal())
		env_samples = sample_environment(env)
		batch_samples.append(env_samples)

	algo.train_batch(batch_samples)


# Wait, this is wasteful...
sawyer_tasks = ['pick_up_cube', 'move_cube', ...]  # etc.
for _ in range(num_batches):
	batch_samples = []
	for _ in range(envs_per_batch)
		env = MetaSawyerEnv.build(task=np.random.choice(sawyer_task))
		env_samples = sample_environment(env)
		batch_samples.append(env_samples)

	algo.train_batch(batch_samples)
```

### Proxy Environments
These get messy quickly, and conflate the outer MDP (the one selecting the environment) with the inner MDP (the actual enviroment), making it difficult to define now new MDPs are sampled. This also suffers the same problem as the factory method: without some other resource-sharing mechanism, every inner environment will allocate new resources whether it needs to or not.

For an example of this pattern, see [MultiTaskEnv](https://github.com/ryanjulian/embed2learn/blob/4e37b96cdf245796a099d10def31e401729ef1f2/envs/multi_task_env.py) from ryanjulian/embed2learn.

```python
from some.where import MultiEnv
from some.where import PointEnv
from some.where import SawyerEnv


# Okay, this seems fine...
env = MultiEnv([PointEnv(start=s, goal=g) for s, g in zip(sample_starts(), sample_goals())])
for _ in range(num_batches):
	batch_samples = []
	env.reset()  # actually chooses a new inner env
	for _ in range(envs_per_batch)
		env_samples = sample_environment(env)
		batch_samples.append(env_samples)

	algo.train_batch(batch_samples)


# Wait, this is wasteful...
sawyer_tasks = ['pick_up_cube', 'move_cube', ...]  # etc.
env = MultiEnv([SawyerEnv(task=t) for t in sawyer_tasks])
for _ in range(num_batches):
	batch_samples = []
	env.reset()  # actually chooses a new inner env
	for _ in range(envs_per_batch)
		env_samples = sample_environment(env)
		batch_samples.append(env_samples)

	algo.train_batch(batch_samples)
```

### Constructor Arguments
This is the most common solution for defining a meta-RL environment. It doesn't really describe how to define a family of environments as much as it does provide some parameterization. The downsides of this approach are similar to the Proxy and Factory cases. Particularly-severe in this case is the conflation between the concrete MDP and the parameters under variation. Environments defined this way quickly devolve into either (1) really deep inheritance trees, (2) classes with huge numbers of conflicting parameters, or both of those things at the same time.

For an example of this pattern, see the [PointEnv](https://github.com/ryanjulian/embed2learn/blob/90b2feda918fb27335c3236a9fe81659a3ac6547/envs/point_env.py) in ryanjulian/embed2learn.

### gym.GoalEnv
This is an excellent abstraction for goal-conditioned meta-RL, but not all meta-RL algorithms are goal-conditioned. Any `gym.GoalEnv` can easily be wrapped to make a goal-conditioned `World` as long as it provides a `set_goal()` API.

For an example of this pattern, see [MultitaskEnv](https://github.com/vitchyr/multiworld/blob/b4ce7ecc0af5cbb8148f62f8731ddede55c4b131/multiworld/core/multitask_env.py) from vitchyr/multiworld.

```python
class GoalEnvWrapper(ParametricWorld, gym.Wrapper):
    """
    World interface
    """

    def __init__(self, env):
        assert isinstance(env, gym.GoalEnv), (
            'This class only supports wrapping gym.GoalEnv')
        super().__init__(env)
        self.pomdp_space = self.env.observation_space.spaces['desired_goal']

    @property
    def pomdp(self):
        return self.env.get_goal()

    @pomdp.setter
    def pomdp(self, pomdp_descriptor):
        self._validate_descriptor(pomdp_descriptor)
        if hasattr(self.env, 'set_goal'):
            self.env.set_goal(pomdp_descriptor)
        else:
            warnings.warn('{} does not implement "set_goal".'
                          'Not able to change the POMDP')

    """
    gym.Wrapper interface
    """
    def step(self, action):
        return self.env.step(action)

    def reset(self):
        return self.reset()
```

