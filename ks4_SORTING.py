from kilosort import run_kilosort
from kilosort.io import load_probe
import os
from pathlib import Path
from SGLXMetaToCoords import MetaToCoords
# import numpy as np
# import pandas as pd

def find_sessions(session_string):
    cgtdata_path = os.path.join('D:\\','CGT_OUT')
    run_dirs = next(os.walk(cgtdata_path))[1]
    runs = []
    for dir in run_dirs:
        if str(session_string) in dir:
            runs.append(dir) # run folder name including g0 but not imec0 etc
    if len(runs)>0:
        print(f'Runs found: {runs}')
    else:
        print('NO RUNS FOUND')
    
    recording_paths = []
    for run in runs:
        session_path = os.path.join(cgtdata_path,f'{run}')
        probedirs = next(os.walk(session_path))[1] # lists all folders within the session folder, should be one for each probe
        for probedir in probedirs:
            recording_paths.append(os.path.join(session_path,probedir))

    print(f"Recordings found: {recording_paths}")
    return recording_paths

def make_channelmap(recording_path):
    files = os.listdir(recording_path)
    meta_paths = []
    for file in files:
        if 'meta' in file:
            meta_path = Path(os.path.join(recording_path,file))
            meta_paths.append(meta_path)
            MetaToCoords(metaFullPath=meta_path, outType=1, showPlot=False) # ks channel map
            MetaToCoords(metaFullPath=meta_path, outType=4, showPlot=False) # true, numpy array of coords saved
            print(f"Made Channel Map {file}")

def find_channelmap(recording_path):
    files = os.listdir(recording_path)
    found_map = False
    for file in files:
        if 'kilosortChanMap_TRUE' in file:
            found_map = True
            return Path(os.path.join(recording_path,file))
    if not found_map:
        print(f"Didn't find channel map for {recording_path}")

def main():
    recording_paths = find_sessions("20230904_CWF3_00_g0")

    for recording_path in recording_paths:
        make_channelmap(recording_path)
        settings = {'data_dir': recording_path, 'n_chan_bin': 385, 'nblocks':0} # set nblocks to 0 to disable drift correction
        probe_dict = load_probe(find_channelmap(recording_path))
        run_kilosort(settings=settings, probe=probe_dict)
    
if __name__=="__main__":
    main()