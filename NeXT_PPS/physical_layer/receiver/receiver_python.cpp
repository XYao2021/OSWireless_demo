# include <pybind11/pybind11.h>
# include <pybind11/stl.h>
#include <pybind11/numpy.h>

# include <uhd/utils/safe_main.hpp>
# include <uhd/utils/static.hpp>
# include <uhd/utils/thread.hpp>
# include <uhd/usrp/multi_usrp.hpp>
# include <uhd/exception.hpp>

// Boost library
# include <boost/program_options.hpp>  // for arguments input
# include <boost/format.hpp>

// Basic library
# include <iostream>
# include <csignal>  // deal with signal
# include <cmath>
# include <functional>  // funtion / bind / std::ref / std::greater/less
# include <thread>
# include <vector>
# include <mutex>  // for FIFO queue and multi-thread processing
# include <fftw3.h>
# include <map>

// Unused but useful library
// # include <fstream>  // File reading / writing

# include "filters.hpp"
# include "messages.hpp"
# include "FIFO.hpp"
// # include "taps.hpp"
# include "modulator.hpp"
# include "transceiver.hpp"
# include "synchronization.hpp"

namespace py = pybind11;

static std::atomic<bool> global_stop_signal(false);

class Receiver_API;
static Receiver_API* g_active_receiver = nullptr;
void sig_int_handler(int);

class Receiver_API{
private:

    // ========================================================================
    // USRP Configuration
    // ========================================================================
    
    int rx_channel_;
    size_t samps_per_buff_;
    int num_recv_request_;
    double rx_freq_;
    double rx_rate_;
    double rx_gain_;
    double rx_bw_;
    double settling_time_;
    double uhd_timeout_;
    std::string rx_args_;
    std::string rx_ant_;
    std::string rx_subdev_;
    std::string ref_;
    std::string otw_;
    std::string data_type_;  // processing data type, should be consist

    // ========================================================================
    // Energy Detector (IIR for now) and AGC Configuration
    // ========================================================================
    
    size_t energy_packet_size_;
    size_t IIR_window_size_;
    float alpha_;
    float energy_threshold_;
    float IIR_threshold_multiplier_;
    bool IIR_threshold_adaptive_;
    std::string AGC_type_;

    // ========================================================================
    // Match Filter Configuration
    // ========================================================================
    
    int num_taps_;
    int U_;
    int D_;
    int num_threads_;
    double symbol_rate_;
    double roll_off_;
    std::string filter_type_;

    // ========================================================================
    // Synchronization Configuration
    // ========================================================================

    int sps_sync_;
    int recv_msg_len_;  // will be moved after add the length to CRC or header
    float sync_threshold_;

    // ========================================================================
    // Demodulation Configuration
    // ========================================================================
    
    int preamble_length_;  // m
    bool add_preamble_;
    std::string demod_scheme_;
    std::string preamble_type_;

    // ========================================================================
    // USRP Device Handle
    // ========================================================================

    uhd::usrp::multi_usrp::sptr rx_usrp_;
    
    // ========================================================================
    // FIFOs for pipeline (your existing structure)
    // ========================================================================

    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> recv_fifo_;
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> detected_fifo_;
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> agc_fifo_;
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> filter_fifo_;
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> synced_fifo_;
    MutexFIFO<std::pair<size_t, std::vector<uint8_t>>>  demod_fifo_;
    MutexFIFO<std::vector<uint8_t>> output_fifo_;  // Demodulated bits → Python

    // ========================================================================
    // Threads
    // ========================================================================

    std::thread receive_thread_;
    std::thread EnergyDetection_thread_;
    std::thread AGC_thread_;
    std::thread Match_filter_thread_;
    std::thread TimeSync_thread_;
    std::thread Demodulation_thread_;
    std::thread Output_thread_;  // Converts bits to strings for Python
    std::thread Watchdog_thread_;
    
    // ========================================================================
    // Control flags
    // ========================================================================

    std::atomic<bool> stop_sign_;
    std::atomic<bool> initialized_;
    bool signal_handler_installed_;
    
