import sys

sys.path.insert(0, './transmitter')     # Relative path
sys.path.insert(0, './receiver')

from USRP_Transmitter import USRPTransmitter
from USRP_Receiver import USRPReceiver

import argparse
import numpy as np
import time


"""Create and configure argument parser"""
parser = argparse.ArgumentParser(
    description='USRP Transmitter/Receiver System',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

# ===== REQUIRED ARGUMENTS =====
parser.add_argument('-role',
                    type=str,
                    default='src1',
                    choices=['src1', 'dst1', 'rly1'],  # Name should be changed
                    help='Operation mode')

# Initialization
options = parser.parse_args()
role = options.role
message_type = "bits"

serial_usrp_src1 = '30CD424'
serial_usrp_rly1 = '30CD3F7'
serial_usrp_dst1 = '3169C62'

transmitter = USRPTransmitter(
                            # USRP settings (matching your C++ defaults)
                            tx_freq=920e6,  # 2.412 GHz
                            tx_rate=1e6,  # 1 MSPS
                            tx_gain=30.0,  # 20 dB
                            tx_bw=500e3,  # 500 kHz
                            tx_args="serial=30CD3F7",  # Auto-detect
                            tx_antenna="TX/RX",
                            tx_subdev="A:B",
                            ref="internal",

                            # Message settings
                            num_bits=1200,
                            interval=1000,  # 1 second between packets
                            continuous=False,  # Not continuous
                            repeat_times=5,

                            # Modulation settings
                            scheme="DBPSK",
                            add_preamble=True,
                            preamble_length=5,  # m=5 for m-sequence
                            preamble_type="m-sequence",

                            # Filter settings
                            filter_type="rrc",
                            symbol_rate=0.8e6,
                            num_taps=151,
                            U=5,
                            D=4,
                            roll_off=0.25,
                            num_threads=1)

receiver = USRPReceiver(
                        rx_channel=0,
                        samps_per_buff=10000,
                        num_recv_request=0,
                        rx_freq=2.4e9,
                        rx_rate=1e6,
                        rx_gain=60.0,
                        rx_bw=500e3,
                        settling_time=0.2,
                        uhd_timeout=1000.0,
                        rx_args="serial=30CD3F7",
                        rx_ant="RX2",
                        rx_subdev="A:B",
                        ref="internal",
                        otw="sc16",
                        data_type="float",

                        # Energy Detection and AGC parameters
                        energy_packet_size=1600,
                        IIR_window_size=1,
                        alpha=0.96,
                        energy_threshold=8.0e-6,  # Fixed threshold
                        IIR_threshold_multiplier=8.0,
                        IIR_threshold_adaptive=False,  # Disable adaptive
                        AGC_type="Feed",

                        # Filter Parameters
                        num_taps=151,
                        U=4,
                        D=1,
                        num_threads=1,
                        symbol_rate=0.8e6,
                        roll_off=0.26,
                        filter_type="rrc",

                        # Synchronization Parameters
                        recv_msg_len=1201,
                        sps_sync=5,
                        sync_threshold=15.0,

                        # Demodulation Parameters
                        preamble_length=5,
                        add_preamble=True,
                        preamble_type="m-sequence",
                        demod_scheme="DBPSK")

success = receiver.start()
if not success:
    print("Failed to start receiver!")
    sys.exit(1)

success_transmit = transmitter.start(message_type)
if not success_transmit:
    print("Failed to start Transmitter!")
    sys.exit(1)

print("[PYTHON] Receiver started - listening for packets...")
print("[PYTHON] Press Ctrl+C to stop")

packet_count = 0
running = True
try:
    while running:
        msg = receiver.receive_bits()
        if msg is not None:
            packet_count += 1
            msg = bytes(msg)
            source_serial = msg[0:13].rstrip(b'\x00').decode('utf-8')
            dest_serial = msg[13:26].rstrip(b'\x00').decode('utf-8')
            payload = msg[26:len(msg)-1].decode('utf-8')
            print("[RELAY PRINTING] The payload is: ", payload, '\n')

            if dest_serial == serial_usrp_rly1:
                print("[RELAY DEST] I am the real destination")
            else:
                print("[RELAY TRANSFER] Pushing the packets to real destination \n")
                byte_array = np.frombuffer(msg, dtype=np.uint8)
                bits = np.unpackbits(byte_array)  # numpy array of bits
                # transmitter.send_bits(bits)
        else:
            # No message available, sleep briefly to avoid busy-waiting
            time.sleep(0.01)

except KeyboardInterrupt:
    print("\n[PYTHON] KeyboardInterrupt caught")

finally:
    print(f"\n[PYTHON] Stopping receiver... (received {packet_count} packets)")
    receiver.stop()
    print("[PYTHON] Receiver stopped")
