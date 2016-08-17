#!/usr/bin/python
#
# Notes:
#
# The stats socket should be readable by the user running ganglia
# gmond process, which is usually unprivileged. One was is to use the
# default read-only stats socket (if server access is limited, say)
# and change the permissions to world writable
#
#  stats socket /tmp/haproxy mode 777
#

import os
import sys
import re
import socket

from optparse import OptionParser
from cStringIO import StringIO
from time import time

last_check = 0

def parse_stats(name):

    stats = get_stats()

    nparts = name.split('-')
    key = nparts.pop()
    svr = nparts.pop()
    # get rid of "haproxy"
    nparts.pop(0)
    svc = '-'.join(nparts)
    name = svc + '-' + svr

    try:
        return int(stats[name][key])
    except:
        return 0

def get_stats():
    global keys, stats_socket, last_check, stats

    if time() - last_check < 20:
        return stats

    buff = StringIO()
    end = time() + 15

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    try:
        client.connect(stats_socket)
        client.send('show stat' + '\n')

        while time() <=  end:
            data = client.recv(4096)
            if data:
                buff.write(data)
            else:
                break
    except Exception, e:
        raise
    finally:
        client.close()
    buff.seek(0)

    last_check = time()

    stats = {}

    lines = buff.read().split('\n')
    stats_keys = lines.pop(0).replace('# ','').split(',')
    for l in lines:
        if l == '':
            continue
        _stats = l.split(',')
        name = _stats[0]+'-'+_stats[1]
        stats[name] = {}
        for k in keys:
            if k in stats_keys:
                stats[name][k] = _stats[stats_keys.index(k)]
    return stats

def metric_init(params):
    global keys, stats_socket

    if 'keys' in params:
        keys = params['keys'].split(',')
    else:
        keys = ['qcur','scur','smax','stot','rate','rate_max']

    stats_socket = params['stats_socket']

    descriptors = []

    # find services in the stats
    stats = get_stats()

    for service in stats.keys():
        dees = []
        for px in keys:
            d = {'name': 'haproxy-%s-%s' %(service,px),
                'call_back': parse_stats,
                'time_max': 90,
                'value_type': 'uint',
                'units': 'requests',
                'slope': 'both',
                'format': '%d',
                'description': px,
                'groups': 'haproxy'}
            dees.append(d)
        descriptors.extend(dees)

    return descriptors

def metric_cleanup():
    '''Clean up the metric module.'''
    pass

#This code is for debugging and unit testing
if __name__ == '__main__':
    params = { 'stats_socket' : '/tmp/haproxy',
               'socket_timeout': 15,
               'groups' : 'haproxy',
               }

    descriptors = metric_init(params)

    for d in descriptors:
        v = d['call_back'](d['name'])
        print '%s,%u  (%s)' % (d['name'],  v, d['description'])