    // ========================================================================
    // Preamble
    // ========================================================================

    std::vector<std::complex<float>> dbpsk_preamble_;  // should be same as transmitter

    // ========================================================================
    // Construct Detector
    // ========================================================================

    EnergyDetectorIIR detector_;

    // ========================================================================
    // Function to monitor all stop signs
    // ========================================================================

    void watchdog_monitor() {
        std::cout << "[WATCHDOG] Started monitoring for signals" << std::endl;
        
        while (!global_stop_signal.load()) {
            // Check every 100ms
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            
            // If global signal detected, propagate it
            if (global_stop_signal.load() && !stop_sign_.load()) {
                std::cout << "[WATCHDOG] Global stop signal detected - propagating..." << std::endl;
                stop_sign_.store(true);
                break;
            }
        }
        
        std::cout << "[WATCHDOG] Stopped" << std::endl;
    }
    
    // ========================================================================
    // Output processing thread (pass the message to Python)
    // ========================================================================

    void output_processor() {

        std::cout << "[RECEIVE API OUTPUT] Started! " << std::endl;
        
        while(!stop_sign_.load() && !global_stop_signal.load()){
            std::pair<size_t, std::vector<uint8_t>> message;
            
            if (!demod_fifo_.pop(message)){continue;}

            output_fifo_.push(message.second);
        }

        std::cout << "[RECEIVE API OUTPUT] Stopped. " << std::endl;
    }

    // ========================================================================
    // Generate Preamble
    // ========================================================================

    void generate_preamble() {
        if (!add_preamble_) {
            dbpsk_preamble_.clear();
            return;
        }
        
        std::cout << "[PREAMBLE GENERATION] Generating preamble (length=" << preamble_length_ << ")..." << std::endl;
        
        if (preamble_type_ == "m-sequence") {
            MSequenceGenerator mseq(preamble_length_);
            dbpsk_preamble_ = mseq.modulate(PreambleModType::DBPSK);
            std::cout << "[PREAMBLE GENERATION] Generated m-sequence preamble with " 
                     << dbpsk_preamble_.size() << " symbols" << std::endl;
        } else {
            std::cout << "[PREAMBLE GENERATION] No preamble type specified" << std::endl;
            dbpsk_preamble_.clear();
        }
    }

    // ========================================================================
    // Initialize USRP
    // ========================================================================

    bool initialize_usrp() {
        std::cout << "[RECEIVE USRP] Initializing receiver..." << std::endl;
        
        try {

            std::signal(SIGINT, sig_int_handler);

            rx_usrp_ = uhd::usrp::multi_usrp::make(rx_args_);
            
            if (!rx_subdev_.empty()) {
                rx_usrp_->set_rx_subdev_spec(rx_subdev_);
            }
            
            std::cout << "[RECEIVE USRP] Using device: " << rx_usrp_->get_pp_string() << std::endl;
            
            if (!ref_.empty()) {
                rx_usrp_->set_clock_source(ref_);
            }
            
            rx_usrp_->set_rx_rate(rx_rate_);
            std::cout << "[RECEIVE USRP] Actual RX Rate: " << rx_usrp_->get_rx_rate() / 1e6 << " Msps" << std::endl;
            
            uhd::tune_request_t rx_tune_request(rx_freq_);
            rx_usrp_->set_rx_freq(rx_tune_request);
            std::cout << "[RECEIVE USRP] Actual RX Freq: " << rx_usrp_->get_rx_freq() / 1e6 << " MHz" << std::endl;
            
            rx_usrp_->set_rx_gain(rx_gain_);
            std::cout << "[RECEIVE USRP] Actual RX Gain: " << rx_usrp_->get_rx_gain() << " dB" << std::endl;
            
            rx_usrp_->set_rx_antenna(rx_ant_);
            rx_usrp_->set_rx_bandwidth(rx_bw_);
            
            // Check LO locked
            std::vector<std::string> rx_sensor_names = rx_usrp_->get_rx_sensor_names(0);
            if (std::find(rx_sensor_names.begin(), rx_sensor_names.end(), "lo_locked") != rx_sensor_names.end()) {
                uhd::sensor_value_t lo_locked = rx_usrp_->get_rx_sensor("lo_locked", 0);
                std::cout << boost::format("[RECEIVE USRP] Checking RX: %s ...") % lo_locked.to_pp_string() << std::endl;
                UHD_ASSERT_THROW(lo_locked.to_bool());
            }
            
            std::this_thread::sleep_for(std::chrono::milliseconds(long(settling_time_ * 1000)));
            
            std::cout << "[RECEIVE USRP] Initialization successful!" << std::endl;
            return true;
            
        } catch (const std::exception& e) {
            std::cerr << "[RECEIVE USRP] ERROR: " << e.what() << std::endl;
            return false;
        }
    }

public:

