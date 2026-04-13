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

namespace py = pybind11;

static std::atomic<bool> global_stop_signal(false);

class Transmitter_API;
static Transmitter_API* g_active_transmitter = nullptr;
void sig_int_handler(int);

class Transmitter_API{
private:
    // These parameters are defined from python side
    // Message parameters
    size_t num_bits_;
    int message_interval_;
    bool continues_;  // continues or not (continues mod should be revised)
    size_t repeat_times_;

    // Modulation paramters
    int preamble_length_;
    bool add_preamble_;
    std::string preamble_type_;  // currently using known m-sequence
    std::string mod_scheme_;

    // Filter parameters
    int U_;  // upsampling factor
    int D_;  // downsampling factor
    int num_taps_;
    int num_threads_;
    int sps_;  // samples per symbol
    double roll_off_;
    std::string filter_type_;  // currently only has rrc pulse design

    // Transmitter parameters
    int tx_channel_;
    double tx_rate_;
    double tx_freq_;
    double symbol_rate_;
    double tx_gain_;
    double tx_bw_;
    double settling_time_;
    double uhd_timeout_;
    std::string tx_args_;
    std::string tx_ant_;
    std::string tx_subdev_;
    std::string ref_;  // clock reference (internal or external)
    std::string otw_;  // wire data type (e.g. sc16)

    // Control Flag
    std::atomic<bool> stop_sign_;
    std::atomic<bool> initialized_;
    bool signal_handler_installed_;

    // USRP Device handle
    uhd::usrp::multi_usrp::sptr tx_usrp_;

    // FIFOs
    MutexFIFO<std::string> message_string_fifo_;
    MutexFIFO<std::vector<uint8_t>> message_bits_fifo_;
    MutexFIFO<std::vector<uint8_t>> message_fifo_;
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> mod_fifo_;
    MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>> filter_fifo_;

    // Physical layer threads
    std::thread message_thread_;
    std::thread modulation_thread_;
    std::thread filter_thread_;
    std::thread transmit_thread_;
    std::thread watchdog_thread_;  // Monitors global_stop_signal

    // Preamble (add more preamble types and generation function in future)
    std::vector<std::complex<float>> dbpsk_preamble_;

    // Function to monitor all stop signs
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

    void python_message_reader(){
        std::cout << "[PYTHON READER] Start! " << std::endl;
        std::string message;
        size_t message_count;
        std::vector<uint8_t> bits;
        while (!stop_sign_.load()){
            if (!message_string_fifo_.pop(message)) {continue;}

            message_count++;
            bits = generate_message_block(message, message_count, num_bits_);
            std::cout << "[PYTHON MESSAGE] Got message from python + header (16) " << bits.size() << std::endl;

            for (size_t i = 0; i < repeat_times_; i++){
                message_fifo_.push(bits);
                if (!continues_ && message_interval_ > 0){
                    std::this_thread::sleep_for(std::chrono::milliseconds(message_interval_));
                }
            }
        }
        
        if (global_stop_signal.load()) {
            std::cout << "[PYTHON READER] Stopped by signal handler" << std::endl;
        } 
    }

    void python_bits_reader(){
        std::cout << "[PYTHON READER] Start! " << std::endl;
        size_t message_count;
        std::vector<uint8_t> bits;
        while (!stop_sign_.load()){
            if (!message_bits_fifo_.pop(bits)) {continue;}

            message_count++;
            // bits = generate_message_block(message, message_count, num_bits_);
            std::cout << "[PYTHON MESSAGE] Got message from python " << bits.size() << std::endl;

            for (size_t i = 0; i < repeat_times_; i++){
                message_fifo_.push(bits);
                if (!continues_ && message_interval_ > 0){
                    std::this_thread::sleep_for(std::chrono::milliseconds(message_interval_));
                }
            }
        }
        
        if (global_stop_signal.load()) {
            std::cout << "[PYTHON READER] Stopped by signal handler" << std::endl;
        } 
    }

