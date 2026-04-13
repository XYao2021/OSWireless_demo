from USRP_Transmitter import USRPTransmitter
import time
import numpy as np

def main():
    print("="*70)
    print("Signal Handling Example")
    print("="*70)
    print("\nThis example demonstrates Ctrl+C handling.")
    print("Press Ctrl+C at any time to stop gracefully.")
    print("="*70 + "\n")

    message_type = "bits"
    # message_type = "string"

    serial_usrp_src1 = '30CD424'
    serial_usrp_rly1 = '30CD3F7'
    serial_usrp_dst1 = '3169C62'
    
    # Create transmitter with same parameters as your C++ defaults
    tx = USRPTransmitter(
        # USRP settings (matching your C++ defaults)
        tx_freq=2.412e9,          # 2.412 GHz
        tx_rate=1e6,              # 1 MSPS
        tx_gain=60.0,             # 20 dB
        tx_bw=500e3,              # 500 kHz
        tx_args="serial=30CD424",               # Auto-detect
        tx_antenna="TX/RX",
        tx_subdev="A:B",
        ref="internal",
        
        # Message settings
        num_bits=1200,
        interval=1000,            # 1 second between packets
        continuous=False,         # Not continuous
        repeat_times=5,
        
        # Modulation settings
        scheme="DBPSK",
        add_preamble=True,
        preamble_length=5,        # m=5 for m-sequence
        preamble_type="m-sequence",
        
        # Filter settings
        filter_type="rrc",
        symbol_rate=0.8e6,
        num_taps=151,
        U=5,
        D=4,
        roll_off=0.25,
        num_threads=1
    )
    
    if not tx.start(message_type):
        return 1
    
    try:
        # Send message
        print("[MAIN] Sending messages...")
        source = serial_usrp_src1.encode().ljust(13, b'\x00')
        dest = serial_usrp_dst1.encode().ljust(13, b'\x00')
        payload = "This is the test message of Xin Yao from University of Florida, Electrical and Computer Engineering Department! [TESTING] !!"
        payload = payload.encode()
        message = source + dest + payload
        byte_array = np.frombuffer(message, dtype=np.uint8)
        bits = np.unpackbits(byte_array)  # numpy array of bits
        for i in range(30):
            tx.send_bits(bits)
            time.sleep(8.0)
        
        # Keep transmitter alive
        print("\n[MAIN] All messages sent.")
        print("[MAIN] Transmitter still running, waiting for Ctrl+C...")
        
        while True:
            time.sleep(1.0)
    
    except KeyboardInterrupt:
        print("\n[MAIN] Stopped by user")
    
    finally:
        tx.stop()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())