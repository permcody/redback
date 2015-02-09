''' Script to create postprocess pictures from csv file generated by Redback '''

import os, sys, csv
import pylab as P
import matplotlib.pyplot as pp
from twisted.trial._synctest import Todo

def readDigitisedCsv(input_dir, normalisation_stress=1.0):
    ''' Read all digitised data from Oka's experiments and return dictionary of data as strings '''
    data = {} # dict of data, key=experiment_index, value=dict{strain:stress}
    for experiment_index in range(1,7):
        csv_infilename = os.path.join(input_dir, 'fig2_cd{0}.csv'.format(experiment_index))
        if not os.path.isfile(csv_infilename):
            error_msg = 'Could not find digitised data (csv) of stress/strain '\
            'curve for experiment CD{}'.format(experiment_index)
            raise Exception, error_msg
        data[experiment_index] = {}
        with open(csv_infilename, 'rb') as csvfile:
            csvreader = csv.reader(csvfile)
            line_i = 0 # line index
            for row in csvreader:
                if line_i < 6:
                    # Skip metadata lines
                    line_i += 1
                    continue
                # Data line
                data[experiment_index][float(row[0])] = float(row[1])/normalisation_stress
                line_i += 1
                continue # go to next data line
        print 'Finished parsing digitised csv file {0}'.format(csv_infilename)
    return data

