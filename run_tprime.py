"""CKW 12/27/2022
This script uses absolute paths stored in the CatGT .fyi file. If you move your CatGT output, you need to update the fyi file."""

import os
import numpy as np

def get_spikes(sorter_path):
    spiketimes = np.load(os.path.join(sorter_path,'spike_times.npy'))
    spike_times_path = os.path.join(sorter_path,'spike_times.txt')
    with open(spike_times_path, 'w') as f:
        for spiketime in spiketimes:
            f.write(f'{int(spiketime)}\n')
    print('converted npy spiketimes to .txt file')
    return spike_times_path

def gen_tprime(run_name,catgt_output_path,sorter=None):
    """Generates the command prompt line that will run tprime (v1.7) for the given run name.
    :param run_name: name of the run to generate the command for
    :return: command prompt command
    """
    root = os.path.join(catgt_output_path, f'{run_name}')

    files = os.listdir(root)
    for file in files:
        if 'fyi' in file:
            fyi_file = file

    fyi_path = os.path.join(root, fyi_file) # catgt outputs a helpful file to tell you where everything is
    fyi = {}
    with open(fyi_path) as f:
        lines = f.readlines()
    for line in lines:
        fyi[line.split('=')[0]] = line.split('=')[1].replace('\n','')

    probe_paths = [value for key,value in fyi.items() if 'outpath_probe' in key.lower()] # list of probe dir paths
    sync_imec = [value for key,value in fyi.items() if 'sync_imec' in key.lower()] # list of paths to the imec sync time txt files
    sync_ni = fyi['sync_ni'] # path
    events_ni = [value for key,value in fyi.items() if 'times_ni' in key.lower()] # list of paths
    print(events_ni)

    ni_events = ''
    for event_path in events_ni:
        out_file = f'{event_path[0:-4]}_synced.txt' # -4 shouldn't be hardcoded here but c'est la vie
        ni_events += f'-events=1,{event_path},{out_file} '
    print(ni_events)

    if len(sync_imec)==1:
        command = f'TPrime -syncperiod=1.0 -tostream={sync_imec[0]} -fromstream=1,{sync_ni} {ni_events}'
    else:
        addtl_probe_streams = ''
        addtl_probe_events = ''
        for imec_path in sync_imec:
            if sync_imec.index(imec_path)>0:
                try:
                    imec_spiketimes = get_spikes(os.path.join(probe_paths[sync_imec.index(imec_path)],sorter)) # extract the SORTED spiketimes from this probe
                    stream_index = sync_imec.index(imec_path)+1 # stream 1 is reserved for NI
                    out_file = f'{imec_path[0:-4]}_spiketimes_synced.txt' # haven't verified this is what i want
                    addtl_probe_streams += f'-fromstream={stream_index},{imec_path}'
                    addtl_probe_events += f'-events={stream_index},{imec_spiketimes},{out_file}'
                except:
                    print(f'No spike times found for probe {sync_imec.index(imec_path)}')
                
        command = f'TPrime -syncperiod=1.0 -tostream={sync_imec[0]} {addtl_probe_streams} -fromstream=1,{sync_ni} {addtl_probe_events} {ni_events}'
        print(command)

    return command

def run_tprime(run_list,tools_path,catgt_output_path):
    """runs catgt and tprime on each file in th run list to generate the synced timestamp text files for each stream.
    :param run_list: list of file names to preprocess
    """
    for run_name in run_list:
        print(f'Running TPrime for {run_name}...')
        print(os.system(f"cd {os.path.join(tools_path, 'TPrime-win')} & {gen_tprime(run_name,catgt_output_path,sorter='kilosort2_5_output')}"))
        print(f'{run_name} done')


if __name__=='__main__':
    tools_path = os.path.join('C:\\','SpikeGLX','Tools')
    output_path = os.path.join('N:\\','CGT_OUT')
    runs = ['catgt_20230731_CWF3_00_g0']
    run_tprime(runs,tools_path,output_path)