    // USRP Intialization
    bool initialize_usrp(){
        std::cout << "[USRP INITIALIZATION] Transmitter intialization start ... " << std::endl;

        try {

            std::signal(SIGINT, sig_int_handler);
            // Create USRP device
            tx_usrp_ = uhd::usrp::multi_usrp::make(tx_args_);
            
            // Set subdevice
            if (!tx_subdev_.empty()) {
                tx_usrp_->set_tx_subdev_spec(tx_subdev_);
            }
            
            std::cout << "[USRP] Using TX Device: " << tx_usrp_->get_pp_string() << std::endl;
            
            // Set clock reference
            if (!ref_.empty()) {
                tx_usrp_->set_clock_source(ref_);
            }
            
            // Set sample rate
            tx_usrp_->set_tx_rate(tx_rate_);
            std::cout << "[USRP] Actual TX Rate: " << tx_usrp_->get_tx_rate() / 1e6 << " Msps" << std::endl;
            
            // Set center frequency
            uhd::tune_request_t tx_tune_request(tx_freq_);
            tx_usrp_->set_tx_freq(tx_tune_request);
            std::cout << "[USRP] Actual TX Freq: " << tx_usrp_->get_tx_freq() / 1e6 << " MHz" << std::endl;
            
            // Set gain
            tx_usrp_->set_tx_gain(tx_gain_);
            std::cout << "[USRP] Actual TX Gain: " << tx_usrp_->get_tx_gain() << " dB" << std::endl;
            
            // Set antenna
            tx_usrp_->set_tx_antenna(tx_ant_);
            
            // Set bandwidth
            tx_usrp_->set_tx_bandwidth(tx_bw_);
            
            // Check LO locked
            std::vector<std::string> tx_sensor_names = tx_usrp_->get_tx_sensor_names(0);
            if (std::find(tx_sensor_names.begin(), tx_sensor_names.end(), "lo_locked") != tx_sensor_names.end()) {
                uhd::sensor_value_t lo_locked = tx_usrp_->get_tx_sensor("lo_locked", 0);
                std::cout << boost::format("[USRP] Checking TX: %s ...") % lo_locked.to_pp_string() << std::endl;
                UHD_ASSERT_THROW(lo_locked.to_bool());
            }
            
            // Settling time
            std::this_thread::sleep_for(std::chrono::milliseconds(long(settling_time_ * 1000)));
            
            std::cout << "[USRP] Initialization successful!" << std::endl;
            return true;
            
        } catch (const std::exception& e) {
            std::cerr << "[USRP] ERROR: " << e.what() << std::endl;
            return false;
        }
    }
    
    // Generate Preamble
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

public:
    // constructor of transmitter
    Transmitter_API()
      : tx_freq_(2.412e9),
        tx_rate_(1e6),
        tx_gain_(20.0),
        tx_bw_(500e3),
        tx_args_(""),
        tx_ant_("TX/RX"),
        tx_subdev_("A:0"),
        ref_("internal"),
        otw_("sc16"),
        tx_channel_(0),
        settling_time_(0.2),
        uhd_timeout_(1000.0),
        num_bits_(1000),
        message_interval_(1000),
        continues_(false),
        repeat_times_(3),
        mod_scheme_("DBPSK"),
        add_preamble_(true),
        preamble_length_(5),
        preamble_type_("m-sequence"),
        filter_type_("rrc"),
        symbol_rate_(0.8e6),
        num_taps_(151),
        U_(5),
        D_(4),
        roll_off_(0.25),
        num_threads_(1),
        stop_sign_(false),
        initialized_(false),
        tx_usrp_(nullptr),
        signal_handler_installed_(false)
    {
        // Register this instance for signal handler
        g_active_transmitter = this;

        std::cout << "[PYTHON READER] Transmitter intialization complete! " << std::endl;
    }

    ~Transmitter_API(){
        if (initialized_.load()){
            stop();
        }

        // Unregister from signal handler
        if (g_active_transmitter == this) {
            g_active_transmitter = nullptr;
        }
    }

