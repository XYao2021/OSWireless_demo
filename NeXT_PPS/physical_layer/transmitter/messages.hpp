#include <atomic>
#include <string>
#include <vector>
#include <complex>
#include <map>
#include <fstream>
#include <bitset>
#include <algorithm>
#include <cstdint>  // for uint8_t
#include "FIFO.hpp"

using namespace std;
// Message functions
std::vector<uint8_t> string_to_bits(const std::string& message);
std::vector<uint8_t> bits_to_bytes(const std::vector<uint8_t>& bits);
std::string bits_to_string(const std::vector<uint8_t> bits, size_t num_bytes);
std::vector<uint8_t> generate_message_block(std::string& message, size_t block_idx, size_t target_bits);
std::string decode_message_block(const std::vector<uint8_t>& bits);

void message_generator_thread(MutexFIFO<std::vector<uint8_t>>& fifo,
                              const std::vector<std::string>& messages,
                              std::atomic<bool>& stop_flag,
                              size_t target_bits,
                              bool continuous,
                              size_t sleep_time);

// Preamble functions
// ============================================================================
// MODULATION TYPES
// ============================================================================
enum class PreambleModType {
    BPSK,           // Binary Phase Shift Keying: 0→+1, 1→-1
    DBPSK,          // Differential BPSK: bit determines phase change
    QPSK,           // Quadrature PSK: 2 bits per symbol
    DQPSK           // Differential QPSK
};

// ============================================================================
// M-SEQUENCE GENERATOR WITH FLEXIBLE MODULATION
// ============================================================================
class MSequenceGenerator {
private:
    int length;
    int lfsr_bits;
    vector<int> taps;
    
    // Constellation points
    map<PreambleModType, string> modTypeNames = {
        {PreambleModType::BPSK, "BPSK"},
        {PreambleModType::DBPSK, "DBPSK"},
        {PreambleModType::QPSK, "QPSK"},
        {PreambleModType::DQPSK, "DQPSK"}
    };
    
public:
    // Constructor
    MSequenceGenerator(int m = 5) {
        lfsr_bits = m;
        length = (1 << m) - 1;  // 2^m - 1
        taps = get_polynomial_taps(m);
        
        cout << "========================================" << endl;
        cout << "M-SEQUENCE GENERATOR INITIALIZED" << endl;
        cout << "========================================" << endl;
        cout << "[M-SEQ] Length: " << length << " bits" << endl;
        cout << "[M-SEQ] LFSR bits: " << lfsr_bits << endl;
        cout << "[M-SEQ] Taps: ";
        for (int tap : taps) cout << tap << " ";
        cout << endl;
        cout << "========================================" << endl;
    }
    
    // ========================================================================
    // PRIMITIVE POLYNOMIAL TAPS (CORRECTED)
    // ========================================================================
    vector<int> get_polynomial_taps(int m) {
        switch (m) {
            case 3: return {3, 1};
            case 4: return {4, 1};
            case 5: return {5, 3};          // FIXED
            case 6: return {6, 1};
            case 7: return {7, 1};
            case 8: return {8, 6, 5, 1};    // FIXED
            case 9: return {9, 4};
            case 10: return {10, 3};
            case 11: return {11, 2};
            case 12: return {12, 6, 4, 1};
            case 13: return {13, 4, 3, 1};
            default: return {5, 3};         // FIXED default
        }
    }
    
