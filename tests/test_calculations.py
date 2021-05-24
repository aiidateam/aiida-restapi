# -*- coding: utf-8 -*-
""" Tests for calculations

"""
import os
from aiida.plugins import DataFactory, CalculationFactory
from aiida.engine import run
from aiida.orm import SinglefileData

from . import TEST_DIR


def test_process(restapi_code):
    """Test running a calculation
    note this does not test that the expected outputs are created of output parsing"""

    # Prepare input parameters
    DiffParameters = DataFactory('restapi')
    parameters = DiffParameters({'ignore-case': True})

    file1 = SinglefileData(
        file=os.path.join(TEST_DIR, 'input_files', 'file1.txt'))
    file2 = SinglefileData(
        file=os.path.join(TEST_DIR, 'input_files', 'file2.txt'))

    # set up calculation
    inputs = {
        'code': restapi_code,
        'parameters': parameters,
        'file1': file1,
        'file2': file2,
        'metadata': {
            'options': {
                'max_wallclock_seconds': 30
            },
        },
    }

    result = run(CalculationFactory('restapi'), **inputs)
    computed_diff = result['restapi'].get_content()

    assert 'content1' in computed_diff
    assert 'content2' in computed_diff
