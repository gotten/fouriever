from __future__ import division


# =============================================================================
# IMPORTS
# =============================================================================

import astropy.io.fits as pyfits
import matplotlib.pyplot as plt
import numpy as np

import os
import sys

from . import inst

observables_known = ['vis', 'vis2', 't3', 'kp']


# =============================================================================
# MAIN
# =============================================================================

class data():
    
    def __init__(self,
                 idir,
                 fitsfiles):
        """
        Parameters
        ----------
        idir: str
            Input directory where fits files are located.
        fitsfiles: list of str
            List of fits files which shall be opened.
        """
        
        self.idir = idir
        self.fitsfiles = fitsfiles
        
        self.inst_list = []
        self.data_list = []
        for i in range(len(self.fitsfiles)):
            inst_list, data_list = inst.open(idir=idir,
                                             fitsfile=self.fitsfiles[i],
                                             verbose=False)
            self.inst_list += inst_list
            self.data_list += data_list
        
        self.set_inst(inst=self.inst_list[0])
        self.set_observables(self.get_observables())
        
        return None
    
    def get_inst(self):
        """
        Returns
        -------
        inst_list: list of str
            List of instruments from which data was opened.
        """
        
        return self.inst_list
    
    def set_inst(self,
                 inst):
        """
        Parameters
        ----------
        inst: str
            Instrument which shall be selected.
        """
        
        if (inst in self.inst_list):
            self.inst = inst
            print('Selected instrument = '+self.inst)
            print('   Use self.set_inst(inst) to change the selected instrument')
        else:
            raise UserWarning(inst+' is an unknown instrument')
        
        return None
    
    def get_observables(self):
        """
        Returns
        -------
        observables: list of str
            List of observables available for currently selected instrument.
        """
        
        observables = []
        ww = np.where(np.array(self.inst_list) == self.inst)[0]
        for i in range(len(observables_known)):
            j = 0
            flag = True
            while (j < len(ww) and flag):
                if (observables_known[i] not in self.data_list[ww[j]][0].keys()):
                    flag = False
                j += 1
            if (flag == True):
                observables += [observables_known[i]]
        
        return observables
    
    def set_observables(self,
                        observables):
        """
        Parameters
        ----------
        observables: list of str
            List of observables which shall be selected.
        """
        
        observables_valid = self.get_observables()
        for i in range(len(observables)):
            if (observables[i] not in observables_valid):
                raise UserWarning(observables[i]+' is not a valid observable for the currently selected instrument')
        self.observables = observables
        print('Selected observables = '+str(self.observables))
        print('   Use self.set_observables(observables) to change the selected observables')
        
        return None
    
    def add_vis2cov(self,
                    odir):
        """
        Parameters
        ----------
        odir: str
            Output directory where fits files with covariance shall be saved
            to.
        """
        
        print('   Computing visibility amplitude correlations')
        
        if (not os.path.exists(odir)):
            os.makedirs(odir)
        
        data_list = []
        ww = np.where(np.array(self.inst_list) == self.inst)[0]
        for i in range(len(ww)):
            data_list += [self.data_list[ww[i]]]
        
        if (len(self.fitsfiles) != len(data_list)):
            raise UserWarning('All input fits files should contain data of the selected instrument')
        
        for i in range(len(self.fitsfiles)):
            Nwave = data_list[i][0]['wave'].shape[0]
            Nbase = data_list[i][0]['vis2'].shape[0]
            
            cor = np.diag(np.ones(Nwave*Nbase))
            covs = []
            for j in range(len(data_list[i])):
                dvis2 = data_list[i][j]['dvis2']
                cov = np.multiply(cor, dvis2.flatten()[:, None]*dvis2.flatten()[None, :])
                covs += [cov]
            covs = np.array(covs)
            
            hdul = pyfits.open(self.idir+self.fitsfiles[i])
            hdu0 = pyfits.ImageHDU(covs)
            hdu0.header['EXTNAME'] = 'VIS2COV'
            hdu0.header['INSNAME'] = self.inst
            hdul += [hdu0]
            hdul.writeto(odir+self.fitsfiles[i], output_verify='fix', overwrite=True)
        
        # plt.imshow(cor, origin='lower')
        # plt.xlabel('Index')
        # plt.ylabel('Index')
        # plt.title('Visibility amplitude correlation')
        # plt.show()
        # plt.close()
        
        return None
    
    def add_t3cov(self,
                  odir):
        """
        Parameters
        ----------
        odir: str
            Output directory where fits files with covariance shall be saved
            to.
        """
        
        print('   Computing closure phase correlations')
        
        if (not os.path.exists(odir)):
            os.makedirs(odir)
        
        data_list = []
        ww = np.where(np.array(self.inst_list) == self.inst)[0]
        for i in range(len(ww)):
            data_list += [self.data_list[ww[i]]]
        
        if (len(self.fitsfiles) != len(data_list)):
            raise UserWarning('All input fits files should contain data of the selected instrument')
        
        for i in range(len(self.fitsfiles)):
            t3mat = data_list[i][0]['t3mat'].copy()
            Nwave = data_list[i][0]['wave'].shape[0]
            Nbase = t3mat.shape[1]
            Ntria = t3mat.shape[0]
            
            trafo = np.zeros((Nwave*Ntria, Nwave*Nbase))
            for k in range(Ntria):
                for l in range(Nbase):
                    trafo[k*Nwave:(k+1)*Nwave, l*Nwave:(l+1)*Nwave] = np.diag(np.ones(Nwave))*t3mat[k, l]
            
            cor = np.dot(trafo, np.dot(np.diag(np.ones(Nwave*Nbase)), trafo.T))/3.
            covs = []
            for j in range(len(data_list[i])):
                dt3 = data_list[i][j]['dt3']
                cov = np.multiply(cor, dt3.flatten()[:, None]*dt3.flatten()[None, :])
                covs += [cov]
            covs = np.array(covs)
            
            hdul = pyfits.open(self.idir+self.fitsfiles[i])
            hdu0 = pyfits.ImageHDU(covs)
            hdu0.header['EXTNAME'] = 'T3COV'
            hdu0.header['INSNAME'] = self.inst
            hdul += [hdu0]
            hdul.writeto(odir+self.fitsfiles[i], output_verify='fix', overwrite=True)
        
        # plt.imshow(cor, origin='lower')
        # plt.xlabel('Index')
        # plt.ylabel('Index')
        # plt.title('Closure phase correlation')
        # plt.show()
        # plt.close()
        
        return None
    
    def add_cov(self,
                odir):
        
        """
        Parameters
        ----------
        odir: str
            Output directory where fits files with covariance shall be saved
            to.
        """
        
        print('Computing correlations')
        
        if (not os.path.exists(odir)):
            os.makedirs(odir)
        
        self.add_vis2cov(odir=odir)
        
        temp = self.idir
        self.idir = odir
        self.add_t3cov(odir=odir)
        self.idir = temp
        
        return None