    // ========================================================================
    // GENERATE BINARY M-SEQUENCE (COMPLETELY REWRITTEN - GALOIS LFSR)
    // ========================================================================
    vector<int> generateBinary(uint32_t seed = 0) {
        vector<int> sequence;
        sequence.reserve(length);
        
        // Default seed: Must be non-zero, preferably with multiple 1s
        if (seed == 0) {
            seed = 0b10111;  // Seed with good distribution: 10111
        }
        
        uint32_t lfsr = seed & ((1 << lfsr_bits) - 1);
        uint32_t initial_state = lfsr;
        
        // cout << "\n[M-SEQ] Generating binary sequence (Galois LFSR)..." << endl;
        // cout << "[M-SEQ] Initial seed: " << bitset<5>(lfsr) << " (decimal: " << lfsr << ")" << endl;
        // cout << "[M-SEQ] Taps for feedback: ";
        // for (int tap : taps) cout << tap << " ";
        // cout << endl;
        
        vector<int> debug_bits;
        int iterations = 0;
        
        do {
            // Output LSB
            int output_bit = lfsr & 1;
            sequence.push_back(output_bit);
            
            if (iterations < 15) {
                debug_bits.push_back(output_bit);
            }
            
            // Galois LFSR operation
            // If LSB is 1, XOR with tap mask after shifting
            unsigned int lsb = lfsr & 1;
            lfsr >>= 1;
            
            if (lsb) {
                // XOR with tap positions
                // For x^5 + x^3 + 1, taps are at positions 5 and 3
                // This means we XOR at bit positions 4 and 2 (0-indexed)
                for (int tap : taps) {
                    int bit_pos = tap - 1;
                    lfsr ^= (1 << bit_pos);
                }
            }
            
            // if (iterations < 5) {
            //     cout << "[M-SEQ] Iter " << iterations << ": output=" << output_bit 
            //          << ", LSB=" << lsb
            //          << ", LFSR after=" << bitset<5>(lfsr) << endl;
            // }
            
            iterations++;
            
            // Safety check: stop if we've done too many iterations
            if (iterations > length + 10) {
                cout << "[M-SEQ] ERROR: Too many iterations! Breaking." << endl;
                break;
            }
            
        } while (lfsr != initial_state && iterations < length);
        
        // cout << "[M-SEQ] Generated " << iterations << " bits" << endl;
        // cout << "[M-SEQ] First 15 bits: ";
        // for (int bit : debug_bits) cout << bit;
        // cout << endl;
        
        // Compare with known good
        vector<int> known_good = {
            1,0,0,0,0,1,1,0,0,1,0,1,1,1,1,1,0,1,0,1,0,0,0,1,1,1,1,0,0,1,1
        };
        
        if (sequence.size() >= 15) {
            cout << "[M-SEQ] Expected:  ";
            for (int i = 0; i < 15; i++) cout << known_good[i];
            cout << endl;
        }
        
        // Pad or trim to exact length
        sequence.resize(length);
        
        // Statistics
        int zeros = 0, ones = 0;
        for (int bit : sequence) {
            if (bit == 0) zeros++;
            else ones++;
        }
        
        cout << "[M-SEQ] Sequence statistics:" << endl;
        cout << "[M-SEQ]   Length: " << sequence.size() << " bits" << endl;
        cout << "[M-SEQ]   Zeros: " << zeros << ", Ones: " << ones << endl;
        cout << "[M-SEQ]   Balance: " << abs(ones - zeros) << " (should be 1)" << endl;
        
        if (abs(ones - zeros) == 1) {
            cout << "[M-SEQ] ✓ Sequence balance correct!" << endl;
        }
        
        return sequence;
    }
    
    // ========================================================================
    // GET KNOWN GOOD 31-BIT M-SEQUENCE (for comparison)
    // ========================================================================
    vector<int> getKnownGood31BitSequence() {
        // This is a verified 31-bit m-sequence from x^5 + x^3 + 1
        // Starting with seed 00001
        vector<int> seq = {
            1,0,0,0,0,1,1,0,0,1,0,1,1,1,1,1,0,1,0,1,0,0,0,1,1,1,1,0,0,1,1
        };
        
        cout << "[M-SEQ] Using known good 31-bit reference sequence" << endl;
        
        // Print it
        cout << "[M-SEQ] Reference: ";
        for (int bit : seq) cout << bit;
        cout << endl;
        
        return seq;
    }
    
