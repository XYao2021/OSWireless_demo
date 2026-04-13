# This program is used to simpflify experiment management
# Start a session by starting the nodes one by one with each node using a separate terminal window
import os
import time

# print 'Starting flow 2...'
print ('Starting flow 2...')

os.system("gnome-terminal -e 'bash -c \"python mynd.py -i dst2 ; exec bash\"'")
time.sleep(3)
# os.system("gnome-terminal -e 'bash -c \"python mynd.py -i rly22; exec bash\"'")
# time.sleep(1)
# os.system("gnome-terminal -e 'bash -c \"python mynd.py -i rly21; exec bash\"'")
# time.sleep(1)
os.system("gnome-terminal -e 'bash -c \"python mynd.py -i src2; exec bash\"'")