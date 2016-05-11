#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re, os
import gdal, osr
import numpy as np
# import geoarray as ga


# should be extended, for available options see:
# http://www.gdal.org/formats_list.html
_DRIVER_DICT = {
    ".tif" : "GTiff",
    ".asc" : "AAIGrid",
    ".img" : "HFA",
    ".png" : "PNG",
}

# type mapping: there is no boolean data type in GDAL
TYPEMAP = {
    "uint8"      : 1,
    "int8"       : 1,
    "uint16"     : 2,
    "int16"      : 3,
    "uint32"     : 4,
    "int32"      : 5,
    "float32"    : 6,
    "float64"    : 7,
    "complex64"  : 10,
    "complex128" : 11,
    1            : "int8",
    2            : "uint16",
    3            : "int16",
    4            : "uint32",
    5            : "int32",
    6            : "float32",
    7            : "float64",
    10           : "complex64",
    11           : "complex128",
    
}

COLOR_DICT = {
    1 : "L",
    2 : "P",
    3 : "R",
    4 : "G",
    5 : "B",
    6 : "A",
    7 : "H",
    8 : "S",
    9 : "V",
    10 : "C",
    11 : "M",
    12 : "Y",
    13 : "K",
    14 : "Y",
    15 : "Cb",
    16 : "Cr",
}

COLOR_MODE_LIST = (
    "L", "P", "RGB", "RGBA", "CMYK", "HSV", "YCbCr"
)
 
gdal.UseExceptions()
gdal.PushErrorHandler('CPLQuietErrorHandler')

class _Projection(object):
    def __init__(self, arg):

        self._srs = osr.SpatialReference()

        if isinstance(arg, int):
            self._srs.ImportFromProj4("+init=epsg:{:}".format(arg))
        elif isinstance(arg, dict):
            params =  "+{:}".format(" +".join(
                ["=".join(map(str, pp)) for pp in arg.items()])
            )
            self._srs.ImportFromProj4(params)
        elif isinstance(arg, str):
            self._srs.ImportFromWkt(arg)
        elif isinstance(arg, _Projection):
            self._srs.ImportFromWkt(arg.getWkt())
            
    def getProj4(self):
        tmp = self._srs.ExportToProj4()
        proj = [x for x in re.split("[+= ]", tmp) if x]
        return dict(zip(proj[0::2], proj[1::2]))
        
    def getWkt(self):
        return self._srs.ExportToWkt()

    def getReference(self):
        if str(self._srs):
            return self._srs

    def __str__(self):
        return str(self.getProj4())

    def __repr__(self):
        return str(self.getProj4())
    
class _Transformer(object):
    def __init__(self, sproj, tproj):
        """
        Arguments
        ---------
        sproj, tproj : Projection
        
        Purpose
        -------
        Encapsulates the osr Cordinate Transformation functionality
        """
        self._tx = osr.CoordinateTransformation(
            sproj.getReference(), tproj.getReference()
        )

    def __call__(self, y, x):
        try:
            xt, yt, _ = self._tx.TransformPoint(x, y)
        except NotImplementedError:
            raise AttributeError("Projections not correct or given!")
        return yt, xt

def _fromFile(fname):
    """
    Parameters
    ----------
    fname : str  # file name
    
    Returns
    -------
    GeoArray

    Purpose
    -------
    Create GeoArray from file

    """
    
    fobj = gdal.OpenShared(fname)
    if fobj:
        return _fromDataset(fobj)
    raise IOError("Could not open file: {:}".format(fname))

def _getColorMode(fobj):

    tmp = []
    for i in xrange(fobj.RasterCount):
        color = fobj.GetRasterBand(i+1).GetColorInterpretation() 
        tmp.append(COLOR_DICT.get(color, "L"))
    return ''.join(sorted(set(tmp), key=tmp.index))
   
def _fromDataset(fobj):
    
    rasterband = fobj.GetRasterBand(1)
    geotrans   = fobj.GetGeoTransform()
    
    return {
        "data"       : fobj.ReadAsArray(),
        "yorigin"    : geotrans[3],
        "xorigin"    : geotrans[0],
        "origin"     : "ul",
        "fill_value" : rasterband.GetNoDataValue(),
        "cellsize"   : (geotrans[5], geotrans[1]),
        "proj"       : fobj.GetProjection(),
        "mode"       : _getColorMode(fobj),
        "fobj"       : fobj,
    }

