#!/usr/bin/env python

"""
A/B timeit test: dict of dicts init.

Output:

exists = False:
speedup   seconds  option
    15%  0.780859  in else
    11%  0.821429  defaultdict
    10%  0.825422  not in
     3%  0.890609  get
     0%  0.918161  setdefault
   -83%  1.683932  try

exists = True:
speedup   seconds  option
    21%  0.619301  defaultdict
    19%  0.634981  try
    13%  0.679612  not in
    13%  0.681775  in else
     5%  0.743055  get
     0%  0.779458  setdefault

Result:

* If you want to control when to avoid auto-init on read
(e.g. after explicit delete of k1),
then use "in else" option:
    if k1 in d:
        d[k1][k2] = v
    else:
        d[k1] = {k2: v}

* If it fits code better, "not in" option is almost as good:
    if k1 not in d:
        d[k1] = {}
    d[k1][k2] = v

* But if you are OK with auto-init in all cases,
then "defaultdict" is the best option - both fast and DRY:
    from collections import defaultdict
    d = defaultdict(dict)
    d[k1][k2] = v

* While it looks like minus one lookup,
"get" option has almost no effect:
    vs = d.get(k1)
    if vs is None:
        d[k1] = {k2: v}
    else:
        vs[k2] = v

* Never use "try" option:
it is very slow when k1 does not exist,
and slower than defaultdict when k1 exists:
    try:
        d[k1][k2] = v
    except KeyError:
        d[k1] = {k2: v}

* "setdefault" option creates new dict each time,
so it is very bad both for memory and speed:
    d.setdefault(k1, {})[k2] = v

Copyright (C) 2017 by Denis Ryzhkov <denisr@denisr.com>
MIT License, see http://opensource.org/licenses/MIT
"""

### import

import gc
import time

### config

envs = [
    'exists = False',
    'exists = True',
]

k1 = 'k1'
k2 = 'k2'
v = 'v'

d1 = {'k' + str(i): {} for i in xrange(10**6)}

defaults = dict(
    init_once='pass',
    init_each='pass',
    repeat=10**6,
)

tests = [
    dict(
        name='setdefault',
        init_once='d = d1.copy()',
        init_each='if not exists: del d[k1]',
        measure='d.setdefault(k1, {})[k2] = v',
    ),
    dict(
        name='defaultdict',
        init_once='''
from collections import defaultdict
d = defaultdict(dict, d1)
''',
        init_each='if not exists: del d[k1]',
        measure='d[k1][k2] = v',
    ),
    dict(
        name='not in',
        init_once='d = d1.copy()',
        init_each='if not exists: del d[k1]',
        measure='''
if k1 not in d:
    d[k1] = {}
d[k1][k2] = v
''',
    ),
    dict(
        name='in else',
        init_once='d = d1.copy()',
        init_each='if not exists: del d[k1]',
        measure='''
if k1 in d:
    d[k1][k2] = v
else:
    d[k1] = {k2: v}
''',
    ),
    dict(
        name='get',
        init_once='d = d1.copy()',
        init_each='if not exists: del d[k1]',
        measure='''
vs = d.get(k1)
if vs is None:
    d[k1] = {k2: v}
else:
    vs[k2] = v
''',
    ),
    dict(
        name='try',
        init_once='d = d1.copy()',
        init_each='if not exists: del d[k1]',
        measure='''
try:
    d[k1][k2] = v
except KeyError:
    d[k1] = {k2: v}

''',
    ),
]

### main

def main():
    gc.disable()

    for env in envs:
        print('\n{}:'.format(env))
        exec(env)
        results = []
        base_seconds = None

        for test in tests:
            init_once = compile(test.get('init_once') or defaults['init_once'], '<string>', 'exec')
            init_each = compile(test.get('init_each') or defaults['init_each'], '<string>', 'exec')
            measure = compile(test['measure'], '<string>', 'exec')
            repeat = test.get('repeat') or defaults['repeat']

            exec(init_once)
            seconds = 0

            for _ in xrange(repeat):
                exec(init_each)

                start = time.time()
                exec(measure)
                seconds += time.time() - start

            results.append((seconds, test['name']))
            if base_seconds is None:
                base_seconds = seconds

        print('speedup   seconds  option')
        for seconds, name in sorted(results):
            print('{:6d}%  {:.6f}  {}'.format(
                int(round(100 * (base_seconds - seconds) / base_seconds)),
                seconds,
                name,
            ))

if __name__ == '__main__':
    main()