    // ========================================================================
    // MODULATE WITH FLEXIBLE CONSTELLATION
    // ========================================================================
    vector<complex<float>> modulate(PreambleModType modType, int seed = 0b00001) {
        // vector<int> binary = generateBinary(seed);
        vector<int> binary = getKnownGood31BitSequence();

        vector<complex<float>> modulated;
        
        cout << "\n[M-SEQ] Modulating with " << modTypeNames[modType] << "..." << endl;
        
        switch (modType) {
            case PreambleModType::BPSK:
                modulated = modulateBPSK(binary);
                break;
            case PreambleModType::DBPSK:
                modulated = modulateDBPSK(binary);
                break;
            case PreambleModType::QPSK:
                modulated = modulateQPSK(binary);
                break;
            case PreambleModType::DQPSK:
                modulated = modulateDQPSK(binary);
                break;
            default:
                modulated = modulateBPSK(binary);
        }
        
        cout << "[M-SEQ] Modulated sequence: " << modulated.size() << " symbols" << endl;
        printFirstSymbols(modulated);
        
        return modulated;
    }
    
private:
    // ========================================================================
    // BPSK MODULATION: 0 → +1, 1 → -1
    // ========================================================================
    vector<complex<float>> modulateBPSK(const vector<int>& bits) {
        vector<complex<float>> symbols;
        symbols.reserve(bits.size());
        
        for (int bit : bits) {
            complex<float> symbol = (bit == 0) ? complex<float>(1.0f, 0.0f) 
                                                : complex<float>(-1.0f, 0.0f);
            symbols.push_back(symbol);
        }
        
        return symbols;
    }
    
    // ========================================================================
    // DBPSK MODULATION: Map directly to BPSK constellation
    // ========================================================================
    // For preamble/synchronization, use DIRECT BPSK mapping of m-sequence
    // The m-sequence itself provides the good autocorrelation properties
    // Differential encoding is done later during data payload modulation
    vector<complex<float>> modulateDBPSK(const vector<int>& bits) {
        vector<complex<float>> symbols;
        symbols.reserve(bits.size());
        
        cout << "[DBPSK] Using direct BPSK mapping for m-sequence preamble" << endl;
        cout << "[DBPSK] (Differential encoding applied to data payload separately)" << endl;
        
        // Direct BPSK mapping: 0→+1, 1→-1
        // This preserves m-sequence autocorrelation properties
        for (size_t i = 0; i < bits.size(); i++) {
            complex<float> symbol = (bits[i] == 0) ? complex<float>(1.0f, 0.0f)
                                                    : complex<float>(-1.0f, 0.0f);
            symbols.push_back(symbol);
            
            // Debug first few symbols
            if (i < 10) {
                cout << "[DBPSK] bit[" << i << "]=" << bits[i] 
                     << " → symbol=" << symbol << endl;
            }
        }
        
        return symbols;
    }
    
    // ========================================================================
    // ALTERNATIVE: True DBPSK with differential pre-coding
    // ========================================================================
    // This applies differential encoding to the m-sequence bits first,
    // then maps to constellation. Use this if you want true differential preamble.
    vector<complex<float>> modulateDBPSK_DifferentialPrecoded(const vector<int>& bits) {
        vector<complex<float>> symbols;
        symbols.reserve(bits.size());
        
        // Differential pre-coding: convert data bits to phase transitions
        vector<int> precoded_bits;
        precoded_bits.reserve(bits.size());
        
        int prev_bit = 0;  // Reference bit
        for (int bit : bits) {
            // XOR for differential encoding
            int current_bit = prev_bit ^ bit;
            precoded_bits.push_back(current_bit);
            prev_bit = current_bit;
        }
        
        // Now map pre-coded bits to BPSK
        for (size_t i = 0; i < precoded_bits.size(); i++) {
            complex<float> symbol = (precoded_bits[i] == 0) ? complex<float>(1.0f, 0.0f)
                                                             : complex<float>(-1.0f, 0.0f);
            symbols.push_back(symbol);
            
            if (i < 10) {
                cout << "[DBPSK-PRECODED] bit[" << i << "]=" << bits[i] 
                     << " → precoded=" << precoded_bits[i]
                     << " → symbol=" << symbol << endl;
            }
        }
        
        return symbols;
    }
    