    // ========================================================================
    // Constructor
    // ========================================================================

    Receiver_API()
        : 
          rx_channel_(0),
          samps_per_buff_(10000),
          num_recv_request_(0),
          rx_freq_(2.412e9),
          rx_rate_(1e6),
          rx_gain_(20.0),
          rx_bw_(500e3),
          settling_time_(0.2),
          uhd_timeout_(1000.0),
          rx_args_(""),
          rx_ant_("RX2"),
          rx_subdev_("A:0"),
          ref_("internal"),
          otw_("sc16"),
          data_type_("float"),
          energy_packet_size_(1340),
          IIR_window_size_(1),
          alpha_(0.96),
          energy_threshold_(0.2),
          IIR_threshold_multiplier_(8.0),
          IIR_threshold_adaptive_(true),
          AGC_type_("Feed"),
          num_taps_(151),
          U_(4),
          D_(1),
          num_threads_(1),
          symbol_rate_(0.8e6),
          roll_off_(0.25),
          filter_type_("rrc"),
          sps_sync_(5),
          recv_msg_len_(1017),
          sync_threshold_(16.0),
          preamble_length_(5),
          add_preamble_(true),
          demod_scheme_("DBPSK"),
          preamble_type_("m-sequence"),
          rx_usrp_(nullptr),
          stop_sign_(false),
          initialized_(false),
          signal_handler_installed_(false)
    {
        g_active_receiver = this;
        
        std::cout << "[RX-WRAPPER] Receiver wrapper created" << std::endl;
    }
    
    ~Receiver_API() {
        
        if (g_active_receiver == this) {
            g_active_receiver = nullptr;
        }

        stop();
    }
    
    // ========================================================================
    // Configuration Methods
    // ========================================================================

    // Set USRP configurations (Can be replaced with single function)

    void set_rx_channel(int channel) {rx_channel_ = channel; }
    void set_samps_per_buff(int spb) {samps_per_buff_ = spb; }
    void set_num_recv_request(int recv_samples) { num_recv_request_ = recv_samples; }
    void set_settling_time(float settling) {settling_time_ = settling; }
    void set_uhd_timeout(float timeout_uhd) {uhd_timeout_ = timeout_uhd; }
    void set_rx_freq(double freq_hz) { rx_freq_ = freq_hz; }
    void set_rx_rate(double rate_hz) { rx_rate_ = rate_hz; }
    void set_rx_gain(double gain_db) { rx_gain_ = gain_db; }
    void set_rx_bw(double bw_hz) { rx_bw_ = bw_hz; }
    void set_rx_args(const std::string& args) { rx_args_ = args; }
    void set_rx_antenna(const std::string& ant) { rx_ant_ = ant; }
    void set_rx_subdev(const std::string& subdev) { rx_subdev_ = subdev; }
    void set_ref(const std::string& ref) { ref_ = ref; }
    void set_otw(const std::string& otw) { otw_ = otw; }
    void set_data_type(const std::string& data_type) { data_type_ = data_type; }

    // Set Threads Parameters

