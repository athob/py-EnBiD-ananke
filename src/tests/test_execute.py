#!/usr/bin/env python
import random

from ..EnBiD_ananke._builtin_utils import execute
from .utils import list_stdout


def _test_verbose(verbose):
    lines = [f'test{random.randrange(100)}' for n in range(10)]
    to_printf = "\n".join(lines)
    with list_stdout() as L:
        execute(['printf', f'{to_printf}'], verbose=verbose)
    return L, lines
    

def test_verbose_true():
    L, lines = _test_verbose(True)
    assert L == lines


def test_verbose_false():
    L, _ = _test_verbose(False)
    assert not(L)


if __name__ == '__main__':
    pass