    // ========================================================================
    // QPSK MODULATION: 2 bits → 1 symbol (4 constellation points)
    // ========================================================================
    vector<complex<float>> modulateQPSK(const vector<int>& bits) {
        vector<complex<float>> symbols;
        
        // QPSK constellation: (±1±j)/sqrt(2) for unit energy
        const float scale = 1.0f / sqrt(2.0f);
        map<int, complex<float>> qpsk_map = {
            {0b00, complex<float>(scale, scale)},      // 00 → +1+j
            {0b01, complex<float>(-scale, scale)},     // 01 → -1+j
            {0b10, complex<float>(scale, -scale)},     // 10 → +1-j
            {0b11, complex<float>(-scale, -scale)}     // 11 → -1-j
        };
        
        // Group bits into pairs
        for (size_t i = 0; i + 1 < bits.size(); i += 2) {
            int dibits = (bits[i] << 1) | bits[i + 1];
            symbols.push_back(qpsk_map[dibits]);
        }
        
        // Handle odd bit (if any)
        if (bits.size() % 2 != 0) {
            int last_bit = bits.back();
            symbols.push_back(qpsk_map[last_bit << 1]);
        }
        
        cout << "[QPSK] " << bits.size() << " bits → " << symbols.size() << " symbols" << endl;
        
        return symbols;
    }
    
