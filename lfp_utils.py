import numpy as np
import os
from pathlib import Path
import shutil
import scipy
import time
import json
from .SpikeGLX_utils import *
from .SGLXMetaToCoords import *

class LFPRecording:
    def __init__(self, recording_dir, load_recording=False, load_downsampled_data=False):
        self.recording_dir = Path(recording_dir) # SGLX data
        self.lfp_data_dir = Path(recording_dir,'lfp') # folder for downsampled LFP output 
        self.downsampled_data_path = self.lfp_data_dir/'downsampled_data.npy' # path for downsampled data
        self.downsampled_timestamps_path = self.lfp_data_dir/'downsampled_timestamps.npy' # path for downsampld timestamps

        self.get_params()
        self.raw_data_loaded = False

        if load_recording:
            self.load_recording()
        if load_downsampled_data:
            if not self.downsampled_data_path.exists():
                if not self.raw_data_loaded:
                    self.load_recording()
                self.downsample_data(desired_sample_rate=1500,save_output=True)
            self.load_downsampled_data()
    
    def get_params(self):
        files = os.listdir(self.recording_dir)
        binfile = ""
        for file in files:
            if 'meta' in file:
                metapath = file
            if 'bin' in file:
                binfile = file             
        metapath = os.path.join(self.recording_dir,metapath)
        # parse metafile
        with open(metapath) as f:
            lines = f.readlines()
            for line in lines:
                if 'fileTimeSecs' in line:
                    fileTimeSecs = float(line.split('=')[1])
        (probe_type, sample_rate, n_channels, ref_channels, uVPerBit, useGeom) = EphysParams(metapath)
        self.params = {'probe_type': probe_type,
                'sample_rate': sample_rate,
                'n_channels': n_channels,
                'ref_channels': ref_channels,
                'uVPerBit': uVPerBit,
                'useGeom': useGeom,
                'binpath': os.path.join(self.recording_dir,binfile),
                'fileTimeSecs': fileTimeSecs,
                'metapath': metapath,
                }
        self.x_coords, self.y_coords, self.shank_labels = MetaToCoords(metaFullPath=Path(self.params['metapath']), outType=4, showPlot=False)
    
    def load_recording(self):
        print(f"Loading Raw Recording")
        self.rawdata = np.memmap(self.params['binpath'], dtype='int16', mode='r')
        self.data = np.reshape(self.rawdata, (int(self.rawdata.size/self.params['n_channels']), self.params['n_channels']))
        self.params['n_samples'] = self.data.shape[0]
        self.timestamps,self.timestep = np.linspace(0,self.params['fileTimeSecs'],num=self.params['n_samples'],retstep=True)
        self.raw_data_loaded = True

    def downsample_data(self,desired_sample_rate=1500,save_output=True):
        print(f"Downsampling data {self.recording_dir.name}")
        downsampling_factor = round(self.params['sample_rate']/desired_sample_rate)
        self.downsampled_sampling_rate = self.params['sample_rate']/downsampling_factor
        sample_indices = np.arange(0,self.params['n_samples'],downsampling_factor)
        self.downsampled_data = self.data[sample_indices]
        self.downsampled_data = self.downsampled_data * self.params['uVPerBit'] # convert to uV after downsampling to save time
        self.downsampled_timestamps = self.timestamps[sample_indices]

        if save_output:
            np.save(self.downsampled_data_path,self.downsampled_data,allow_pickle=False)
            np.save(self.downsampled_timestamps_path,self.downsampled_timestamps,allow_pickle=False)

        return self.downsampled_data,self.downsampled_timestamps,self.downsampled_sampling_rate

    def load_downsampled_data(self):
        print(f"Loading Downsampled Data")
        self.downsampled_data = np.load(self.downsampled_data_path, mmap_mode='r')
        self.downsampled_timestamps = np.load(self.downsampled_timestamps_path, mmap_mode='r')
        self.downsampled_sampling_rate = 1/np.mean(np.diff(self.downsampled_timestamps[1:-1]))

def lfp_power(data,sos,SD=None):
    """SD = in samples"""
    lfp = scipy.signal.sosfiltfilt(sos, data)
    power = np.abs(np.imag(scipy.signal.hilbert(lfp)))
    power = scipy.ndimage.gaussian_filter(power,SD,order=0) 
    return power