def _getDataset(grid):

    if grid._fobj:
        return grid._fobj
    
    driver = gdal.GetDriverByName("MEM")
        
    out = driver.Create(
        "", grid.ncols, grid.nrows, grid.nbands, TYPEMAP[str(grid.dtype)]
    )

    out.SetGeoTransform(
        (
            grid.bbox["xmin"], abs(grid.cellsize[1]), 0,
            grid.bbox["ymax"], 0, abs(grid.cellsize[0])*-1)
    )
    out.SetProjection(grid.proj.getWkt())
    for n in xrange(grid.nbands):
        band = out.GetRasterBand(n+1)
        band.SetNoDataValue(float(grid.fill_value))
        band.WriteArray(grid[n] if grid.ndim > 2 else grid)
            
    return out

def _warp(grid, proj, max_error=0.125):

    bbox = grid.bbox
    trans = _Transformer(grid.proj, _Projection(proj))
    uly, ulx = trans(bbox["ymax"], bbox["xmin"])
    lry, lrx = trans(bbox["ymin"], bbox["xmax"])
    ury, urx = trans(bbox["ymax"], bbox["xmax"])
    lly, llx = trans(bbox["ymin"], bbox["xmin"])

    # Calculate cellsize, i.e. same number of cells along the diagonal.
    sdiag = np.sqrt(grid.nrows**2 + grid.ncols**2)
    # tdiag = np.sqrt((uly - lry)**2 + (lrx - ulx)**2)
    tdiag = np.sqrt((lly - ury)**2 + (llx - urx)**2)
    tcellsize = tdiag/sdiag
    
    # number of cells
    ncols = int(abs(round((max(urx, lrx) - min(ulx, llx))/tcellsize)))
    nrows = int(abs(round((max(ury, lry) - min(uly, lly))/tcellsize)))
    
    return {
        "shape"      : (grid.nbands, nrows, ncols),
        "value"      : grid.fill_value,
        "fill_value" : grid.fill_value,
        "dtype"      : grid.dtype,
        "yorigin"    : max(uly, ury, lly, lry),
        "xorigin"    : min(ulx, urx, llx, lrx),
        "origin"     : "ul",
        "cellsize"   : (-tcellsize, tcellsize),
        "proj"       : proj
    }

def _warpTo(source, target, max_error=0.125):

    if target.ndim == 1:
        target = target[None,:]
    if target.ndim < source.ndim:
        target = np.broadcast_to(
            target, source.shape[:-len(target.shape)]+target.shape, subok=True
        )

    target = np.array(target, dtype=source.dtype, copy=True, subok=True)
    target[target.mask] = source.fill_value
    target.fill_value = source.fill_value
        
    out = _getDataset(target)
    resampling = gdal.GRA_NearestNeighbour
    
    gdal.ReprojectImage(
        _getDataset(source), out,
        None, None,
        resampling, 
        0.0, max_error
    )
    return _fromDataset(out)

def _toFile(geoarray, fname):
    """
    Arguments
    ---------
    fname : str  # file name
    
    Returns
    -------
    None
    
    Purpose
    -------
    Write GeoArray to file. The output dataset type is derived from
    the file name extension. See _DRIVER_DICT for implemented formats.
    """
 
    def _fnameExtension(fname):
        return os.path.splitext(fname)[-1].lower()

    def _getDriver(fext):
        """
        Guess driver from file name extension
        """
        if fext in _DRIVER_DICT:
            driver = gdal.GetDriverByName(_DRIVER_DICT[fext])
            metadata = driver.GetMetadata_Dict()
            if "YES" == metadata.get("DCAP_CREATE",metadata.get("DCAP_CREATECOPY")):
                return driver
            raise IOError("Datatype canot be written")
        raise IOError("No driver found for filename extension '{:}'".format(fext))

    def _getDatatype(driver):
        tnames = tuple(driver.GetMetadata_Dict()["DMD_CREATIONDATATYPES"].split(" "))
        types = tuple(gdal.GetDataTypeByName(t) for t in tnames)
        tdict = tuple((gdal.GetDataTypeSize(t), t) for t in types)
        otype = max(tdict, key=lambda x: x[0])[-1]
        return np.dtype(TYPEMAP[otype])

        
    dataset = _getDataset(geoarray)
    driver = _getDriver(_fnameExtension(fname))
    driver.CreateCopy(fname, dataset, 0)
