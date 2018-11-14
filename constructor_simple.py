#!/usr/bin/env python3
import copy
import types

def constructed_by(con_type):
    '''
    Attach a constructor type to the provided type.
    This will allow calling instances of the constructor type to construct
    instances of the provided type, by copying fields from the constructor
    object.
    This function doesn't impose any constraints on the two types, but generally
    the constructor type should be picklable.
    '''
    def constructed_by_decorator(constructed_type):
        # Check that we haven't already attached this constructor.
        if hasattr(con_type, '_constructed_type'):
            raise TypeError(f'{con_type.__name__} cannot construct '
            f'{constructed_type.__name__}, since it is already a constructor '
            f'for {con_type._constructed_type.__name__}.')

        # Check that the constructor type doesn't define __call__.
        # Looking up __call__ will first attempt to get the class's field. If
        # the class defines __call__, this will return a function type, since
        # we're looking up through the class (and not an instance).
        # If the class doesn't define __call__, looking up __call__ will look up
        # the __call__ method defined on the `type` type itself.
        class_has_call = isinstance(con_type.__call__, types.FunctionType)
        if class_has_call and con_type.__call__ is not Constructor.__call__:
            raise TypeError(f'{con_type.__name__} cannot be a constructor,'
                            ' since it already defines __call__.')

        con_type._constructed_type = constructed_type
        def instantiate(constructor):
            instance = constructed_type.__new__(constructed_type)
            instance.__dict__ = dict((k, copy.deepcopy(v))
                                     for k, v in constructor.__dict__.items())
            if hasattr(instance, 'construct'):
                instance.construct()
            return instance

        # Finish attaching to the constructor type.
        con_type.__call__ = instantiate
        return constructed_type
    return constructed_by_decorator


class Constructor:

    def __call__(self):
        # This should only happen if constructed_by wasn't used to attach the
        # specific Constructor type to a class.
        raise TypeError(f"{type(self).__name__} doesn't construct any type.")


class Preconstructed:
    '''
    A constructor object which just returns copies of a given object.
    '''

    def __init__(self, to_copy):
        self.to_copy = to_copy

    def __call__(self):
        return copy.deepcopy(self.to_copy)


# Simple simulation of deploying a constructor.

def test_deploy(constructor):
    import pickle
    print()
    print('constructor', constructor)
    s = pickle.dumps(constructor)
    # print('pickled constructor', s)
    loaded_constructor = pickle.loads(s)
    # print('loaded constructor', s)
    instance = loaded_constructor()
    print('instance', instance)
    print()


## Example without using constructor:

class MyEnv:

    def __init__(self, name):
        self._name = name

# We can't pickle a lambda, so we use `functools.partial` for this example.
import functools # pylint: disable=C0413

test_deploy(functools.partial(MyEnv, 'MyEnv'))



## Example using Preconstructed (this only works because MyEnv is picklable).

test_deploy(Preconstructed(MyEnv('Preconstructed MyEnv')))


## Example with recommended practices.

class ExampleEnvCon(Constructor):

    def __init__(self, width, height=None):
        if height is None:
            height = width
        self.width = width
        self.height = height

# If the decorator is forgotten, the following error occurs:
#      TypeError: ExampleEnvCon doesn't construct any type
@constructed_by(ExampleEnvCon)
class ExampleEnv(ExampleEnvCon):
    # To get better tab completion / pylint output, inherit from
    # ExampleEnvCon, even though we don't need to.

    def construct(self):
        print(f"creating ExampleEnv with {self.width}, {self.height}")
        self._world = {}

test_deploy(ExampleEnvCon(width=8))


## Example with minimal practices.

class MinimalCon:
    def __init__(self, width, height=None):
        if height is None:
            height = width
        self.width = width
        self.height = height

# If the decorator is forgotten, the following error occurs:
#   TypeError: 'ExampleEnvCon' object is not callable
@constructed_by(MinimalCon)
class MinimalEnv:
    # If we don't inherit, nothing breaks, but pylint and friends can no longer
    # determine our fields.
    # We probably want the following:
    # pylint: disable=no-member

    def construct(self):
        print(f"creating MinimalEnv with {self.width}, {self.height}")
        self._world = {}

test_deploy(MinimalCon(width=8))


## Example with showing results of attaching constructor to two types.

class RepeatedCon:
    def __init__(self, width, height=None):
        if height is None:
            height = width
        self.width = width
        self.height = height

@constructed_by(RepeatedCon)
class FirstEnv:
    # pylint: disable=no-member

    def construct(self):
        print(f"creating FirstEnv with {self.width}, {self.height}")
        self._world = {}

try:
    @constructed_by(RepeatedCon)
    class SecondEnv(RepeatedCon):
        pass
except TypeError as e:
    print()
    print('Error message resulting from repeated constructed_by call:')
    # RepeatedCon cannot construct SecondEnv, since it is already a
    # constructor for FirstEnv.
    print(e)
    print()


## Example with a constructor that already defined __call__.

class ErroneousCon:

    def __init__(self, width, height=None):
        if height is None:
            height = width
        self.width = width
        self.height = height

    def __call__(self):
        print('oh no!')

try:
    @constructed_by(ErroneousCon)
    class ErroneousEnv:
        pass
except TypeError as e:
    print()
    print('Error message resulting from constructor defining __call__:')
    # ErroneousCon cannot be a constructor, since it already defines
    # __call__.
    print(e)
    print()
