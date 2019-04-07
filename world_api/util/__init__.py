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
    print('state: [{:.2f}, {:.2f}]\treward: -\tdone: -'.format(*state))


def print_step(step):
    s, r, d, _ = step
    print('state: [{:.2f}, {:.2f}]\treward: {:.2f}\tdone: {}'.format(*s, r, d))
    time.sleep(0.1)
