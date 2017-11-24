# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals, print_function, division

import os
import subprocess
from datetime import datetime
import tempfile

import regex

from django.conf import settings
from django.db import connection

from celery.worker.autoscale import Autoscaler
from celery.five import monotonic

AUTOSCALE_RUN_EVERY_SEC = os.environ.get('AUTOSCALE_RUN_EVERY_SEC', 5)

AUTOSCALE_MAX_CPU_USAGE = os.environ.get('AUTOSCALE_MAX_CPU_USAGE', 75)
AUTOSCALE_MAX_USED_MEMORY = os.environ.get('AUTOSCALE_MAX_USED_MEMORY', 75)

AUTOSCALE_MAX_WORKER_INC_BY = os.environ.get('AUTOSCALE_MAX_WORKER_INC_BY', 4)
AUTOSCALE_MAX_WORKER_DEC_BY = os.environ.get('AUTOSCALE_MAX_WORKER_DEC_BY', 4)

AUTOSCALE_DB_QUERY_EXECUTION_MS = os.environ.get('AUTOSCALE_DB_QUERY_EXECUTION_MS', 10)


class SuperAutoscaler(Autoscaler):
    last_call = monotonic()

    cpu_stats = (0.0, 0.0, 0.0)
    max_cpu_bound_workers = 0
    max_memory_bound_workers = 0
    max_db_bound_workers = 0

    initial_memory_usage = None

    re_total = regex.compile(r'MemTotal:\s+(?P<total>\d+)\s+kB', flags=regex.V0)
    re_available = regex.compile(r'MemAvailable:\s+(?P<available>\d+)\s+kB', flags=regex.V0)

    def __init__(self, *args, **kwargs):
        super(SuperAutoscaler, self).__init__(*args, **kwargs)

        if settings.DEBUG is True:
            self._debug_log_file = tempfile.NamedTemporaryFile(prefix='autoscaler_', suffix='.log')

        # bootstrap
        self.initial_memory_usage = self._get_used_memory()

    def _debug(self, msg):
        if settings.DEBUG is True:
            print('{timestamp}: {msg}'.format(timestamp=datetime.now(), msg=msg), file=self._debug_log_file)

    def _maybe_scale(self, req=None):
        if self.should_run():
            self.collect_stats()

            self._debug(
                '_maybe_scale => CUR: (%s) CON: (%s,%s), Qty: %s, CPU: %s, Mem: %s, Db: %s' % (
                    self.processes, self.min_concurrency, self.max_concurrency, self.qty,
                    self.max_cpu_bound_workers, self.max_memory_bound_workers, self.max_db_bound_workers
                )
            )

            max_target_procs = min(
                self.qty, self.max_concurrency, self.max_cpu_bound_workers, self.max_memory_bound_workers,
                self.max_db_bound_workers
            )
            if max_target_procs > self.processes:
                n = min((max_target_procs - self.processes), AUTOSCALE_MAX_WORKER_INC_BY)
                self._debug('SCALE_UP => %s + %s = %s' % (self.processes, n, self.processes + n))
                self.scale_up(n)
                return True

            min_target_procs = max(self.min_concurrency, max_target_procs)
            if min_target_procs < self.processes:
                n = min((self.processes - min_target_procs), AUTOSCALE_MAX_WORKER_DEC_BY)
                self._debug('SCALE_DOWN => %s - %s = %s' % (self.processes, n, self.processes - n))
                self.scale_down(n)
                return True

    def collect_stats(self):
        self.max_cpu_bound_workers = self._check_cpu_usage()
        self.max_memory_bound_workers = self._check_used_memory()
        self.max_db_bound_workers = self._check_query_execution_time()

    def _check_cpu_usage(self):
        cpu_usage_data = subprocess.check_output(['grep', '-w', 'cpu', '/proc/stat']).split(' ')

        cur_stats = (float(cpu_usage_data[2]), float(cpu_usage_data[4]), float(cpu_usage_data[5]))

        cpu_usage = float(
            (self.cpu_stats[0] + self.cpu_stats[1] - cur_stats[0] - cur_stats[1]) * 100 /
            (self.cpu_stats[0] + self.cpu_stats[1] + self.cpu_stats[2] - cur_stats[0] - cur_stats[1] - cur_stats[2])
        )

        self.cpu_stats = cur_stats

        if self.processes > 0:
            cpu_usage_per_proc = cpu_usage / self.processes
            max_cpu_bound_workers = int(
                ((AUTOSCALE_MAX_CPU_USAGE - cpu_usage) / cpu_usage_per_proc) + self.processes
            )
            target_cpu_bound_workers = min(max_cpu_bound_workers, self.max_concurrency)
        else:
            target_cpu_bound_workers = self.min_concurrency
            cpu_usage_per_proc = -1

        self._debug(
            '_cpu => %s %s %s %s' % (
                AUTOSCALE_MAX_CPU_USAGE, cpu_usage, cpu_usage_per_proc, target_cpu_bound_workers
            )
        )

        return target_cpu_bound_workers

    def _check_used_memory(self):
        used_memory = self._get_used_memory()

        if self.processes > 0:
            mem_usage_per_proc = (used_memory - self.initial_memory_usage) / self.processes
            max_mem_bound_workers = int(
                ((AUTOSCALE_MAX_USED_MEMORY - used_memory) / mem_usage_per_proc) + self.processes
            )
            target_mem_bound_workers = min(max_mem_bound_workers, self.max_concurrency)
        else:
            target_mem_bound_workers = self.min_concurrency
            mem_usage_per_proc = -1

        self._debug(
            '_mem => %s %s %s %s' % (
                AUTOSCALE_MAX_CPU_USAGE, used_memory, mem_usage_per_proc, target_mem_bound_workers
            )
        )

        return target_mem_bound_workers

    def _get_used_memory(self):
        with open('/proc/meminfo', 'rb') as f:
            mem = f.read()
        mem_ratio = (
            int(self.re_available.search(mem).group("available")) / int(self.re_total.search(mem).group("total"))
        )
        used_memory = 100 * (1 - mem_ratio)
        return used_memory

    def _check_query_execution_time(self):
        with connection.cursor() as cursor:
            start_time = monotonic()
            cursor.execute('SELECT id FROM orgs_org ORDER BY id LIMIT 1')
            cursor.fetchone()

            total_time = (monotonic() - start_time) * 1000.0

        if total_time < AUTOSCALE_DB_QUERY_EXECUTION_MS:
            # if we are not limited by the db, scale to max_concurrency
            target_db_bound_workers = self.max_concurrency
        else:
            target_db_bound_workers = self.min_concurrency

        self._debug(
            '_db => %s %s %s' % (
                AUTOSCALE_DB_QUERY_EXECUTION_MS, total_time, target_db_bound_workers
            )
        )
        return target_db_bound_workers

    def should_run(self):
        current_time = monotonic()

        if current_time - self.last_call > AUTOSCALE_RUN_EVERY_SEC:
            self.last_call = current_time
            return True
        else:
            return False
