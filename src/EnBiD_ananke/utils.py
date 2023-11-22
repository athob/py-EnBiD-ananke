#!/usr/bin/env python
"""
Module miscellaneous utilities
"""
import subprocess

__all__ = ['Singleton', 'execute']


class Singleton(type):
    """
    Singleton metaclass.
    Credit https://stackoverflow.com/q/6760685
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def _execute_generator(cmd, **kwargs):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, **kwargs)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def execute(cmd, verbose=True, **kwargs):
    """
    Credit https://stackoverflow.com/a/4417735
    """
    for path in _execute_generator(cmd, **kwargs):
        print(path, end="") if verbose else None


if __name__ == '__main__':
    pass
