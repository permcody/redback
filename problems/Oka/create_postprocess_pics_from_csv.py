''' Script to create postprocess pictures from csv file generated by Redback '''

import os, sys, csv
import pylab as P
import matplotlib.pyplot as pp

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
    (data, key1, key2, output_dir, name_root='pic', 
    index_first=0, index_last=999999,
    title='graph title', label1='x_label', label2='y_label',
    plot_ellipse=False, # flag to plot P-Q space with ellipse or just time evolution
    time_step=1.e-4, # redback simulation time step
    export_freq=1, # frequency of redback exports
    block_height=4, # height of block (in Y direction)
    yield_stress = 3., # RedbackMechMaterial yield_stress value (>0)
    slope_yield = -0.8 # RedbackMechMaterial slope_yield_surface value (<0)
    ):
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
        x_min = x_min*100/block_height
        x_max = x_max*100/block_height
    if plot_ellipse:
        x_min = min(-P.fabs(yield_stress), x_min)
        x_max = max(0, x_max)
        y_min = min(0, y_min) # only show top half of ellipse
        y_max = max(P.fabs(slope_yield)*P.fabs(yield_stress)/2., y_max)
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
            data_x = data_x*100./block_height
        print 'Doing frame {0}{1}/{2}'.format(name_root, i, nb_pts_plotted-1)
        P.plot(data_x[1:], data_y[1:], 'bo-')
        # Plot modified Cam-Clay ellipse if required
        if plot_ellipse:
            P.hold(True)
            if 0:
                # plot ellipse with regularly spaced points in x
                step = float(P.fabs(yield_stress))/100.
                data_p = P.arange(0, -P.fabs(yield_stress)-step, -step)
                data_q = P.fabs(slope_yield)*P.sqrt(data_p*(-data_p-P.fabs(yield_stress)))
                P.plot(data_p, data_q, 'r-')
                P.plot(data_p, -data_q, 'r-')
            else:
                # plot ellipse parametrically
                angle_step = P.pi/100.
                angles = P.arange(0, 2*P.pi+angle_step, angle_step)
                data_p = -P.fabs(yield_stress)/2 + P.fabs(yield_stress)/2.*P.cos(angles)
                data_q = P.fabs(slope_yield)*P.fabs(yield_stress)/2.*P.sin(angles)
                P.plot(data_p, data_q, 'r-')
                P.plot(data_p, -data_q, 'r-')
        else:
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
        msg = r"Strain = {:>8.3%}".format(i*time_step*export_freq/block_height)
        # see https://docs.python.org/3.3/library/string.html#formatspec
        P.figtext(0.5, 0.82, msg, horizontalalignment='center', color='black', 
                  fontsize=20)
        margin = 5*float(y_max-y_min)/100.
        P.axis([x_min, x_max, y_min-margin, y_max+margin])
        P.savefig(os.path.join(output_dir,'{0}{1:05d}.png'.format(name_root, i)),
                  format='png')
        P.clf()

if __name__ == '__main__':
    csv_filename = os.path.join('Oka.csv')
    output_dir = os.path.join('.', 'pics_postprocess') # where pics will be created
    column_keys = ['time', 'mises_stress_top', 'mean_stress_top',
                   'temp_middle'] # CSV columns we're interested in
    
    # parse CSV file
    data = parseCsvFile(csv_filename) #, column_keys)
    # create output dir if it doesn't exist yet
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    # Plot stress vs strain curve
    if 1:
        createPicturesForData(data,
            key1='mean_stress_top', key2='mises_stress_top', 
            output_dir=os.path.join(output_dir, 'P-Q'), name_root='P-Q_', 
            index_first=0, index_last=999999, title=None, label1='Mean Stress', label2='Deviatoric Stress',
            plot_ellipse=True, time_step=1.e-4, export_freq=10, block_height=4,
            yield_stress = 1., # RedbackMechMaterial yield_stress value (>0)
            slope_yield = 1.44 # RedbackMechMaterial slope_yield_surface value (<0)
            )
    # Plot mean stress vs volumetric strain (for geotechnics people)
    if 0:
        createPicturesForData(data,
            key1='mean_stress', key2='volumetric_strain', 
            output_dir=os.path.join(output_dir, 'mean_stress_vol_strain'), name_root='mean_stress_vol_strain_', 
            index_first=0, index_last=999999, title=None, label1='Mean Stress', label2='Volumetric Strain',
            time_step=1.e-4, export_freq=10, block_height=4)
    # Plot time evolutions
    if 0:
        maps = {'mises_stress':     {'key':'mises_stress',      'label':'Mises Stress'},
                'mises_strain_rate':{'key':'mises_strain_rate', 'label':'Mises Strain Rate'},
                'volumetric_strain':{'key':'volumetric_strain', 'label':'Volumetric Strain'},
                'volumetric_strain_rate':{'key':'volumetric_strain_rate', 'label':'Volumetric Strain Rate'},
                'porosity':         {'key':'porosity_middle',   'label':'Porosity'},
                'solid_ratio':      {'key':'solid_ratio_middle','label':'Solid Ratio'},
                'mean_stress':      {'key':'mean_stress',       'label':'Mean Stress'},
                'temp':             {'key':'temp_middle',       'label':'Normalised Temperature'}}
        for name in maps.keys():
            createPicturesForData(data,
                key1='time', key2=maps[name]['key'], 
                output_dir=os.path.join(output_dir, name), name_root='{0}_'.format(name), 
                index_first=0, index_last=999999, title=None, label1='Strain (%)', label2=maps[name]['label'], 
                time_step=1.e-4, export_freq=10, block_height=4)
    print 'Finished'
    