    // Configuration methods (called in python before start)
    // USRP Configuration
    void set_tx_freq(double freq_hz) {
        tx_freq_ = freq_hz;
        std::cout << "[TRANSMITTER CONFIG] TX freq set to " << freq_hz / 1e6 << " MHz" << std::endl;
    }
    
    void set_tx_rate(double rate_hz) {
        tx_rate_ = rate_hz;
        std::cout << "[TRANSMITTER CONFIG] TX rate set to " << rate_hz / 1e6 << " Msps" << std::endl;
    }
    
    void set_tx_gain(double gain_db) {
        tx_gain_ = gain_db;
        std::cout << "[TRANSMITTER CONFIG] TX gain set to " << gain_db << " dB" << std::endl;
    }
    
    void set_tx_bw(double bw_hz) {
        tx_bw_ = bw_hz;
        std::cout << "[TRANSMITTER CONFIG] TX bandwidth set to " << bw_hz / 1e6 << " MHz" << std::endl;
    }
    
    void set_tx_args(const std::string& args) {
        tx_args_ = args;
        std::cout << "[TRANSMITTER CONFIG] TX args set to: " << args << std::endl;
    }
    
    void set_tx_antenna(const std::string& ant) {
        tx_ant_ = ant;
        std::cout << "[TRANSMITTER CONFIG] TX antenna set to: " << ant << std::endl;
    }
    
    void set_tx_subdev(const std::string& subdev) {
        tx_subdev_ = subdev;
        std::cout << "[TRANSMITTER CONFIG] TX subdev set to: " << subdev << std::endl;
    }
    
    void set_ref(const std::string& ref) {
        ref_ = ref;
        std::cout << "[TRANSMITTER CONFIG] Clock reference set to: " << ref << std::endl;
    }
    
    // Message Configuration
    void set_num_bits(size_t bits) {
        num_bits_ = bits;
        std::cout << "[TRANSMITTER CONFIG] Num bits set to " << bits << std::endl;
    }
    
    void set_message_interval(int ms) {
        message_interval_ = ms;
        std::cout << "[TRANSMITTER CONFIG] Interval set to " << ms << " ms" << std::endl;
    }
    
    void set_continuous(bool cont) {
        continues_ = cont;
        std::cout << "[TRANSMITTER CONFIG] Continuous mode: " << (cont ? "ON" : "OFF") << std::endl;
    }
    
    // Modulation Configuration
    void set_mod_scheme(const std::string& scheme) {
        mod_scheme_ = scheme;
        std::cout << "[TRANSMITTER CONFIG] Modulation scheme set to: " << scheme << std::endl;
    }
    
    void set_preamble(bool add_preamble, int length, const std::string& type) {
        add_preamble_ = add_preamble;
        preamble_length_ = length;
        preamble_type_ = type;
        std::cout << "[TRANSMITTERCONFIG] Preamble: " << (add_preamble ? "ON" : "OFF") 
                 << " (length=" << length << ", type=" << type << ")" << std::endl;
    }
    
    // Filter Configuration
    void set_filter(const std::string& type, double symbol_rate, int num_taps, 
                   int U, int D, double roll_off, int num_threads) {
        filter_type_ = type;
        symbol_rate_ = symbol_rate;
        num_taps_ = num_taps;
        U_ = U;
        D_ = D;
        roll_off_ = roll_off;
        num_threads_ = num_threads;
        std::cout << "[CONFIG] Filter: type=" << type << ", symbol_rate=" << symbol_rate/1e6 
                 << " MHz, taps=" << num_taps << ", U=" << U << ", D=" << D 
                 << ", roll_off=" << roll_off << std::endl;
    }

    // Repeat time setting
    void set_repeat_time(size_t repeat_times) {
        repeat_times_ = repeat_times;
        std::cout << "[TRANSMITTER CONFIG] Repeat time set to: " << repeat_times_ << std::endl;
    }

