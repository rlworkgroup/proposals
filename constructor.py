#!/usr/bin/env python3
import types

def _copy_mode_to_function(mode):
    '''
    Convert `mode`, which is either `deep`, `shallow`, or a falsy value into
    an appropriate function from the copy module.
    '''
    if mode:
        import copy
        if mode == 'deep':
            return copy.deepcopy
        elif mode == 'shallow':
            return copy.copy
        else:
            raise TypeError(f'Invalid copy mode {mode}')
    return lambda x: x


def constructed_by(con_type, copy_values=False):
    '''
    Attach a constructor type to the provided type.
    This will allow calling the constructor type to construct instances of the
    provided type, by copying fields from the constructor type.
    This function doesn't impose any constraints on the two types, but generally
    the constructor type should be picklable.
    If the provided type might mutate the fields of provided by the
    constructor, then copy_values should be 'deep' or 'shallow', as
    appropriate.
    Otherwise, (or if the constructor will be only be used once) copy_values can be
    False or None.
    '''
    # Get the requested copy function.
    copy_fn = _copy_mode_to_function(copy_values)

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
        # This is all of the real magic for `constructed_by`.
        if (hasattr(con_type, '__slots__') or
            hasattr(constructed_type, '__slots__')):
            # Handle types with slots (this is slower).
            import inspect
            def instantiate(constructor):
                instance = constructed_type.__new__(constructed_type)
                for slot, value in inspect.getmembers(constructor):
                    if not slot.endswith('__'):
                        setattr(instance, slot, copy_fn(value))
                if hasattr(instance, 'construct'):
                    instance.construct()
                return instance
        else:
            # Handle types without slots (this is faster).
            if copy_values:
                def instantiate(constructor):
                    instance = constructed_type.__new__(constructed_type)
                    fields = constructor.__dict__.items()
                    instance.__dict__ = dict((k, copy_fn(v))
                                             for k, v in fields)
                    if hasattr(instance, 'construct'):
                        instance.construct()
                    return instance
            else:
                # This is the real fast path.
                def instantiate(constructor):
                    instance = constructed_type.__new__(constructed_type)
                    instance.__dict__ = constructor.__dict__.copy()
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

    def __init__(self, to_copy, copy_mode='deep'):
        self.copy_fn = _copy_mode_to_function(copy_mode)
        self.to_copy = to_copy

    def __call__(self):
        return self.copy_fn(self.to_copy)


# Simple simulation of deploying a Constructor.

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
    print('second instance', loaded_constructor())
    print()


## Example without using Constructor:

class MyEnv:

    def __init__(self, name):
        self._name = name


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
    print(e)
    print()


## Example where both objects have slots.

class BothHaveSlotsCon(Constructor):

    __slots__ = ('width', 'height')

    def __init__(self, width, height=None):
        if height is None:
            height = width
        self.width = width
        self.height = height


@constructed_by(BothHaveSlotsCon)
class BothHaveSlotsEnv(BothHaveSlotsCon):
    __slots__ = ('width', 'height', '_world')

    def construct(self):
        print(f"creating BothHaveSlotsEnv with {self.width}, {self.height}")
        self._world = {}

test_deploy(BothHaveSlotsCon(width=8))


## Example where only the constructor object has slots.

class OnlyConSlotsCon(Constructor):
    __slots__ = ('width', 'height')

    def __init__(self, width, height=None):
        if height is None:
            height = width
        self.width = width
        self.height = height


@constructed_by(OnlyConSlotsCon)
class OnlyConSlotsEnv(OnlyConSlotsCon):

    def construct(self):
        print(f"creating OnlyConSlotsEnv with {self.width}, {self.height}")
        self._world = {}

test_deploy(OnlyConSlotsCon(width=8))


## Example where only the constructed object has slots.

class OnlyEnvSlotsCon(Constructor):

    def __init__(self, width, height=None):
        if height is None:
            height = width
        self.width = width
        self.height = height


@constructed_by(OnlyEnvSlotsCon)
class OnlyEnvSlotsEnv(BothHaveSlotsCon):
    __slots__ = ('width', 'height', '_world')

    def construct(self):
        print(f"creating OnlyEnvSlotsEnv with {self.width}, {self.height}")
        self._world = {}

test_deploy(OnlyEnvSlotsCon(width=8))


## Example using `attr`

try:
    import attr
    @attr.s(slots=True)
    class WithAttrSlotsCon(Constructor):

        width = attr.ib()
        height = attr.ib()

        @height.default
        def height_default(self):
            return self.width


    # If using slots=True, attr.s needs to be invoked first, so that
    # constructed_by sees the slots.
    @constructed_by(WithAttrSlotsCon)
    @attr.s(slots=True)
    class WithAttrEnv(WithAttrSlotsCon):

        world = attr.ib(factory=dict)

        def __attrs_post_init__(self):
            self.construct()

        def construct(self):
            print(f"creating WithAttrEnv with {self.width}, {self.height}")
            self.world = {}

    test_deploy(WithAttrSlotsCon(width=8))
except ImportError:
    print("Install attr to run attr example.")


## Example with multiple instances without copying.

class CopyCon:
    def __init__(self, x):
        self.x = x
        self.world = ['from_constructor']

@constructed_by(CopyCon, copy_values='shallow')
class CopyEnv:
    # If we don't inherit, nothing breaks, but pylint and friends can no longer
    # determine our fields.
    # We probably want the following:
    # pylint: disable=no-member

    def construct(self):
        self.world.append('item')
        print(f"populating world CopyEnv: {self.world}")

test_deploy(CopyCon(x='x'))


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
