# This program is used to simpflify experiment management
# Start a session by starting the nodes one by one with each node using a separate terminal window
import os
import time
import netcfg

# print 'Starting flow 1...'
print('Starting flow 1...')

os.system("gnome-terminal -e 'bash -c \"python mynd.py -i dst1; exec bash\"'")
time.sleep(3)
# os.system("gnome-terminal -e 'bash -c \"python mynd.py -i rly12; exec bash\"'")
# time.sleep(1)
# os.system("gnome-terminal -e 'bash -c \"python mynd.py -i rly11; exec bash\"'")
# time.sleep(1)
os.system("gnome-terminal -e 'bash -c \"python mynd.py -i src1; exec bash\"'")