    // ========================================================================
    // DQPSK MODULATION: Differential QPSK
    // ========================================================================
    vector<complex<float>> modulateDQPSK(const vector<int>& bits) {
        vector<complex<float>> symbols;
        
        // Phase changes for DQPSK
        const float scale = 1.0f / sqrt(2.0f);
        map<int, complex<float>> phase_changes = {
            {0b00, complex<float>(1.0f, 0.0f)},        // 00 → 0°
            {0b01, complex<float>(0.0f, 1.0f)},        // 01 → 90°
            {0b10, complex<float>(-1.0f, 0.0f)},       // 10 → 180°
            {0b11, complex<float>(0.0f, -1.0f)}        // 11 → 270°
        };
        
        // Start with reference
        complex<float> prev_symbol(scale, scale);
        
        for (size_t i = 0; i + 1 < bits.size(); i += 2) {
            int dibits = (bits[i] << 1) | bits[i + 1];
            complex<float> current_symbol = prev_symbol * phase_changes[dibits];
            symbols.push_back(current_symbol);
            prev_symbol = current_symbol;
        }
        
        if (bits.size() % 2 != 0) {
            int last_bit = bits.back();
            symbols.push_back(prev_symbol * phase_changes[last_bit << 1]);
        }
        
        cout << "[DQPSK] " << bits.size() << " bits → " << symbols.size() << " symbols" << endl;
        
        return symbols;
    }
    
public:
    // ========================================================================
    // COMPUTE AND PLOT FULL AUTOCORRELATION
    // ========================================================================
    void computeFullAutocorrelation(const vector<complex<float>>& seq, const string& filename) {
        int N = seq.size();
        
        cout << "\n[M-SEQ] Computing full autocorrelation function..." << endl;
        cout << "[M-SEQ] Sequence length: " << N << " symbols" << endl;
        
        vector<float> autocorr_mag;
        vector<int> lags;
        
        // Compute autocorrelation for all possible lags (0 to N-1)
        for (int lag = 0; lag < N; lag++) {
            complex<float> corr(0, 0);
            
            // Circular autocorrelation: R[lag] = sum(conj(x[n]) * x[(n+lag) mod N])
            for (int n = 0; n < N; n++) {
                corr += conj(seq[n]) * seq[(n + lag) % N];
            }
            
            float corr_mag = abs(corr);
            autocorr_mag.push_back(corr_mag);
            lags.push_back(lag);
        }
        
        // Find peak and sidelobes
        float peak = *max_element(autocorr_mag.begin(), autocorr_mag.end());
        int peak_lag = distance(autocorr_mag.begin(), 
                               max_element(autocorr_mag.begin(), autocorr_mag.end()));
        
        // Find max sidelobe (excluding peak at lag 0)
        float max_sidelobe = 0;
        int max_sidelobe_lag = 0;
        for (int lag = 1; lag < N; lag++) {
            if (autocorr_mag[lag] > max_sidelobe) {
                max_sidelobe = autocorr_mag[lag];
                max_sidelobe_lag = lag;
            }
        }
        
        // Calculate statistics
        float avg_sidelobe = 0;
        for (int lag = 1; lag < N; lag++) {
            avg_sidelobe += autocorr_mag[lag];
        }
        avg_sidelobe /= (N - 1);
        
        cout << "\n[AUTOCORR] Results:" << endl;
        cout << "[AUTOCORR]   Peak at lag 0: " << peak << endl;
        cout << "[AUTOCORR]   Max sidelobe at lag " << max_sidelobe_lag << ": " 
             << max_sidelobe << endl;
        cout << "[AUTOCORR]   Avg sidelobe: " << avg_sidelobe << endl;
        cout << "[AUTOCORR]   Peak-to-max-sidelobe: " 
             << 20 * log10(peak / (max_sidelobe + 1e-10)) << " dB" << endl;
        cout << "[AUTOCORR]   Peak-to-avg-sidelobe: " 
             << 20 * log10(peak / (avg_sidelobe + 1e-10)) << " dB" << endl;
        
        // Check if it's a good m-sequence
        float expected_peak = N;
        float expected_sidelobe = 1.0;
        float expected_ratio_dB = 20 * log10(N);
        
        cout << "\n[AUTOCORR] Expected for ideal " << N << "-bit m-sequence:" << endl;
        cout << "[AUTOCORR]   Peak: " << expected_peak << endl;
        cout << "[AUTOCORR]   Sidelobes: ~" << expected_sidelobe << endl;
        cout << "[AUTOCORR]   Ratio: ~" << expected_ratio_dB << " dB" << endl;
        
        if (abs(peak - expected_peak) < 0.1 && max_sidelobe < 2.0) {
            cout << "[AUTOCORR] ✓ Excellent autocorrelation properties!" << endl;
        } else if (abs(peak - expected_peak) < 1.0 && max_sidelobe < 3.0) {
            cout << "[AUTOCORR] ✓ Good autocorrelation properties" << endl;
        } else {
            cout << "[AUTOCORR] ⚠️  Autocorrelation not ideal" << endl;
        }
        
        // Save to file for plotting
        if (!filename.empty()) {
            ofstream file(filename);
            file << "# Lag\tAutocorrelation_Magnitude\tAutocorr_dB\n";
            for (int lag = 0; lag < N; lag++) {
                float corr_dB = 20 * log10(autocorr_mag[lag] / peak);  // Normalized to peak
                file << lag << "\t" << autocorr_mag[lag] << "\t" << corr_dB << "\n";
            }
            file.close();
            cout << "\n[AUTOCORR] Saved to " << filename << endl;
            cout << "[AUTOCORR] Plot with:" << endl;
            cout << "[AUTOCORR]   gnuplot> plot '" << filename << "' using 1:2 with lines" << endl;
            cout << "[AUTOCORR]   or in Python/MATLAB" << endl;
        }
    }
    
    // ========================================================================
    // SIMPLIFIED VERSION (keeping old interface)
    // ========================================================================
    void computeAutocorrelation(const vector<complex<float>>& seq) {
        computeFullAutocorrelation(seq, "debugging/autocorrelation_mseq.txt");
    }
    
    // ========================================================================
    // PRINT HELPERS
    // ========================================================================
    void printFirstSymbols(const vector<complex<float>>& symbols, int count = 10) {
        cout << "[M-SEQ] First " << min(count, (int)symbols.size()) << " symbols: ";
        for (int i = 0; i < min(count, (int)symbols.size()); i++) {
            cout << "(" << symbols[i].real() << "," << symbols[i].imag() << ") ";
        }
        cout << endl;
    }
    
    void printSequence(const vector<int>& seq) {
        cout << "\n[M-SEQ] Binary Sequence:" << endl;
        cout << "[M-SEQ] ";
        for (size_t i = 0; i < seq.size(); i++) {
            cout << seq[i];
            if ((i + 1) % 10 == 0) cout << " ";
        }
        cout << endl;
    }
};

