# -*- coding: utf-8 -*-
"""
Sony .spi3d LUT Format Input / Output Utilities
===============================================

Defines *Sony* *.spi3d* *LUT* Format related input / output utilities objects.

-   :func:`colour.io.read_LUT_SonySPI3D`
-   :func:`colour.io.write_LUT_SonySPI3D`
"""

from __future__ import division, unicode_literals

import numpy as np

from colour.constants import DEFAULT_INT_DTYPE
from colour.io.luts import LUT3D, LUTSequence
from colour.io.luts.common import parse_array, path_to_title
from colour.utilities import as_float_array, usage_warning

__author__ = 'Colour Developers'
__copyright__ = 'Copyright (C) 2013-2019 - Colour Developers'
__license__ = 'New BSD License - https://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Colour Developers'
__email__ = 'colour-science@googlegroups.com'
__status__ = 'Production'

__all__ = ['read_LUT_SonySPI3D', 'write_LUT_SonySPI3D']


def read_LUT_SonySPI3D(path):
    """
    Reads given *Sony* *.spi3d* *LUT* file.

    Parameters
    ----------
    path : unicode
        *LUT* path.

    Returns
    -------
    LUT3D or LUT3x1D
        :class:`LUT3D` or :class:`LUT3x1D` class instance.

    Examples
    --------
    Reading a 3D *Sony* *.spi3d* *LUT*:

    >>> import os
    >>> path = os.path.join(
    ...     os.path.dirname(__file__), 'tests', 'resources', 'sony_spi3d',
    ...     'Colour_Correct.spi3d')
    >>> print(read_LUT_SonySPI3D(path))
    LUT3D - Colour Correct
    ----------------------
    <BLANKLINE>
    Dimensions : 3
    Domain     : [[ 0.  0.  0.]
                  [ 1.  1.  1.]]
    Size       : (4, 4, 4, 3)
    Comment 01 : Adapted from a LUT generated by Foundry::LUT.
    """

    title = path_to_title(path)
    domain_min, domain_max = np.array([0, 0, 0]), np.array([1, 1, 1])
    size = 2
    indexes = []
    table = []
    comments = []

    with open(path) as spi3d_file:
        lines = filter(None, (line.strip() for line in spi3d_file.readlines()))
        for line in lines:
            if line.startswith('#'):
                comments.append(line[1:].strip())
                continue

            tokens = line.split()
            if len(tokens) == 3:
                assert len(set(tokens)) == 1, (
                    'Non-uniform "LUT" shape is unsupported!')

                size = DEFAULT_INT_DTYPE(tokens[0])
            if len(tokens) == 6:
                indexes.append(parse_array(tokens[:3]))
                table.append(parse_array(tokens[3:]))

    assert np.array_equal(
        indexes,
        DEFAULT_INT_DTYPE(LUT3D.linear_table(size) * (size - 1)).reshape(
            (-1, 3))), 'Indexes do not match expected "LUT3D" indexes!'

    table = as_float_array(table).reshape([size, size, size, 3])

    return LUT3D(
        table, title, np.vstack([domain_min, domain_max]), comments=comments)


def write_LUT_SonySPI3D(LUT, path, decimals=7):
    """
    Writes given *LUT* to given *Sony* *.spi3d* *LUT* file.

    Parameters
    ----------
    LUT : LUT3D
        :class:`LUT3D` or :class:`LUTSequence` class instance to write at given
        path.
    path : unicode
        *LUT* path.
    decimals : int, optional
        Formatting decimals.

    Returns
    -------
    bool
        Definition success.

    Warning
    -------
    -   If a :class:`LUTSequence` class instance is passed as ``LUT``, the
        first *LUT* in the *LUT* sequence will be used.

    Examples
    --------
    Writing a 3D *Sony* *.spi3d* *LUT*:

    >>> LUT = LUT3D(
    ...     LUT3D.linear_table(16) ** (1 / 2.2),
    ...     'My LUT',
    ...     np.array([[0, 0, 0], [1, 1, 1]]),
    ...     comments=['A first comment.', 'A second comment.'])
    >>> write_LUT_SonySPI3D(LUT, 'My_LUT.cube')  # doctest: +SKIP
    """

    if isinstance(LUT, LUTSequence):
        LUT = LUT[0]
        usage_warning('"LUT" is a "LUTSequence" instance was passed, '
                      'using first sequence "LUT":\n'
                      '{0}'.format(LUT))

    assert not LUT.is_domain_explicit(), '"LUT" domain must be implicit!'

    assert isinstance(LUT, LUT3D), '"LUT" must be either a 3D "LUT"!'

    assert np.array_equal(LUT.domain, np.array([
        [0, 0, 0],
        [1, 1, 1],
    ])), '"LUT" domain must be [[0, 0, 0], [1, 1, 1]]!'

    def _format_array(array):
        """
        Formats given array as a *Sony* *.spi3d* data row.
        """

        return '{1:d} {2:d} {3:d} {4:0.{0}f} {5:0.{0}f} {6:0.{0}f}'.format(
            decimals, *array)

    with open(path, 'w') as spi3d_file:
        spi3d_file.write('SPILUT 1.0\n')

        spi3d_file.write('3 3\n')

        spi3d_file.write('{0} {0} {0}\n'.format(LUT.size))

        indexes = DEFAULT_INT_DTYPE(
            LUT.linear_table(LUT.size) * (LUT.size - 1)).reshape([-1, 3])
        table = LUT.table.reshape([-1, 3])

        for i, row in enumerate(indexes):
            spi3d_file.write('{0}\n'.format(
                _format_array(list(row) + list(table[i]))))

        if LUT.comments:
            for comment in LUT.comments:
                spi3d_file.write('# {0}\n'.format(comment))

    return True
