#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re, os
import gdal, osr
import numpy as np

# needs to be extended
_DRIVER_DICT = {
    ".tif" : "GTiff",
    ".asc" : "AAIGrid",
    ".bmp" : "BMP",
    # ".gif" : "GIF",   # the driver seems not to work...
    ".img" : "HFA",
    ".jpg" : "JPEG",
    # ".png" : "PNG",  
}

gdal.PushErrorHandler('CPLQuietErrorHandler')
#gdal.UseExceptions()

class _GeoGridBase(object):
    
    """
    The File Reader/Writer Base class. All reader/writer classes NEED 
    to inherit from _GeoGridBase. Its purpose is to garantee a common 
    interface on which _GeoGrid depends on. It give meaningful defaults
    to the child class attributes and ensure data state consistency.
    
    TODO:
        Implement an input arguments check
    """        
    def __init__(self,
            nbands=None,nrows=None, ncols=None,
            xllcorner=None, yllcorner=None,cellsize=None,
            dtype=None, data=None, nodata_value=None,        
            proj_params=None
    ): 
        self._data = data
        self._nodata_value = nodata_value
        self.dtype = dtype
        self.nbands = nbands if nbands else 1
        self.nrows = nrows
        self.ncols = ncols
        self.xllcorner = xllcorner
        self.yllcorner = yllcorner
        self.cellsize = cellsize
        self.proj_params = proj_params
        self.__consistentTypes()
        
    def __consistentTypes(self):
        """
           Reflect dtype changes
        """
        self._nodata_value = self.dtype(self._nodata_value)
        if self._data != None:
            self._data = self[:].astype(self._dtype)
       
    def _squeeze(self):
        """
           Squeeze the possibly 1-length first dimension for
           convinient indexing.
        """
        if self._data != None:
            try:
                return np.squeeze(self._data,0)
            except ValueError:
                return self._data

    def _getNodataValue(self):
        """
            nodata_value getter
        """
        return self._nodata_value

    def _setNodataValue(self,value):
        """
            nodata_value setter
            All nodata_values in the dataset will be changed accordingly.
            Stored data will be read from disk, so calling this
            property may be a costly operation
        """
        self[self[:] == self._nodata_value] = self.dtype(value)
        self._nodata_value = self.dtype(value)

    def _getShape(self):
        """
            shape getter
            1-length nbands will be skipped
        """
        if self.nbands > 1:
            return self.nbands, self.nrows, self.ncols
        return self.nrows, self.ncols

    def _getDataType(self):
        """
            dtype getter
        """
        return self._dtype

    
    def _setDataType(self,value):
        """
            dtype setter
            If the data is already read from file its type will be
            changed. __consistentTypes() is invoked
        """
        self._dtype = np.dtype(value).type
        self.__consistentTypes()
        
    def __getitem__(self,slc):
        """
            slicing operator invokes the data reading
            TODO: Implement a slice reading from file
        """
        if self._data == None:
            self._data = self.dtype(self._readData())
        return self._squeeze()[slc]
        
    def __setitem__(self,slc,value):
        if self._data == None:
            self[:]
        self._data[slc] = value

    def write(self,fname):
        _GridWriter(self).write(fname)
        
    nodata_value  = property(fget=lambda self:            self._getNodataValue(),
                             fset=lambda self, value:     self._setNodataValue(value))
    shape         = property(fget=lambda self:            self._getShape())
    dtype         = property(fget=lambda self:            self._getDataType(),
                             fset=lambda self, value:     self._setDataType(value))
    
class _DummyGrid(_GeoGridBase):
    """
        A simple dummy data class needed as reader attribute to
        _GeoGrid if data is given on initialisation
    """
    def __init__(self,*args,**kwargs):
        super(_DummyGrid,self).__init__(*args,**kwargs)
        
    def _readData(self):
        """
            returns an array filled with nodata_values
        """
        out = np.empty((self.nbands,self.nrows,self.ncols),dtype=self.dtype)
        out.fill(self.nodata_value)        
        return out
            
                
