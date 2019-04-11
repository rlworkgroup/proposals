import pprint
import time

import numpy as np

np.set_printoptions(precision=2)


def print_running(world):
    print('-' * 80)
    print('| Running {}...'.format(type(world).__name__))
    print('-' * 80)


def print_pomdp(pomdp):
    print('-' * 60)
    print('Sampling new POMDP...')
    print('-' * 60)
    print('POMDP: {}'.format(pprint.pformat(pomdp)))
    time.sleep(1.)


def print_reset(state):
    print('--- reset ---')

    if isinstance(state, np.ndarray):
        print('state: {}\treward: -\tdone: -'.format(state2str(state)))

def print_step(step):
    s, r, d, _ = step
    print('state: {}\treward: {:.2f}\tdone: {}'.format(state2str(s), r, d))
    time.sleep(0.1)

def state2str(state):
    if isinstance(state, np.ndarray) and len(state) == 2:
        return '[{:.2f}, {:.2f}]'.format(*state)
    else:
        return pprint.pformat(state)