class ZadoffChuGenerator {
private:
    size_t N_;          // Sequence length (MUST be positive!)
    size_t u_;          // Root index
    int m_;             // Cyclic shift (default 0)
    
    // ========================================================================
    // HELPER: Calculate GCD (Greatest Common Divisor)
    // Check if two numbers are coprime: gcd(a, b) = 1
    // ========================================================================
    size_t gcd(size_t a, size_t b) {
        while (b != 0) {
            size_t temp = b;
            b = a % b;
            a = temp;
        }
        return a;
    }
    
    // ========================================================================
    // HELPER: Check if number is prime
    // ========================================================================
    bool is_prime(size_t n) {
        if (n < 2) return false;
        if (n == 2) return true;
        if (n % 2 == 0) return false;
        
        for (size_t i = 3; i * i <= n; i += 2) {
            if (n % i == 0) return false;
        }
        return true;
    }
    
    // ========================================================================
    // HELPER: Find nearest prime number
    // Useful if your desired length isn't prime
    // ========================================================================
    size_t find_nearest_prime(size_t n) {
        // Search upwards first
        for (size_t i = n; i <= n + 1000; i++) {
            if (is_prime(i)) {
                return i;
            }
        }
        // If not found upwards, search downwards
        for (size_t i = n; i >= 2; i--) {
            if (is_prime(i)) {
                return i;
            }
        }
        return 2;  // Fallback
    }
    
public:
    // ========================================================================
    // CONSTRUCTOR
    // ========================================================================
    ZadoffChuGenerator(size_t N = 1024, size_t u = 1, int m = 0)
        : N_(N), u_(u), m_(m) {
        
        // VALIDATION: Check if N is positive and reasonable
        if (N <= 0) {
            std::cerr << "[ERROR] N must be positive! Got N = " << N << std::endl;
            N_ = 1024;  // Default
        }
        
        if (N > 1000000) {
            std::cerr << "[WARNING] N is very large (" << N << "), may cause issues" << std::endl;
        }
        
        // VALIDATION: Check if N is prime
        if (!is_prime(N)) {
            std::cout << "[WARNING] N = " << N << " is not prime." << std::endl;
            std::cout << "          Zadoff-Chu sequences work best with prime N." << std::endl;
            std::cout << "          Nearest primes: ";
            
            // Find nearby primes
            for (size_t i = N; i <= N + 100; i++) {
                if (is_prime(i)) {
                    std::cout << i << " ";
                    break;
                }
            }
            std::cout << std::endl;
        }
        
        // VALIDATION: Check if u and N are coprime
        if (gcd(u, N) != 1) {
            std::cerr << "[ERROR] Root u = " << u << " is NOT coprime to N = " << N << std::endl;
            std::cerr << "        gcd(" << u << ", " << N << ") = " << gcd(u, N) << std::endl;
            std::cerr << "        This will degrade correlation properties!" << std::endl;
            
            // Try to find a valid root
            std::cout << "        Searching for valid root..." << std::endl;
            bool found = false;
            for (size_t new_u = 1; new_u < N; new_u++) {
                if (gcd(new_u, N) == 1) {
                    std::cout << "        Found valid root u = " << new_u << std::endl;
                    u_ = new_u;
                    found = true;
                    break;
                }
            }
            
            if (!found) {
                std::cerr << "        Could not find valid root! Sequence may have poor properties." << std::endl;
            }
        }
        
        std::cout << "[Zadoff-Chu] Initialized: N=" << N_ << ", u=" << u_ 
                  << ", m=" << m_ << std::endl;
    }
    
