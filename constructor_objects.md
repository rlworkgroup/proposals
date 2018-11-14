Constructor Objects
===================

## Background

Currently in Garage, we have two general methods of “serializing” types.

The for stateful objects (basically just neural networks), we have
`Parameterized`, which is used to essentially store the network's weights in a
picklable dictionary. The logic for doing that is not very magic, and not
necessary for more recent frameworks, since the frameworks provide equivalent
functions (e.g.  `torch.nn.Module.named_parameters()`,
`mxnet.gluon.Block.collect_params()`). We can simply define a common interface
for getting / setting a picklable version of a model, which is shared by all of
these frameworks. However, `Parameterized` also inherits
from the other serialization type.

The other (more magic) serialization type we have is `Serializable`, which is
used for stateless types. It functions by capturing the parameters to
`__init__`, and serializing those instead of the object itself. This is not an
obvious interface, and generally doesn’t do exactly what we want. Usually we
want to describe how to construct an object, then transmit that. But
`Serializable` requires additional hacks to achieve that. Furthermore,
`Serializable` has basically permeated the code base, being inherited from in a
bunch of places it’s not needed.


## Proposal

I propose replacing Serializable with the use of "constructor objects."
Constructor objects are just pickleable objects that can be invoked to
construct instances of their corresponding type.

That’s too abstract to easily understand, so here’s an example.
Currently, if you have an environment that can’t be pickled (since it opens a
subprocess, etc.), you would do something like this (extracted from
garage/envs/mujoco/gather/gather_env.py):

```python
from garage.core import Serializable

class GatherEnv(Serializable):

    def __init__(self, n_apples=8, n_bombs=8):
        self.n_apples = n_apples
        self.n_bombs = n_bombs

        # Serializable constructor is often called last, but should usually be
        # called first.
        Serializable.quick_init(self, locals())
```

In experiment file (at least in principle):

```python
env = GatherEnv(3, 2)

run_experiment(..., env=env)
```

I propose replacing it the following interface:

```python
class GatherEnv:

    def __init__(self, n_apples=8, n_bombs=8):
        self.n_apples = n_apples
        self.n_bombs = n_bombs
```

In experiment file (at least in principle):

```python
run_experiment(..., env_con=functools.partial(GatherEnv, 3, 2))
```

For types with many parameters (e.g. most environments in practice),
`functools.partial` has the weakness that it doesn’t check any parameters.  To
handle that case, I’ve made a simple decorator to help split a class into a
constructor type and the main type:

```python
class GatherEnvCon:

    def __init__(self, n_apples=8, n_bombs=8):
        self.n_apples = n_apples
        self.n_bombs = n_bombs

@constructed_by(GatherEnvCon)
class GatherEnv:

    def construct(self):
        # constructor fields are already set
        for apple in range(self.n_apples):
            ...
```

In experiment file (at least in principle):

```python
run_experiment(..., env_con=GatherEnvCon(3, 2))
```

A simple version of the source is in `constructor_simple.py`. I more
sophisticated version which handles `__slots__` is in `constructor.py`.
