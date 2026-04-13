import USRP_Receiver
import signal
import sys
import time

message_type = "bits"
# message_type = "string"

serial_usrp_src1 = '30CD424'
serial_usrp_rly1 = '30CD3F7'
serial_usrp_dst1 = '3169C62'

rx = USRP_Receiver.USRPReceiver(
                                rx_channel=0,
                                samps_per_buff=10000,
                                num_recv_request=0,
                                rx_freq=920e6,
                                rx_rate=1e6,
                                rx_gain=30.0,
                                rx_bw=500e3,
                                settling_time=0.2,
                                uhd_timeout=1000.0,
                                rx_args="serial=3169C62",
                                rx_ant="RX2",
                                rx_subdev="A:0",
                                ref="internal",
                                otw="sc16",
                                data_type="float",

                                # Energy Detection and AGC parameters
                                energy_packet_size=1600,
                                IIR_window_size=1,
                                alpha=0.96,
                                energy_threshold=1.0e-5,  # Fixed threshold
                                IIR_threshold_multiplier=8.0,
                                IIR_threshold_adaptive=False,  # Disable adaptive
                                AGC_type="Feed",

                                # Filter Parameters
                                num_taps=151,
                                U=4,
                                D=1,
                                num_threads=1,
                                symbol_rate=0.8e6,
                                roll_off=0.25,
                                filter_type="rrc",

                                # Synchronization Parameters
                                recv_msg_len=1201,
                                sps_sync=5,
                                sync_threshold=15,

                                # Demodulation Parameters
                                preamble_length=5,
                                add_preamble=True,
                                preamble_type="m-sequence",
                                demod_scheme="DBPSK")

success = rx.start()
if not success:
    print("Failed to start receiver!")
    sys.exit(1)

print("[PYTHON] Receiver started - listening for packets...")
print("[PYTHON] Press Ctrl+C to stop")

packet_count = 0
running = True
try:
    while running:
        if message_type == "bits":
            msg = rx.receive_bits()
            if msg is not None:
                packet_count += 1
                msg = bytes(msg)
                source_serial = msg[0:13].rstrip(b'\x00').decode('utf-8')
                dest_serial = msg[13:26].rstrip(b'\x00').decode('utf-8')
                payload = msg[26:len(msg) - 1].decode('utf-8')
                print(source_serial)
                print(dest_serial)
                print(payload)
            else:
                # No message available, sleep briefly to avoid busy-waiting
                time.sleep(0.01)
        else:
            print("[RECEIVE WARNING] Unrecognize message type for C++ - Python API")

except KeyboardInterrupt:
    print("\n[PYTHON] KeyboardInterrupt caught")

finally:
    print(f"\n[PYTHON] Stopping receiver... (received {packet_count} packets)")
    rx.stop()
    print("[PYTHON] Receiver stopped")