    // Start transmitter (Launch all threads)
    bool start(std::string message_type){
        if (initialized_.load()){
            std::cout << "[PYTHON TRANSMIT WRAPPER] Already running ... " << initialized_.load() << std::endl;
            return false;
        }

        stop_sign_.store(false);
        global_stop_signal.store(false);

        // Install signal handler if not already installed
        if (!signal_handler_installed_) {
            std::signal(SIGINT, sig_int_handler);
            signal_handler_installed_ = true;
            std::cout << "[TRANSMIT WRAPPER] Signal handler installed (Ctrl+C will stop transmitter)" << std::endl;
        }

        if (!initialize_usrp()){
            std::cerr << "[PYTHON TRANSMIT WRAPPER] Failed to initialize USRP!" << std::endl;
            return false;
        }

        // Verify USRP is valid
        if (!tx_usrp_) {
            std::cerr << "[TRANSMIT WRAPPER] ERROR: USRP pointer is null!" << std::endl;
            stop_sign_.store(true);
            return false;
        }
        
        std::cout << "[TRANSMIT WRAPPER] USRP initialized successfully" << std::endl;

        generate_preamble();

        // 1. FIRST: Transmit thread (consumer - must be ready)
        //    Uses your existing transmit_thread function
        std::vector<unsigned long> channel = {static_cast<unsigned long>(tx_channel_)};
        try {
            transmit_thread_ = std::thread(transmit_thread,
                                          tx_usrp_,
                                          std::ref(filter_fifo_),
                                          tx_rate_,
                                          channel,
                                          uhd_timeout_,
                                          std::ref(stop_sign_));
            std::cout << "[TRANSMIT WRAPPER] Transmit thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[TRANSMIT WRAPPER] Failed to start transmit thread: " << e.what() << std::endl;
            // stop_sign_.store(true);
            // stop();
            return false;
        }
        
        // 2. Filter thread (reads from mod_fifo_, writes to filter_fifo_)
        try {
            filter_thread_ = std::thread(pulse_shaping_filter_thread,
                                         std::ref(mod_fifo_),
                                         std::ref(filter_fifo_),
                                         filter_type_,
                                         symbol_rate_,
                                         tx_rate_,
                                         num_taps_,
                                         U_, D_,
                                         roll_off_,
                                         num_threads_,
                                         std::ref(stop_sign_),
                                         "transmitter");
            std::cout << "[TRANSMIT WRAPPER] Filter thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[TRANSMIT WRAPPER] Failed to start filter thread: " << e.what() << std::endl;
            // stop_sign_.store(true);
            // stop();
            return false;
        }
        
        // 3. Modulation thread (reads from message_fifo_, writes to mod_fifo_)
        try {
            modulation_thread_ = std::thread(modulation_thread,
                                            std::ref(message_fifo_),
                                            std::ref(mod_fifo_),
                                            std::ref(mod_scheme_),
                                            std::ref(stop_sign_),
                                            dbpsk_preamble_,
                                            std::ref(add_preamble_));
            std::cout << "[TRANSMIT WRAPPER] Modulation thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[TRANSMIT WRAPPER] Failed to start modulation thread: " << e.what() << std::endl;
            // stop_sign_.store(true);
            // stop();
            return false;
        }
        
        // 4. LAST: Python message feeder (producer - starts last)
        try {
            if (message_type == "string"){ 
                message_thread_ = std::thread(&Transmitter_API::python_message_reader, this);
            } 
            else if (message_type == "bits"){
                message_thread_ = std::thread(&Transmitter_API::python_bits_reader, this);
            }
            else { 
                std::cout << "[TRANSMIT WRAPPER WARNING] Unrecognize message type, need to update!!!";
            }
            std::cout << "[TRANSMIT WRAPPER] Message feeder thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[TRANSMIT WRAPPER] Failed to start message feeder: " << e.what() << std::endl;
            // stop_sign_.store(true);
            // stop();
            return false;
        }

        // Give threads time to fully start
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        
        // Start watchdog thread last
        try {
            watchdog_thread_ = std::thread(&Transmitter_API::watchdog_monitor, this);
            std::cout << "[TRANSMIT WRAPPER] Watchdog thread started" << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "[TRANSMIT WRAPPER] Failed to start watchdog thread: " << e.what() << std::endl;
            // Non-critical, continue anyway
        }
        
        initialized_.store(true);
        std::cout << "[TRANSMIT WRAPPER] All threads started successfully!!!" << std::endl;
        std::cout << "[TRANSMIT WRAPPER] Press Ctrl+C to stop transmission!!!" << std::endl;
        return true;
    }

