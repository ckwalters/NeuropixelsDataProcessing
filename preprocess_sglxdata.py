import os

def run_catgt(run_list,tools_path,input_path,output_path,probes,event_bits,nidq=True,car=None,filter=None,inverted=False):
    """Run CatGT v3.4
    run_list is a list of run names, including g0
    input_path is the main SGLX data folder
    output_path is e.g. CGT_Out
    probes is 0 or 0:1 etc
    event_bits is a list of digital bits you want to extract from NIDAQ
    """
    probes = str(probes)

    if nidq:
        event_extractors = ''
        for bit in event_bits:
            event_extractors += f'-xd=0,0,-1,{bit},0 ' # extractors: stream type,stream index,word,bit,millisec
        if inverted:
            for bit in event_bits:
                event_extractors += f'-ixd=0,0,-1,{bit},0 ' # find the falling edges
        nidq_command = f'-ni {event_extractors}'
    else:
        nidq_command = ''

    # Signal digital referencing
    if car=='global':
        car_command = '-gblcar'
    elif car=='local':
        car_command = '-loccar=4,32'
    elif car==None:
        car_command = ''
    else:
        raise(Exception) # invalid CAR input
    
    # Signal filtering
    if filter=='butter':
        filter_command = '-apfilter=butter,12,300,6000'
    elif filter==None:
        filter_command = ''
    else:
        raise(Exception) # invalid filter input

    for run_name in run_list:
        command = f'CatGT -dir={input_path} -run={run_name[0:-3]} -prb_fld -g={run_name[-1]},{run_name[-1]} -t=0,0 -ap -prb={probes} {car_command} {filter_command} {nidq_command} -dest={output_path} -out_prb_fld -pass1_force_ni_ob_bin'
        print(f'Running CatGT for {run_name}...')
        print(command)
        print(os.system(f"cd {os.path.join(tools_path, 'CatGT-win')} & {command}"))
        print(f'{run_name} done')


def preprocess_sglxdata(sessions,car=None,highpass_filter=None,process_nidq=True):
    """In my terminology, a session is a group of runs that you want to
    concatenate and sort together. A run is any time SGLX starts/stops
    recording, and consists of n number of (imec) recordings, where n is the
    number of probes.
    """
    # Set these up for your computer & rig
    tools_path = os.path.join('C:\\','SpikeGLX','Tools')
    input_path = os.path.join('D:\\','SGLX_Data')
    output_path = os.path.join('D:\\','CGT_OUT')
    probes = '0:1' # probes is 0 or 0:1 etc.
    event_bits = [1,2] # Your behavior event bits on your NIDAQ stream 

    if type(sessions) != list:
        sessions = [sessions] # list of strings identifying a particular session
    run_dirs = next(os.walk(input_path))[1] # list all the directories in the SGLX data folder

    for session in sessions:
        # Find the runs that compose the session
        runs = []
        for dir in run_dirs:
            if str(session) in dir:
                runs.append(dir) # run folder name including g0 but not imec0 etc
        if len(runs)>0:
            print(f'Runs found: {runs}')
        else:
            print('NO RUNS FOUND')

        # Run CatGT
        run_catgt(runs,tools_path,input_path,output_path,probes,event_bits,car=car,filter=highpass_filter,inverted=False,nidq=process_nidq)
            # you have to adjust filter settings in the function 

        session_catgt_dir = os.path.join(output_path,f'catgt_{runs[0]}')

        # Find each recording (one for each probe) that makes up the session
        recording_paths = []
        probedirs = next(os.walk(session_catgt_dir))[1] # lists all folders within the session folder, should be one for each probe
        probedirs = [probedirs[1]] # for just one probe
        for probedir in probedirs:
            recording_paths.append(os.path.join(session_catgt_dir,probedir))
        
        print(recording_paths)


if __name__=='__main__':
    preprocess_sglxdata(['20240206'],process_nidq=True)