    void set_energy_detector(int energy_packet_size, int IIR_window_size, float alpha,
                             float energy_threshold, float IIR_threshold_multiplier,
                             bool IIR_threshold_adaptive, const std::string& AGC_type) {
        energy_packet_size_ = energy_packet_size;
        IIR_window_size_ = IIR_window_size;
        alpha_ = alpha;
        energy_threshold_ = energy_threshold;
        IIR_threshold_multiplier_ = IIR_threshold_multiplier;
        IIR_threshold_adaptive_ = IIR_threshold_adaptive;
        AGC_type_ = AGC_type;
    }

    void set_filter(int num_taps, int U, int D, int num_threads,
                   double symbol_rate, double roll_off, const std::string& type) {

        num_taps_ = num_taps;
        U_ = U;
        D_ = D;
        num_threads_ = num_threads;
        symbol_rate_ = symbol_rate;
        roll_off_ = roll_off;
        filter_type_ = type;
    }

    void set_sync_and_demod(int recv_msg_len, int sps_sync, float sync_threshold,
                            int preamble_length, bool add_preamble, 
                            const std::string& preamble_type, const std::string& demod_scheme){
        // Synchronization Parameters
        recv_msg_len_ = recv_msg_len;
        sps_sync_ = sps_sync;
        sync_threshold_ = sync_threshold;

        // Demodulation Parameters
        preamble_length_ = preamble_length;
        add_preamble_ = add_preamble;
        preamble_type_ = preamble_type;
        demod_scheme_ = demod_scheme;
    }