    void stop() {
        if (!initialized_.load()){return;}
        std::cout << "[PYTHON TRANSMIT WRAPPER] Stopping transmitter..." << std::endl;

        stop_sign_.store(true);

        // Join all threads
        if (message_thread_.joinable()) message_thread_.join();
        if (modulation_thread_.joinable()) modulation_thread_.join();
        if (filter_thread_.joinable()) filter_thread_.join();
        if (transmit_thread_.joinable()) transmit_thread_.join();
        
        initialized_.store(false);
        std::cout << "[PYTHON TRANSMIT WRAPPER] Transmitter stopped" << std::endl;
    }

    void send_message(const std::string message){
        if (!initialized_.load()) {
            std::cerr << "[PYTHON TRANSMIT WRAPPER] ERROR: Transmitter not started!" << std::endl;
            return;
        }
        
        message_string_fifo_.push(message);
        std::cout << "[PYTHON TRANSMIT WRAPPER] Queued String " << message << " for transmission" << std::endl;
    }

    void send_bits(py::array_t<uint8_t> bits) {
        if (!initialized_.load()) {
            std::cerr << "[PYTHON TRANSMIT WRAPPER] ERROR: Transmitter not started!" << std::endl;
            return;
        }
        
        auto buf = bits.request();
        uint8_t* ptr = static_cast<uint8_t*>(buf.ptr);
        
        // Store as vector
        std::vector<uint8_t> bit_vector(ptr, ptr + buf.size);
        message_bits_fifo_.push(std::move(bit_vector));
        
        std::cout << "[PYTHON TRANSMIT WRAPPER] Queued " << buf.size 
                << " bits for transmission" << std::endl;
    }

    void request_stop() {
        stop_sign_.store(true);
    }

    // Status and Utility Functions (for debugging)
    py::dict get_status() {
        py::dict status;
        status["running"] = initialized_.load();
        status["message_queue_size"] = message_fifo_.size();
        status["mod_queue_size"] = mod_fifo_.size();
        status["filter_queue_size"] = filter_fifo_.size();
        status["tx_freq_mhz"] = tx_freq_ / 1e6;
        status["tx_rate_msps"] = tx_rate_ / 1e6;
        status["tx_gain_db"] = tx_gain_;
        status["repeat_count"] = repeat_times_;
        status["mod_scheme"] = mod_scheme_;
        status["continuous"] = continues_;
        return status;
    }
    
    py::dict get_config() {
        py::dict config;
        
        // USRP config
        config["tx_freq"] = tx_freq_;
        config["tx_rate"] = tx_rate_;
        config["tx_gain"] = tx_gain_;
        config["tx_bw"] = tx_bw_;
        config["tx_args"] = tx_args_;
        config["tx_antenna"] = tx_ant_;
        
        // Message config
        config["num_bits"] = num_bits_;
        config["message_interval"] = message_interval_;
        config["continuous"] = continues_;
        
        // Modulation config
        config["mod_scheme"] = mod_scheme_;
        config["add_preamble"] = add_preamble_;
        config["preamble_length"] = preamble_length_;
        
        // Filter config
        config["filter_type"] = filter_type_;
        config["symbol_rate"] = symbol_rate_;
        config["num_taps"] = num_taps_;
        config["U"] = U_;
        config["D"] = D_;
        config["roll_off"] = roll_off_;
        
        return config;
    }
};

