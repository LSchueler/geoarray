#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author
------
David Schaefer

Purpose
-------
This module provides initializer function for core.GeoArray
"""

import numpy as np
from gdalfuncs import _fromFile
from core import GeoArray

def array(data, dtype=None, yorigin=None, xorigin=None, origin=None,
          fill_value=None, cellsize=None, proj=None, mode=None, copy=False):
    """
    Arguments
    ---------
    data         : numpy.ndarray  # data to wrap

    Optional Arguments
    ------------------
    dtype        : str/np.dtype                  # type of the returned grid
    yorigin      : int/float, default: 0         # y-value of the grid's origin
    xorigin      : int/float, default: 0         # x-value of the grid's origin
    origin       : {"ul","ur","ll","lr"},        # position of the origin. One of:
                   default: "ul"                 #     "ul" : upper left corner
                                                 #     "ur" : upper right corner
                                                 #     "ll" : lower left corner
                                                 #     "lr" : lower right corner
    fill_value   : inf/float                     # fill or fill value
    cellsize     : int/float or 2-tuple of those # cellsize, cellsizes in y and x direction
    proj         : dict/None                     # proj4 projection parameters
    copy         : bool                          # create a copy of the given data
    
    Returns
    -------
    GeoArray

    Purpose
    -------
    Create a GeoArray from data.
    """

    if isinstance(data, GeoArray):
        dtype      = dtype or data.dtype
        yorigin    = yorigin or data.yorigin
        xorigin    = xorigin or data.xorigin
        origin     = origin or data.origin
        fill_value = fill_value or data.fill_value
        cellsize   = cellsize or data.cellsize
        proj       = proj or data.proj
        mode       = mode or data.mode
        

    return GeoArray(
        data       = np.array(data, dtype=dtype, copy=copy), 
        yorigin    = yorigin or 0,
        xorigin    = xorigin or 0,
        origin     = origin or "ul",
        fill_value = fill_value,
        cellsize   = cellsize or (1,1),
        proj       = proj,
        mode       = mode,
    )

def zeros(shape, dtype=np.float64, yorigin=0, xorigin=0, origin="ul",
          fill_value=None, cellsize=1, proj=None, mode=None):
    """
    Arguments
    ---------
    shape        : tuple          # shape of the returned grid

    Optional Arguments
    ------------------
    dtype        : str/np.dtype                  # type of the returned grid
    yorigin      : int/float                     # y-value of the grid's origin
    xorigin      : int/float                     # x-value of the grid's origin
    origin       : {"ul","ur","ll","lr"}         # position of the origin. One of:
                                                 #     "ul" : upper left corner
                                                 #     "ur" : upper right corner
                                                 #     "ll" : lower left corner
                                                 #     "lr" : lower right corner
    fill_value   : inf/float                     # fill or fill value
    cellsize     : int/float or 2-tuple of those # cellsize, cellsizes in y and x direction
    proj         : dict/None                     # proj4 projection parameters

    Returns
    -------
    GeoArray

    Purpose
    -------
    Return a new GeoArray of given shape and type, filled with zeros.
    """

    return GeoArray(
        data       = np.zeros(shape, dtype),
        yorigin    = yorigin,
        xorigin    = xorigin,
        origin     = origin,
        fill_value = fill_value,
        cellsize   = cellsize,
        proj       = proj,
        mode       = mode,
    )

def ones(shape, dtype=np.float64, yorigin=0, xorigin=0, origin="ul",
         fill_value=None, cellsize=1, proj=None, mode=None):
    """
    Arguments
    ---------
    shape        : tuple          # shape of the returned grid

    Optional Arguments
    ------------------
    dtype        : str/np.dtype                  # type of the returned grid
    yorigin      : int/float                     # y-value of the grid's origin
    xorigin      : int/float                     # x-value of the grid's origin
    origin       : {"ul","ur","ll","lr"}         # position of the origin. One of:
    fill_value   : inf/float                     # fill or fill value
    cellsize     : int/float or 2-tuple of those # cellsize, cellsizes in y and x direction
    proj         : dict/None                     # proj4 projection parameters

    Returns
    -------
    GeoArray

    Purpose
    -------
    Return a new GeoArray of given shape and type, filled with ones.
    """

    return GeoArray(
        data       = np.ones(shape, dtype),
        yorigin    = yorigin,
        xorigin    = xorigin,
        origin     = origin,
        fill_value = fill_value,
        cellsize   = cellsize,
        proj       = proj,
        mode       = mode,
    )

def full(shape, value, dtype=np.float64, yorigin=0, xorigin=0, origin="ul",
         fill_value=None, cellsize=1, proj=None, mode=None):
    """
    Arguments
    ---------
    shape        : tuple          # shape of the returned grid
    fill_value   : scalar         # fille value

    Optional Arguments
    ------------------
    dtype        : str/np.dtype                  # type of the returned grid
    yorigin      : int/float                     # y-value of the grid's origin
    xorigin      : int/float                     # x-value of the grid's origin
    origin       : {"ul","ur","ll","lr"}         # position of the origin. One of:
    fill_value   : inf/float                     # fill or fill value
    cellsize     : int/float or 2-tuple of those # cellsize, cellsizes in y and x direction
    proj         : dict/None                     # proj4 projection parameters

    Returns
    -------
    GeoArray

    Purpose
    -------
    Return a new GeoArray of given shape and type, filled with fill_value.
    """

    return GeoArray(
        data       = np.full(shape, value, dtype),
        yorigin    = yorigin,
        xorigin    = xorigin,
        origin     = origin,
        fill_value = fill_value,
        cellsize   = cellsize,
        proj       = proj,
        mode       = mode,
    )

def empty(shape, dtype=np.float64, yorigin=0, xorigin=0, origin="ul",
          fill_value=None, cellsize=1, proj=None, mode=None):
    """
    Arguments
    ----------
    shape        : tuple          # shape of the returned grid

    Optional Arguments
    ------------------
    dtype        : str/np.dtype                  # type of the returned grid
    yorigin      : int/float                     # y-value of the grid's origin
    xorigin      : int/float                     # x-value of the grid's origin
    origin       : {"ul","ur","ll","lr"}         # position of the origin. One of:
    fill_value   : inf/float                     # fill or fill value
    cellsize     : int/float or 2-tuple of those # cellsize, cellsizes in y and x direction
    proj         : dict/None                     # proj4 projection parameters

    Returns
    -------
    GeoArray

    Purpose
    -------
    Return a new empty GeoArray of given shape and type
    """

    return GeoArray(
        data       = np.empty(shape, dtype),
        yorigin    = yorigin,
        xorigin    = xorigin,
        origin     = origin,
        fill_value = fill_value,
        cellsize   = cellsize,
        proj       = proj,
        mode       = mode,
    )

def fromfile(fname):
    """
    Arguments
    ---------
    fname : str  # file name
    
    Returns
    -------
    GeoArray

    Purpose
    -------
    Create GeoArray from file

    """
    return GeoArray(**_fromFile(fname))
