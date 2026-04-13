

import netcfg
import numpy as np


# Remove problematic import at top level
# import matplotlib.pyplot as plt  - THIS LINE IS REMOVED

def delay_cal_plot(file_name):
    try:
        # Only import matplotlib when needed
        import matplotlib
        matplotlib.use('Agg')  # Use non-GUI backend
        import matplotlib.pyplot as plt

        dict_tx = netcfg.tx_time_stamp_dict
        dict_rx = netcfg.ack_time_stamp_dict

        # For each element in the ack dict, get the delay by subtracting the time stamp of the ack and the time stamp of the txd packet

        delay_list = []
        for rxackid in dict_rx.keys():
            delay = dict_rx[rxackid] - dict_tx[rxackid]
            # Append the delay for each packet in the delay_list
            delay_list.append(delay)

        # Now, for each element of the delay_list, calculate the running average

        avg_del_list = []
        for dela in range(len(delay_list)):
            # Append the mean value to the avg_del_list. This will be used to plot the figure
            avg_del_list.append(np.mean(delay_list[0:dela + 1]))

        with open(file_name, 'wb') as f5:
            np.save(f5, delay_list)

        # Create and save the plot
        plt.figure(1)
        font = {'family': 'sans', 'size': 16}
        plt.rc('font', **font)

        plt.plot(range(len(avg_del_list)), avg_del_list, c='k', linestyle='-', marker='.', label='Running Average')

        plt.xlabel('Time (s)')
        plt.ylabel('Avg Delay (ms)')
        plt.xlim(0, len(avg_del_list) - 1)
        plt.grid(True)
        plt.legend()

        # Save the figure
        plot_filename = file_name.replace('.npy', '.png')
        plt.savefig(plot_filename)
        print(f"Plot saved as {plot_filename}")

    except ImportError as e:
        print(f"Warning: Could not import matplotlib to create plot: {e}")
        print("Still saving data to npy file...")

        # Save the data even if plotting fails
        delay_list = []
        dict_tx = netcfg.tx_time_stamp_dict
        dict_rx = netcfg.ack_time_stamp_dict

        for rxackid in dict_rx.keys():
            delay = dict_rx[rxackid] - dict_tx[rxackid]
            delay_list.append(delay)

        with open(file_name, 'wb') as f5:
            np.save(f5, delay_list)

        
        
    