    // ========================================================================
    // Start Receiver
    // ========================================================================
    bool start() {
        if (initialized_.load()) {
            std::cout << "[RECEIVE API] Already running" << std::endl;
            return false;
        }

        stop_sign_.store(false);
        global_stop_signal.store(false);

        // Install signal handler if not already installed
        if (!signal_handler_installed_) {
            std::signal(SIGINT, sig_int_handler);
            signal_handler_installed_ = true;
            std::cout << "[RECEIVE WRAPPER] Signal handler installed (Ctrl+C will stop transmitter)" << std::endl;
        }

        if (!initialize_usrp()){
            std::cerr << "[PYTHON RECEIVE WRAPPER] Failed to initialize USRP!" << std::endl;
            return false;
        }

        // Verify USRP is valid
        if (!rx_usrp_) {
            std::cerr << "[RECEIVE WRAPPER] ERROR: USRP pointer is null!" << std::endl;
            stop_sign_ = true;
            return false;
        }
        
        std::cout << "[RECEIVE WRAPPER] USRP initialized successfully" << std::endl;

        generate_preamble();

        // Launch threads in order: receive → filter → demod → output
        
        // 1. Receive thread (from USRP)
        try {
            std::vector<unsigned long> channel = {static_cast<unsigned long>(rx_channel_)};
            receive_thread_ = std::thread(receive_thread,
                                         rx_usrp_,
                                         channel,
                                         rx_rate_,
                                         settling_time_,
                                         std::ref(recv_fifo_),
                                         num_recv_request_,
                                         samps_per_buff_,                                         
                                         std::ref(stop_sign_));
            std::cout << "[RECEIVE WRAPPER] Receive thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[RECEIVE WRAPPER] Failed to start receive thread: " << e.what() << std::endl;
            stop_sign_.store(true);
            stop();
            return false;
        }
        
        // 2. Energy Detector thread
        try {
            detector_ = EnergyDetectorIIR(alpha_, 
                                       energy_threshold_, 
                                       energy_packet_size_, 
                                       IIR_window_size_, 
                                       IIR_threshold_adaptive_,
                                       IIR_threshold_multiplier_);

            EnergyDetection_thread_ = std::thread(EnergyDetection_thread,
                                        std::ref(recv_fifo_),
                                        std::ref(detected_fifo_),
                                        std::ref(detector_),
                                        std::ref(stop_sign_));

            std::cout << "[RECEIVE WRAPPER] Energy Detector thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[RECEIVE WRAPPER] Failed to start Energy Detector thread: " << e.what() << std::endl;
            stop_sign_.store(true);
            stop();
            return false;
        }
        
        // 3. AGC thread
        try {
            AGC_thread_ = std::thread(AGC_thread,
                                      std::ref(detected_fifo_),
                                      std::ref(agc_fifo_),
                                      std::ref(stop_sign_),
                                      AGC_type_);

            std::cout << "[RECEIVE WRAPPER] AGC thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[RECEIVE WRAPPER] Failed to start AGC thread: " << e.what() << std::endl;
            stop_sign_.store(true);
            stop();
            return false;
        }
        

        // 4. Match filter thread
        try {
            Match_filter_thread_ = std::thread(match_filter_thread,
                                        std::ref(agc_fifo_),
                                        std::ref(filter_fifo_),
                                        filter_type_,
                                        symbol_rate_,
                                        rx_rate_,
                                        num_taps_,
                                        U_, D_,
                                        roll_off_,
                                        num_threads_,
                                        std::ref(stop_sign_),
                                        "receiver");

            std::cout << "[RECEIVE WRAPPER] Match filter thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[RECEIVE WRAPPER] Failed to start Match filter thread: " << e.what() << std::endl;
            stop_sign_.store(true);
            stop();
            return false;
        }

        // 5. Filter thread
        try {
            TimeSync_thread_ = std::thread(TimeSync_thread,
                                        std::ref(filter_fifo_),
                                        std::ref(synced_fifo_),
                                        std::ref(dbpsk_preamble_),
                                        U_, D_,
                                        sps_sync_,
                                        std::ref(stop_sign_),
                                        recv_msg_len_,
                                        sync_threshold_);

            std::cout << "[RECEIVE WRAPPER] Time Sync thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[RECEIVE WRAPPER] Failed to start Time Sync thread: " << e.what() << std::endl;
            stop_sign_.store(true);
            stop();
            return false;
        }
        
        // 6. Demodulation thread
        try {
            Demodulation_thread_ = std::thread(demodulation_thread,
                                       std::ref(synced_fifo_),
                                       std::ref(demod_fifo_),
                                       std::ref(demod_scheme_),
                                       std::ref(stop_sign_));

            std::cout << "[RECEIVE WRAPPER] Demodulation thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[RECEIVE WRAPPER] Failed to start Demodulation thread: " << e.what() << std::endl;
            stop_sign_.store(true);
            stop();
            return false;
        }
        
        // 7. Output processor (bits → Python)
        try {
            Output_thread_ = std::thread(&Receiver_API::output_processor, this);
            std::cout << "[RECEIVE WRAPPER] Output thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[RECEIVE WRAPPER] Failed to start Output thread: " << e.what() << std::endl;
            stop_sign_.store(true);
            stop();
            return false;
        }
        
        // 8. Watchdog thread
        try {
            Watchdog_thread_ = std::thread(&Receiver_API::watchdog_monitor, this);
            std::cout << "[RECEIVE WRAPPER] Watchdog thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[RECEIVE WRAPPER] Failed to start Watchdog: " << e.what() << std::endl;
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        initialized_.store(true);
        std::cout << "[RECEIVE WRAPPER] Receiver started successfully" << std::endl;
        std::cout << "[RECEIVE WRAPPER] Press Ctrl+C to stop" << std::endl;
        return true;
    }

    // ========================================================================
    // Stop Receiver
    // ========================================================================
    void stop() {
        if (!initialized_.load()) {
            return;
        }
        
        std::cout << "[PYTHON RECEIVE WRAPPER] Stopping receiver..." << std::endl;
        
        stop_sign_.store(true);
        global_stop_signal.store(true);

        // Join all threads
        if (receive_thread_.joinable()) receive_thread_.join();
        if (EnergyDetection_thread_.joinable()) EnergyDetection_thread_.join();
        if (AGC_thread_.joinable()) AGC_thread_.join();
        if (Match_filter_thread_.joinable()) Match_filter_thread_.join();
        if (TimeSync_thread_.joinable()) TimeSync_thread_.join();
        if (Demodulation_thread_.joinable()) Demodulation_thread_.join();
        if (Output_thread_.joinable()) Output_thread_.join();
        if (Watchdog_thread_.joinable()) Watchdog_thread_.join();
        
        initialized_.store(false);
        std::cout << "[PYTHON RECEIVE WRAPPER] Receiver stopped" << std::endl;
    }

    void request_stop() {
        stop_sign_.store(true);
    }

    py::object receive_message() {
        std::vector<uint8_t> bits;
        
        if (output_fifo_.pop(bits)) {
            // Convert bits to string
            std::string message = bits_to_string(bits, int(bits.size() / 8));
            return py::cast(message);  // Convert the C++ string to the python char
        }
        
        return py::none();
    }
    
    py::object receive_bits() {
        std::vector<uint8_t> bits;
        
        if (output_fifo_.pop(bits)) {
            std::vector<uint8_t> message = bits_to_bytes(bits);
            return py::cast(message);
        }
        
        return py::none();
    }

    // ========================================================================
    // Status
    // ========================================================================
    py::dict get_status() {
        py::dict status;
        status["running"] = initialized_.load();
        status["rx_queue_size"] = recv_fifo_.size();
        status["filter_queue_size"] = filter_fifo_.size();
        status["demod_queue_size"] = demod_fifo_.size();
        status["output_queue_size"] = output_fifo_.size();
        status["rx_freq_mhz"] = rx_freq_ / 1e6;
        status["rx_rate_msps"] = rx_rate_ / 1e6;
        status["rx_gain_db"] = rx_gain_;
        status["scheme"] = demod_scheme_;
        status["signal_received"] = global_stop_signal.load();
        return status;
    }
    
    py::dict get_config() {
        py::dict config;

        config["rx_channel"] = rx_channel_;
        config["samps_per_buff"] = samps_per_buff_;
        config["num_recv_request"] = num_recv_request_;
        config["rx_freq"] = rx_freq_;
        config["rx_rate"] = rx_rate_;
        config["rx_gain"] = rx_gain_;
        config["rx_bw"] = rx_bw_;
        config["settling_time"] = settling_time_;
        config["uhd_timeout"] = uhd_timeout_;
        config["rx_args"] = rx_args_;
        config["rx_antenna"] = rx_ant_;
        config["rx_subdev"] = rx_subdev_;
        config["ref"] = ref_;
        config["otw"] = otw_;
        config["data_type"] = data_type_;

        config["energy_packet_size"] = energy_packet_size_;
        config["IIR_window_size"] = IIR_window_size_;
        config["alpha"] = alpha_;
        config["energy_threshold"] = energy_threshold_;
        config["IIR_threshold_multiplier"] = IIR_threshold_multiplier_;
        config["IIR_threshold_adaptive"] = IIR_threshold_adaptive_;
        config["AGC_type"] = AGC_type_;
        
        config["num_taps"] = num_taps_;
        config["U"] = U_;
        config["D"] = D_;
        config["num_threads"] = num_threads_;
        config["symbol_rate"] = symbol_rate_;
        config["roll_off"] = roll_off_;
        config["filter_type"] = filter_type_;

        config["sps_sync"] = sps_sync_;
        config["recv_msg_len"] = recv_msg_len_;
        config["sync_threshold"] = sync_threshold_;

        config["preamble_length"] = preamble_length_;
        config["add_preamble"] = add_preamble_;
        config["demod_scheme"] = demod_scheme_;
        config["preamble_type"] = preamble_type_;

        return config;
    }
};

void sig_int_handler(int) {
    std::signal(SIGINT, SIG_DFL);
    global_stop_signal.store(true);

    std::cout << "\n[SIGNAL] Ctrl+C detected - stopping transmitter..." << std::endl;

    // Simply request stop
    if (g_active_receiver != nullptr) {
        std::cout << "[SIGNAL] Marking stop request" << std::endl;
        g_active_receiver->request_stop();   // new function
    }

    // Now forward signal to Python
    std::raise(SIGINT);
}

// ============================================================================
// Python Binding
// ============================================================================
PYBIND11_MODULE(receiver, m) {
    m.doc() = "USRP Receiver wrapper for Python";
    
    py::class_<Receiver_API>(m, "Receiver")
        .def(py::init<>(), "Create receiver wrapper")
        
        // USRP Configuration
        .def("set_rx_channel", &Receiver_API::set_rx_channel,
             py::arg("channel"), "Set RX channel")

        .def("set_samps_per_buff", &Receiver_API::set_samps_per_buff,
             py::arg("spb"), "Set samples per buffer")
        
        .def("set_num_recv_request", &Receiver_API::set_num_recv_request,
             py::arg("recv_samples"), "Set expected Receive samples")
            
        .def("set_settling_time", &Receiver_API::set_settling_time,
             py::arg("settling"), "Set system settling time")

        .def("set_uhd_timeout", &Receiver_API::set_uhd_timeout,
             py::arg("timeout_uhd"), "Set UHD timeout for waiting")

        .def("set_rx_freq", &Receiver_API::set_rx_freq,
             py::arg("freq_hz"), "Set RX center frequency in Hz")

        .def("set_rx_rate", &Receiver_API::set_rx_rate,
             py::arg("rate_hz"), "Set RX sample rate in Hz")

        .def("set_rx_gain", &Receiver_API::set_rx_gain,
             py::arg("gain_db"), "Set RX gain in dB")

        .def("set_rx_bw", &Receiver_API::set_rx_bw,
             py::arg("bw_hz"), "Set RX bandwidth in Hz")

        .def("set_rx_args", &Receiver_API::set_rx_args,
             py::arg("args"), "Set USRP device arguments")

        .def("set_rx_antenna", &Receiver_API::set_rx_antenna,
             py::arg("ant"), "Set RX antenna (e.g., 'RX2')")

        .def("set_rx_subdev", &Receiver_API::set_rx_subdev,
             py::arg("subdev"), "Set RX subdevice (e.g., 'A:0')")

        .def("set_ref", &Receiver_API::set_ref,
             py::arg("ref"), "Set clock reference (internal/external/mimo)")
        
        .def("set_otw", &Receiver_API::set_otw,
             py::arg("otw"), "Set wired datatype (sc16)")

        .def("set_data_type", &Receiver_API::set_data_type,
             py::arg("data_type"), "Set operating datatype (int, float, double)")

        .def("set_energy_detector", &Receiver_API::set_energy_detector,
             py::arg("energy_packet_size"),
             py::arg("IIR_window_size"),
             py::arg("alpha"),
             py::arg("energy_threshold"),
             py::arg("IIR_threshold_multiplier"),
             py::arg("IIR_threshold_adaptive"),
             py::arg("AGC_type"),
             "Configure energy detector")

        .def("set_energy_detector", &Receiver_API::set_energy_detector,
             py::arg("energy_packet_size"),
             py::arg("IIR_window_size"),
             py::arg("alpha"),
             py::arg("energy_threshold"),
             py::arg("IIR_threshold_multiplier"),
             py::arg("IIR_threshold_adaptive"),
             py::arg("AGC_type"),
             "Configure energy detector")

        .def("set_filter", &Receiver_API::set_filter,
             py::arg("num_taps"),
             py::arg("U"),
             py::arg("D"),
             py::arg("num_threads"),
             py::arg("symbol_rate"),
             py::arg("roll_off"),
             py::arg("type"),
             "Configure match filter")
        
        .def("set_sync_and_demod", &Receiver_API::set_sync_and_demod,
             py::arg("recv_msg_len"),
             py::arg("sps_sync"),
             py::arg("sync_threshold"),
             py::arg("preamble_length"),
             py::arg("add_preamble"),
             py::arg("preamble_type"),
             py::arg("demod_scheme"),
             "Configure synchronization and demodulaion")
        
        // Control
        .def("start", &Receiver_API::start,
             "Start Receiver")

        .def("stop", &Receiver_API::stop,
             "Stop Receiver")

        // Data
        .def("receive_message", &Receiver_API::receive_message,
             "Receive demodulated message as string")

        .def("receive_bits", &Receiver_API::receive_bits,
             "Receive demodulated bits as list")
        
        // Status
        .def("get_status", &Receiver_API::get_status)
        .def("get_config", &Receiver_API::get_config);
}