class _GdalGrid(_GeoGridBase):
    def __init__(self,fname,proj_params=None,dtype=None):
        self.fobj = self._open(fname)
        trans = self.fobj.GetGeoTransform()
        band = self.fobj.GetRasterBand(1)
        pparams = self._proj4Params() 
        
        super(_GdalGrid,self).__init__(
            nbands       = self.fobj.RasterCount,
            nrows        = self.fobj.RasterYSize,
            ncols        = self.fobj.RasterXSize,
            xllcorner    = trans[0],
            yllcorner    = self._yllcorner(trans[3],trans[5],self.fobj.RasterYSize),
            cellsize     = self._cellsize(trans[1],trans[5]),
            nodata_value = band.GetNoDataValue(),
            proj_params  = pparams if pparams else proj_params if proj_params else {},
            dtype        = dtype if dtype else gdal.GetDataTypeName(band.DataType),
        )

    def _open(self,fname):
        fobj = gdal.Open(fname)
        if fobj:
            return fobj
        raise IOError("Could not open file")
        
    def _readData(self):
        return self.fobj.ReadAsArray()
        
    def _yllcorner(self,yulcorner,cellsize,nrows):
        if cellsize < 0:
            return float(yulcorner) + (cellsize * nrows)
        return yulcorner
        
    def _cellsize(self,x_cellsize,y_cellsize):
        if abs(x_cellsize) == abs(y_cellsize):
            return abs(x_cellsize)
        raise NotImplementedError(
            "Diverging cellsizes in x and y direction are not allowed yet!")    
        
    def _proj4Params(self):
        srs = osr.SpatialReference()
        srs.ImportFromWkt(self.fobj.GetProjection())
        proj_string = srs.ExportToProj4()
        proj_params = filter(None,re.split("[+= ]",proj_string))
        return dict(zip(proj_params[0::2],proj_params[1::2]))

class _GridWriter(object):

    def __init__(self,fobj):
        self.fobj = fobj
        
    def _fnameExtension(self,fname):
        return os.path.splitext(fname)[-1].lower()

    def _getDriver(self,fext):
        if fext in _DRIVER_DICT:
            driver = gdal.GetDriverByName(_DRIVER_DICT[fext])
            metadata = driver.GetMetadata_Dict()
            if "YES" == metadata.get("DCAP_CREATE",metadata.get("DCAP_CREATECOPY")):
                return driver
            raise IOError("Datatype canot be written")            
        raise IOError("No driver found for filenmae extension '{:}'".format(fext))

    def _proj4String(self):
        return "+{:}".format(" +".join(
            ["=".join(pp) for pp in self.fobj.proj_params.items()])
        )
    

    def _writeGdalMemory(self):
        driver = gdal.GetDriverByName("MEM")
        out = driver.Create(
            "",self.fobj.ncols,self.fobj.nrows,self.fobj.nbands,
            gdal.GetDataTypeByName(self.fobj.dtype.__name__)
        )
        out.SetGeoTransform(
            (self.fobj.xllcorner,self.fobj.cellsize,0,
             self.fobj.yllcorner + (self.fobj.nrows * self.fobj.cellsize),
             0,self.fobj.cellsize*-1)
        )
        srs = osr.SpatialReference()
        srs.ImportFromProj4(self._proj4String())
        out.SetProjection(srs.ExportToWkt())
        for n in xrange(self.fobj.nbands):
            band = out.GetRasterBand(n+1)
            band.SetNoDataValue(float(self.fobj.nodata_value)) 
            band.WriteArray(self.fobj[:])
        out.FlushCache()
        return out

    def write(self,fname):
        memset = self._writeGdalMemory()
        fext = self._fnameExtension(fname)        
        outdriver = self._getDriver(fext)
        out = outdriver.CreateCopy(fname,memset,0)
        errormsg = gdal.GetLastErrorMsg()
        if errormsg or not out:
            raise IOError(errormsg)
                
    
if __name__ == "__main__":

    pass
    
    