void sig_int_handler(int) {
    std::signal(SIGINT, SIG_DFL);
    global_stop_signal.store(true);

    std::cout << "\n[SIGNAL] Ctrl+C detected - stopping transmitter..." << std::endl;

    // Simply request stop
    if (g_active_transmitter != nullptr) {
        std::cout << "[SIGNAL] Marking stop request" << std::endl;
        g_active_transmitter->request_stop();   // new function
    }

    // Now forward signal to Python
    std::raise(SIGINT);
}

// =================== Pythin Binding =================== //
PYBIND11_MODULE(transmitter, m) {
    m.doc() = "USRP Transmitter wrapper - integrates with existing thread pipeline";
    
    py::class_<Transmitter_API>(m, "Transmitter")
        .def(py::init<>(), "Create transmitter wrapper")
        
        // USRP Configuration
        .def("set_tx_freq", &Transmitter_API::set_tx_freq,
             py::arg("freq_hz"),
             "Set TX center frequency in Hz")
        
        .def("set_tx_rate", &Transmitter_API::set_tx_rate,
             py::arg("rate_hz"),
             "Set TX sample rate in Hz")
        
        .def("set_tx_gain", &Transmitter_API::set_tx_gain,
             py::arg("gain_db"),
             "Set TX gain in dB")
        
        .def("set_tx_bw", &Transmitter_API::set_tx_bw,
             py::arg("bw_hz"),
             "Set TX bandwidth in Hz")
        
        .def("set_tx_args", &Transmitter_API::set_tx_args,
             py::arg("args"),
             "Set USRP device arguments")
        
        .def("set_tx_antenna", &Transmitter_API::set_tx_antenna,
             py::arg("antenna"),
             "Set TX antenna (e.g., 'TX/RX')")
        
        .def("set_tx_subdev", &Transmitter_API::set_tx_subdev,
             py::arg("subdev"),
             "Set TX subdevice (e.g., 'A:0')")
        
        .def("set_ref", &Transmitter_API::set_ref,
             py::arg("ref"),
             "Set clock reference (internal/external/mimo)")
        
        // Message Configuration
        .def("set_num_bits", &Transmitter_API::set_num_bits,
             py::arg("bits"),
             "Set number of bits per message block")
        
        .def("set_interval", &Transmitter_API::set_message_interval,
             py::arg("ms"),
             "Set interval between packets in ms")
        
        .def("set_continuous", &Transmitter_API::set_continuous,
             py::arg("continuous"),
             "Set continuous transmission mode")
        
        .def("set_repeat_times", &Transmitter_API::set_repeat_time,
             py::arg("times"),
             "Set repeat times")
        
        // Modulation Configuration
        .def("set_mod_scheme", &Transmitter_API::set_mod_scheme,
             py::arg("scheme"),
             "Set modulation scheme (e.g., 'DBPSK', 'QPSK')")
        
        .def("set_preamble", &Transmitter_API::set_preamble,
             py::arg("add_preamble"),
             py::arg("length"),
             py::arg("type"),
             "Configure preamble (add, length, type)")
        
        // Filter Configuration
        .def("set_filter", &Transmitter_API::set_filter,
             py::arg("type"),
             py::arg("symbol_rate"),
             py::arg("num_taps"),
             py::arg("U"),
             py::arg("D"),
             py::arg("roll_off"),
             py::arg("num_threads"),
             "Configure pulse shaping filter")
        
        // Control
        .def("start", &Transmitter_API::start,
             py::arg("message_type"),
             "Start transmitter with specified repeat count")
        
        .def("stop", &Transmitter_API::stop,
             "Stop transmitter")
        
        // Data
        .def("send_message", &Transmitter_API::send_message,
             py::arg("string message"),
             "Send string message for transmission")
        
        .def("send_bits", &Transmitter_API::send_bits,
             py::arg("bits message"),
             "Send string message for transmission")
        
        // Status
        .def("get_status", &Transmitter_API::get_status,
             "Get current status")
        
        .def("get_config", &Transmitter_API::get_config,
             "Get current configuration");
}