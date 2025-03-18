#!/usr/bin/env python
"""
Module utilities using built-in implementation
"""
import subprocess
import re

__all__ = ['Singleton', 'execute', 'get_version_of_command']


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


def _execute_generator(args, **kwargs):
    popen = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, **kwargs)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, args)


def execute(args, verbose=True, **kwargs):
    """
    Run the command described by args, and use
    verbose kwarg to redirect output/error stream
    to python output stream.
    Credit https://stackoverflow.com/a/4417735
    """
    for path in _execute_generator(args, **kwargs):
        print(path, end="") if verbose else None


def get_version_of_command(cmd):
    return re.findall("((?:[0-9]+\.)+[0-9]+)",
                      str(subprocess.check_output([cmd, '--version'])))[0]


if __name__ == '__main__':
    raise NotImplementedError()