def parseCsvFile(filename, column_keys=None):
    ''' Read info from csv file '''
    print 'Parsing "{}"...'.format(filename)
    column_index = {} # mapping, key=column_key, value=corresponding column index
    data = {} # dict of data, key=column_key, value=data list (floats)
    with open(filename, 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        line_i = 0 # line index
        for row in csvreader:
            if line_i == 0:
                # Headers. Find interesting columns
                headers = row
                # prepare structure for all columns we want
                if column_keys is None:
                    # grab all data in file
                    column_keys_we_want = [elt.lower() for elt in headers]
                else:
                    # grab only requested data from file
                    assert type(column_keys)==type([])
                    column_keys_we_want = column_keys
                for column_key in column_keys_we_want:
                    data[column_key] = []
                for column_i, elt in enumerate(headers):
                    elt_lower = elt.lower()
                    if elt_lower in column_keys_we_want:
                        column_index[elt_lower] = column_i
                column_indices = column_index.values()
                line_i += 1
                print 'Found columns {0}'.format(column_index)
                continue
            # Data line
            if len(row) < len(headers):
                break # finished reading all data
            for column_key in column_keys_we_want:
                data[column_key].append(float(row[column_index[column_key]]))
            line_i += 1
            continue # go to next data line
    print 'Finished parsing csv file'
    return data

def createPicturesForData\
    (data, # dict of data
    key1, key2, output_dir, name_root='pic', 
    index_first=0, index_last=999999,
    title='graph title', label1='x_label', label2='y_label',
    plot_ellipse=False, # flag to plot P-Q space with ellipse or just time evolution
    velocity=1e-3, # coefficient alpha where BC function is alpha*t
    time_step=1.e-4, # redback simulation time step
    export_freq=1, # frequency of redback exports
    block_height=4, # height of block (in Y direction)
    yield_stress = 3., # RedbackMechMaterial yield_stress value (>0)
    slope_yield = -0.8, # RedbackMechMaterial slope_yield_surface value (<0)
    digitised_data = {}, # dict of digitised data as returned by readDigitisedData
    do_show=False): # show picture (pausing the script!) or not
    ''' Create pictures for plot of key1(x) vs key2(y) '''
    print 'Creating picture for {0}/{1}'.format(key1, key2)
    for key in [key1, key2]:
        if key1 not in data:
            error_msg = 'Key "{0}" not in data column_keys {1}'\
                .format(key1, data.keys())
            raise Exception, error_msg
    # Ensure output_dir exists
    if not os.path.isdir(output_dir):
        print 'Creating the output directory "{0}"'.format(output_dir)
        os.makedirs(output_dir)
    # get min and max values
    x_min = min(data[key1])
    x_max = max(data[key1])
    y_min = min(data[key2])
    y_max = max(data[key2])
    if key1== 'time':
        # change time to strain
        x_min = 100*velocity*x_min/block_height # x_min/(10.*time_step*block_height)
        x_max = 100*velocity*x_max/block_height # x_max/(10.*time_step*block_height)
    # get number of points
    nb_pts = len(data[key1])
    assert nb_pts == len(data[key2])
    # plot with matplotlib
    fig = P.figure(figsize=(7, 3))
    ax = fig.add_subplot(111)
    pp.subplots_adjust(left=0.15, bottom=0.2, right=0.95, top=0.8,
                wspace=None, hspace=None)
    nb_pts_plotted = min(index_last, nb_pts)
    #for i in range(max(0, index_first), nb_pts_plotted):
    for i in range(nb_pts_plotted-1, nb_pts_plotted): # TODO: hacked to produce only last picture
        P.grid(True)
        data_x = P.array(data[key1][0:i+1])
        data_y = P.array(data[key2][0:i+1])
        if key1== 'time':
            # change time to strain (%)
            data_x = 100*velocity*data_x/block_height # data_x/(10.*time_step*block_height)
        print 'Doing frame {0}{1}/{2}'.format(name_root, i, nb_pts_plotted-1)
        
        # Plot simulation data
        P.plot(data_x[1:], data_y[1:], 'bo-', label='simulation')
        
        # Plot digitised data
        styles = ['r-', 'b-', 'g-', 'c-', 'm-', 'y-']
        for experiment_index in sorted(digitised_data.keys()):
            dig_data_x = sorted(digitised_data[experiment_index].keys())
            dig_data_y = [digitised_data[experiment_index][key] for key in dig_data_x]
            P.plot(dig_data_x[1:], dig_data_y[1:], styles[experiment_index%len(styles)], label='CD{0}'.format(experiment_index+1))

        P.hold(False)
        P.grid(True)
        # labels
        P.xlabel(label1)
        #r"$Time \hspace{1}(\times10^3 years)$")
        #r"$\dot{\epsilon}_M  \hspace{0.5} (s^{-1})$"
        P.ylabel(label2)
        #r"$Nusselt\hspace{1}number$")
        if title:
            P.title(title)
        #msg = r"$Time \hspace{0.5}=\hspace{0.5}%4.2f\times10^3 years$"%(time)
        msg = r"$Strain \hspace{0.5}=\hspace{0.5}%.3f$"%(i*time_step*export_freq/block_height)
        msg = r"Strain = {:>8.3%}".format(i*time_step*export_freq/block_height/1000)
        
        # see https://docs.python.org/3.3/library/string.html#formatspec
        #P.figtext(0.5, 0.82, msg, horizontalalignment='center', color='black', fontsize=20)
        
        legend = P.legend(bbox_to_anchor=(0,1.02,1.,0.102), loc=3, ncol=7, mode='expand', borderaxespad=0., fontsize='small')
        margin = 5*float(y_max-y_min)/100.
        P.axis([x_min, x_max, y_min-margin, y_max+margin])
        P.savefig(os.path.join(output_dir,'{0}{1:05d}.png'.format(name_root, i)),
                  format='png')
        if do_show:
            P.show()
        P.clf()

def createPicturesForBatchData\
    (data, # list of dicts of data
    key1, key2, output_dir, name_root='pic', 
    title='graph title', label1='x_label', label2='y_label',
    velocity=1e-3, # coefficient alpha where BC function is alpha*t
    block_height=4, # height of block (in Y direction)
    digitised_data = {}, # dict of digitised data as returned by readDigitisedData
    do_show=False): # show picture (pausing the script!) or not
    ''' Create pictures for plot of key1(x) vs key2(y) for batch result '''
    print 'Mode batch, creating picture for {0}/{1}'.format(key1, key2)
    # Ensure output_dir exists
    if not os.path.isdir(output_dir):
        print 'Creating the output directory "{0}"'.format(output_dir)
        os.makedirs(output_dir)
    
    # create figure
    fig = P.figure(figsize=(7, 3))
    ax = fig.add_subplot(111)
    pp.subplots_adjust(left=0.15, bottom=0.2, right=0.95, top=0.8,
                wspace=None, hspace=None)
    P.grid(True)
    P.hold(True)

    styles =     ['r-',  'b-',  'g-',  'c-',  'm-',  'y-']
    styles_sim = ['ro-', 'bo-', 'go-', 'co-', 'mo-', 'yo-']
    
    data_to_plot = []
    global_x_min = 1e99
    global_x_max = -1e99
    global_y_min = 1e99
    global_y_max = -1e99
    for i in range(6): # For each simulation
        sim_index = i+1
        if i >= len(data):
            # Not all simulations were run. TODO
            raise Exception, 'Not all simulations were run. TODO'
            continue
        # Check keys
        for key in [key1, key2]:
            if key1 not in data[i]:
                error_msg = 'Key "{0}" not in data column_keys {1} for CD{2}'\
                    .format(key1, data[i].keys(), sim_index)
                raise Exception, error_msg
        # get min and max values
        x_min = min(data[i][key1])
        x_max = max(data[i][key1])
        y_min = min(data[i][key2])
        y_max = max(data[i][key2])
        if key1== 'time':
            # change time to strain
            x_min = 100*velocity*x_min/block_height
            x_max = 100*velocity*x_max/block_height
        global_x_min = min(global_x_min, x_min)
        global_x_max = max(global_x_max, x_max)
        global_y_min = min(global_y_min, y_min)
        global_y_max = max(global_y_max, y_max)
        # get number of points
        assert len(data[i][key1]) == len(data[i][key2])
    
        data_x = P.array(data[i][key1][:])
        data_y = P.array(data[i][key2][:])
        if key1== 'time':
            # change time to strain (%)
            data_x = 100*velocity*data_x/block_height
        
        # Plot simulation data
        P.plot(data_x[1:], data_y[1:], styles_sim[sim_index%len(styles_sim)], label='simulation {0}'.format(sim_index))

    # Plot digitised data
    for experiment_index in sorted(digitised_data.keys()):
        dig_data_x = sorted(digitised_data[experiment_index].keys())
        dig_data_y = [digitised_data[experiment_index][key] for key in dig_data_x]
        P.plot(dig_data_x[1:], dig_data_y[1:], styles[experiment_index%len(styles)], label='CD{0}'.format(experiment_index))
        global_x_min = min(global_x_min, min(dig_data_x[1:]))
        global_x_max = max(global_x_max, max(dig_data_x[1:]))
        global_y_min = min(global_y_min, min(dig_data_y[1:]))
        global_y_max = max(global_y_max, max(dig_data_y[1:]))

    P.hold(False)
    P.grid(True)
    # labels
    P.xlabel(label1)
    #r"$Time \hspace{1}(\times10^3 years)$")
    #r"$\dot{\epsilon}_M  \hspace{0.5} (s^{-1})$"
    P.ylabel(label2)
    #r"$Nusselt\hspace{1}number$")
    if title:
        P.title(title)
    #msg = r"Strain = {:>8.3%}".format(i*time_step*export_freq/block_height/1000)
    
    # see https://docs.python.org/3.3/library/string.html#formatspec
    #P.figtext(0.5, 0.82, msg, horizontalalignment='center', color='black', fontsize=20)
    
    legend = P.legend(bbox_to_anchor=(0,1.02,1.,0.102), loc=3, ncol=6, mode='expand', borderaxespad=0., fontsize='small')
    
    margin = 5*float(y_max-y_min)/100.
    P.axis([global_x_min, global_x_max, global_y_min-margin, global_y_max+margin])
    P.savefig(os.path.join(output_dir,'{0}{1:05d}.png'.format(name_root, i)),
              format='png')
    if do_show:
        P.show()
    P.clf()

def computeDifferentialStress(data, confining_pressure):
    ''' Compute differential stress from average top stress and confining pressure.
       Since we don't have the equilibration step yet, shift the curve to start at 0.
    '''
    #data['avg_top(sig1) - sig3'] = data['mises_stress']
    #return data
    
    diff_stress = [-confining_pressure - elt for elt in data['top_avg_stress_yy']]
    data['avg_top(sig1) - sig3'] = diff_stress
    # Potentially remove data points to make differential stress start at 0
    index = 0
    while index < len(diff_stress):
        if diff_stress[index] >= 0:
            break
        index += 1
    assert index < len(diff_stress)
    if index == 0:
        if diff_stress[index] > 0:
            raise Exception, 'Case diff_stress[0]>0 not handled...'
        elif diff_stress[index] == 0:
            # nothing to do
            return data
    # We're now in the case where diff_stress starts negative
    t_0 = data['time'][index-1] - diff_stress[index-1]*(data['time'][index] - data['time'][index-1])/(diff_stress[index] - diff_stress[index-1])
    new_time = [0]
    new_diff_stress = [0]
    for i in range(index, len(diff_stress)):
        new_time.append(data['time'][i] - t_0)
        new_diff_stress.append(diff_stress[i])
    data['time'] = new_time
    data['avg_top(sig1) - sig3'] = new_diff_stress
    return data

if __name__ == '__main__':
    velocity = (2e-3)/3. # boundary condition on top surface (coeff x t)
    oka_digitised_dir = os.path.join('fig2')
    output_dir = os.path.join('.', 'pics_postprocess') # where pics will be created
     
    # Read digitised version of Oka's results
    oka_data = readDigitisedCsv(oka_digitised_dir, normalisation_stress=2.26)
    
    # create output dir if it doesn't exist yet
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    if 0:
        # Show curve for current simulation
        csv_filename = os.path.join('Oka.csv')
        confining_pressure = 0.8
    
        # parse CSV file
        data = parseCsvFile(csv_filename)
        # compute differential stress
        data = computeDifferentialStress(data, confining_pressure)
    
        # Plot stress vs strain curve
        createPicturesForData(data=data,
            key1='time', key2='avg_top(sig1) - sig3', 
            output_dir=os.path.join(output_dir, 'StressStrainCurves'), name_root='{0}_'.format('StressStrain'), 
            index_first=0, index_last=999999, title=None, label1='Strain (%)', label2='Deviatoric stress', 
            velocity=velocity, block_height=4, digitised_data=oka_data, do_show=True)
    
    if 1:
        # Show curves for batch of simulations
        batch_directory = os.path.join('results', 'batch1')
        data = [] # list of 6 dictionaries for each simulation data
        normalising_stress = 2.26e6 # Pa
        confining_pressures = {
            1:0.25e6/normalising_stress,
            2:0.5e6/normalising_stress,
            3:0.75e6/normalising_stress,
            4:1.0e6/normalising_stress,
            5:1.5e6/normalising_stress,
            6:2.0e6/normalising_stress,
        }
        for i in range(6):
            csv_filename = os.path.join(batch_directory, 'oka_CD{0}.csv'.format(i+1))
            data.append(parseCsvFile(csv_filename))
            data[i] = computeDifferentialStress(data[i], confining_pressures[i+1])
        # Plot stress vs strain curves
        createPicturesForBatchData(data=data,
            key1='time', key2='avg_top(sig1) - sig3', 
            output_dir=os.path.join(output_dir, 'StressStrainCurves'), name_root='{0}_'.format('StressStrain'), 
            title=None, label1='Strain (%)', label2='Deviatoric stress', 
            velocity=velocity, block_height=4, digitised_data=oka_data, do_show=True)
    print 'Finished'
    
