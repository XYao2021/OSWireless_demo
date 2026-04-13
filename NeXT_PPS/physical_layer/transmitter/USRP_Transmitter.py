import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
import transmitter
import time
from typing import Optional, List
import sys

class USRPTransmitter:
    
    def __init__(self,
                # USRP Parameters
                tx_freq: float = 2.412e9,
                tx_rate: float = 1e6,
                tx_gain: float = 20.0,
                tx_bw: float = 500e3,
                tx_args: str = "",
                tx_antenna: str = "TX/RX",
                tx_subdev: str = "A:0",
                ref: str = "internal",
                 
                # Message Parameters
                num_bits: int = 1000,
                interval: int = 1000,
                continuous: bool = False,
                repeat_times: int = 3,
                 
                # Modulation Parameters
                scheme: str = "DBPSK",
                add_preamble: bool = True,
                preamble_length: int = 5,
                preamble_type: str = "m-sequence",
                 
                # Filter Parameters
                filter_type: str = "rrc",
                symbol_rate: float = 0.8e6,
                num_taps: int = 151,
                U: int = 5,
                D: int = 4,
                roll_off: float = 0.25,
                num_threads: int = 1):
        """
        Initialize transmitter with all parameters.
        
        USRP Parameters:
            tx_freq: Center frequency in Hz (default: 2.412 GHz)
            tx_rate: Sample rate in Hz (default: 1 MSPS)
            tx_gain: Transmit gain in dB (default: 20 dB)
            tx_bw: Transmit bandwidth in Hz (default: 500 kHz)
            tx_args: USRP device arguments (default: auto-detect)
            tx_antenna: Antenna port (default: "TX/RX")
            tx_subdev: Subdevice specification (default: "A:0")
            ref: Clock reference (default: "internal")
        
        Message Parameters:
            num_bits: Number of bits per message block (default: 1000)
            interval: Time between packets in ms (default: 1000)
            continuous: Continuous transmission mode (default: False)
        
        Modulation Parameters:
            scheme: Modulation scheme (default: "DBPSK")
            add_preamble: Add preamble to messages (default: True)
            preamble_length: Preamble length for m-sequence (default: 5)
            preamble_type: Preamble type (default: "m-sequence")
        
        Filter Parameters:
            filter_type: Filter type - "rrc", "rc", or "lowpass" (default: "rrc")
            symbol_rate: Symbol rate in Hz (default: 0.8 MHz)
            num_taps: Number of filter taps (default: 151)
            U: Upsampling factor (default: 5)
            D: Downsampling factor (default: 4)
            roll_off: Roll-off factor for RRC/RC (default: 0.25)
            num_threads: Number of FFT threads (default: 1)
        """
        print("[Python API] Initializing transmitter...")
        
        # Create C++ transmitter object
        self._tx = transmitter.Transmitter()
        
        # Configure USRP
        self._tx.set_tx_freq(tx_freq)
        self._tx.set_tx_rate(tx_rate)
        self._tx.set_tx_gain(tx_gain)
        self._tx.set_tx_bw(tx_bw)
        if tx_args:
            self._tx.set_tx_args(tx_args)
        self._tx.set_tx_antenna(tx_antenna)
        self._tx.set_tx_subdev(tx_subdev)
        self._tx.set_ref(ref)
        
        # Configure Message
        self._tx.set_num_bits(num_bits)
        self._tx.set_interval(interval)
        self._tx.set_continuous(continuous)
        
        # Configure Modulation
        self._tx.set_mod_scheme(scheme)
        self._tx.set_preamble(add_preamble, preamble_length, preamble_type)
        
        # Configure Filter
        self._tx.set_filter(filter_type, symbol_rate, num_taps, U, D, roll_off, num_threads)

        self._tx.set_repeat_times(repeat_times)
        
        self._is_running = False
        self._num_bits = num_bits
        
        # Print configuration summary
        print(f"\n[Python API] Configuration Summary:")
        print(f"  USRP:")
        print(f"    Frequency: {tx_freq/1e6:.3f} MHz")
        print(f"    Sample Rate: {tx_rate/1e6:.3f} MSPS")
        print(f"    Gain: {tx_gain} dB")
        print(f"    Bandwidth: {tx_bw/1e6:.3f} MHz")
        print(f"  Message:")
        print(f"    Bits per block: {num_bits}")
        print(f"    Interval: {interval} ms")
        print(f"    Continuous: {continuous}")
        print(f"  Modulation:")
        print(f"    Scheme: {scheme}")
        print(f"    Preamble: {add_preamble} (length={preamble_length})")
        print(f"  Filter:")
        print(f"    Type: {filter_type}")
        print(f"    Symbol Rate: {symbol_rate/1e6:.3f} MHz")
        print(f"    U/D: {U}/{D}")
        print()
    
    def start(self, message_type: str):
        if self._is_running == True:
            print("[Python API] Already running")
            return False
        
        success = self._tx.start(message_type)
        
        if success:
            self._is_running = True
            time.sleep(0.5)  # Give threads time to initialize
            print("[Python API] Transmitter started ✓")
        else:
            print("[Python API] Failed to start transmitter ✗")
        
        return success  # return true if success
    
    def stop(self):
        """Stop the transmitter pipeline."""
        if not self._is_running:
            return
        
        print("[Python API] Stopping transmitter...")
        self._tx.stop()
        self._is_running = False
        print("[Python API] Transmitter stopped ✓")
    
    def send_string(self, message: str):
        """
        Send a text message.
        
        Args:
            message: String message to transmit
        """
        if not self._is_running:
            raise RuntimeError("Transmitter not running. Call start() first.")
        
        # Send to C++ transmitter
        self._tx.send_message(message)
        print(f"[Python API] Sent message: {message}")
    
    def send_bits(self, message: bytes):
        """
        Send a text message.
        
        Args:
            message: String message to transmit
        """
        if not self._is_running:
            raise RuntimeError("Transmitter not running. Call start() first.")
        
        # Send to C++ transmitter
        self._tx.send_bits(message)
        print(f"[Python API] Sent message bytes -> bits: {len(message)}")
    
    def get_status(self) -> dict:
        """
        Get transmitter status including queue sizes.
        
        Returns:
            Dictionary with status information
        """
        return self._tx.get_status()
    
    def get_config(self) -> dict:
        """
        Get current configuration.
        
        Returns:
            Dictionary with all configuration parameters
        """
        return self._tx.get_config()
    
    def clear_queues(self):
        """Clear all pending messages in queues."""
        self._tx.clear_queues()
        print("[Python API] All queues cleared")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto cleanup."""
        self.stop()
        return False