    // ========================================================================
    // MAIN FUNCTION: Generate Zadoff-Chu sequence
    // ========================================================================
    std::vector<std::complex<float>> generate() {
        std::cout << "[Zadoff-Chu] Generating sequence..." << std::endl;
        
        std::vector<std::complex<float>> sequence(N_);
        
        // Formula: x[n] = exp( -j * π * u * n * (n + m) / N )
        for (size_t n = 0; n < N_; n++) {
            // Calculate exponent: -π * u * n * (n + m) / N
            float numerator = -M_PI * static_cast<float>(u_) 
                            * static_cast<float>(n) 
                            * static_cast<float>(n + m_);
            float denominator = static_cast<float>(N_);
            float angle = numerator / denominator;
            
            // Create complex exponential: cos(angle) + j*sin(angle)
            sequence[n] = std::complex<float>(std::cos(angle), std::sin(angle));
        }
        
        std::cout << "[Zadoff-Chu] Sequence generated: " << N_ << " samples" << std::endl;
        return sequence;
    }
    
    // ========================================================================
    // HELPER: Print sequence properties
    // ========================================================================
    void print_properties(const std::vector<std::complex<float>>& seq) {
        std::cout << "\n[Zadoff-Chu Properties]" << std::endl;
        std::cout << "  Sequence length: " << seq.size() << std::endl;
        std::cout << "  Root (u): " << u_ << std::endl;
        std::cout << "  Cyclic shift (m): " << m_ << std::endl;
        std::cout << "  GCD(u, N): " << gcd(u_, N_) << " (should be 1)" << std::endl;
        std::cout << "  N is prime: " << (is_prime(N_) ? "YES" : "NO") << std::endl;
        
        // Check amplitude (should all be 1.0)
        float min_amp = std::abs(seq[0]);
        float max_amp = std::abs(seq[0]);
        for (const auto& sample : seq) {
            float amp = std::abs(sample);
            min_amp = std::min(min_amp, amp);
            max_amp = std::max(max_amp, amp);
        }
        std::cout << "  Amplitude range: [" << min_amp << ", " << max_amp << "] (should be ~1.0)" << std::endl;
        
        // Check first few samples
        std::cout << "  First 5 samples:" << std::endl;
        for (size_t i = 0; i < std::min(size_t(5), seq.size()); i++) {
            std::cout << "    [" << i << "] = " << seq[i] << std::endl;
        }
    }
    
    // ========================================================================
    // SETTERS
    // ========================================================================
    void set_length(size_t N) {
        if (N <= 0) {
            std::cerr << "[ERROR] N must be positive!" << std::endl;
            return;
        }
        N_ = N;
        std::cout << "[Zadoff-Chu] Length set to: " << N << std::endl;
    }
    
    void set_root(size_t u) {
        if (gcd(u, N_) != 1) {
            std::cerr << "[ERROR] Root " << u << " is not coprime to N=" << N_ << std::endl;
            return;
        }
        u_ = u;
        std::cout << "[Zadoff-Chu] Root set to: " << u << std::endl;
    }
    
    void set_cyclic_shift(int m) {
        m_ = m;
        std::cout << "[Zadoff-Chu] Cyclic shift set to: " << m << std::endl;
    }
    
    // ========================================================================
    // GETTERS
    // ========================================================================
    size_t get_length() const { return N_; }
    size_t get_root() const { return u_; }
    int get_cyclic_shift() const { return m_; }
    
    // ========================================================================
    // Utility: Auto-correlation test (should have sharp peak)
    // ========================================================================
    void test_autocorrelation(const std::vector<std::complex<float>>& seq) {
        std::cout << "\n[Autocorrelation Test]" << std::endl;
        
        // Calculate correlation at lag 0 (should be N)
        std::complex<float> corr_0(0, 0);
        for (size_t i = 0; i < seq.size(); i++) {
            corr_0 += seq[i] * std::conj(seq[i]);
        }
        
        std::cout << "  Correlation at lag 0: " << std::abs(corr_0) 
                  << " (should be " << seq.size() << ")" << std::endl;
        
        // Check correlation at a few other lags
        std::cout << "  Correlation at other lags (should be ~1):" << std::endl;
        for (size_t lag = 1; lag <= 5; lag++) {
            std::complex<float> corr(0, 0);
            for (size_t i = 0; i < seq.size() - lag; i++) {
                corr += seq[i] * std::conj(seq[i + lag]);
            }
            std::cout << "    lag " << lag << ": " << std::abs(corr) << std::endl;
        }
    }
};