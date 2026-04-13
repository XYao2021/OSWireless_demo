#ifndef TAPS_HPP
#define TAPS_HPP
#include <vector>
#include <complex>
#include <cmath>
#include <iostream>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// ============================================================================
// ROOT RAISED COSINE FILTER DESIGN
// ============================================================================

template<typename T>
std::vector<std::complex<T>> design_rrc_taps(
    double sample_rate,     // Output sample rate (Hz)
    double symbol_rate,     // Symbol rate (Hz)
    double alpha,           // Roll-off factor (0 to 1)
    int num_taps)           // Number of filter taps (should be odd)
{
    std::cout << "[RRC DESIGN] ================================" << std::endl;
    std::cout << "[RRC DESIGN] Root Raised Cosine Filter Design" << std::endl;
    std::cout << "[RRC DESIGN] ================================" << std::endl;
    std::cout << "[RRC DESIGN] Sample rate: " << sample_rate / 1e6 << " MHz" << std::endl;
    std::cout << "[RRC DESIGN] Symbol rate: " << symbol_rate / 1e6 << " MHz" << std::endl;
    std::cout << "[RRC DESIGN] Roll-off (alpha): " << alpha << std::endl;
    std::cout << "[RRC DESIGN] Number of taps: " << num_taps << std::endl;

    // Validate inputs
    if (sample_rate <= 0 || symbol_rate <= 0) {
        std::cerr << "[RRC DESIGN] ERROR: Invalid sample rate or symbol rate!" << std::endl;
        return std::vector<std::complex<T>>();
    }
    
    if (alpha < 0 || alpha > 1) {
        std::cerr << "[RRC DESIGN] ERROR: Alpha must be between 0 and 1!" << std::endl;
        return std::vector<std::complex<T>>();
    }
    
    if (num_taps % 2 == 0) {
        std::cout << "[RRC DESIGN] WARNING: num_taps should be odd, incrementing to " 
                  << (num_taps + 1) << std::endl;
        num_taps++;
    }

    // Calculate samples per symbol
    double sps = sample_rate / symbol_rate;
    std::cout << "[RRC DESIGN] Samples per symbol: " << sps << std::endl;

    // Calculate filter span in symbols
    double span_symbols = (num_taps - 1) / (2.0 * sps);
    std::cout << "[RRC DESIGN] Filter span: " << span_symbols << " symbols" << std::endl;

    // Generate RRC taps
    std::vector<std::complex<T>> taps(num_taps);
    int center = num_taps / 2;
    
    for (int i = 0; i < num_taps; i++) {
        // Calculate time in symbol periods
        double t = (i - center) / sps;
        
        double h;
        
        // Special case 1: t = 0 (center tap)
        if (std::abs(t) < 1e-10) {
            h = (1.0 - alpha + 4.0 * alpha / M_PI);
            std::cout << "[RRC DESIGN] THE PEAK value before energy normalization: " << h << std::endl;
        }
        // Special case 2: t = ±1/(4*alpha) (avoid division by zero)
        else if (std::abs(std::abs(4.0 * alpha * t) - 1.0) < 1e-10) {
            double val = alpha / std::sqrt(2.0) * 
                        ((1.0 + 2.0 / M_PI) * std::sin(M_PI / (4.0 * alpha)) +
                         (1.0 - 2.0 / M_PI) * std::cos(M_PI / (4.0 * alpha)));
            h = val;
        }
        // General case
        else {
            double numerator = std::sin(M_PI * t * (1.0 - alpha)) + 
                              4.0 * alpha * t * std::cos(M_PI * t * (1.0 + alpha));
            double denominator = M_PI * t * (1.0 - std::pow(4.0 * alpha * t, 2));
            h = numerator / denominator;
        }
        
        taps[i] = std::complex<T>(static_cast<T>(h), 0.0);
    }

    // Normalize to unit energy (sum of squared magnitudes = 1)
    double energy = 0.0;
    for (const auto& tap : taps) {
        energy += std::norm(tap);  // |tap|^2
    }
    
    double norm_factor = 1.0 / std::sqrt(energy);
    std::cout << "[RRC DESIGN] Normalization factor: " << norm_factor << std::endl;
    
    for (auto& tap : taps) {
        tap *= static_cast<T>(norm_factor);
    }

    // Verify the design
    std::cout << "[RRC DESIGN] ================================" << std::endl;
    std::cout << "[RRC DESIGN] Verification:" << std::endl;
    std::cout << "[RRC DESIGN] ================================" << std::endl;
    
    // Check center tap
    std::cout << "[RRC DESIGN] Center tap [" << center << "]: " 
              << taps[center].real() << std::endl;
    
    // Check edge taps
    std::cout << "[RRC DESIGN] First tap [0]: " << taps[0].real() << std::endl;
    std::cout << "[RRC DESIGN] Last tap [" << (num_taps-1) << "]: " 
              << taps[num_taps-1].real() << std::endl;
    
    // Verify energy
    double final_energy = 0.0;
    for (const auto& tap : taps) {
        final_energy += std::norm(tap);
    }
    std::cout << "[RRC DESIGN] Final energy: " << final_energy 
              << " (should be 1.0)" << std::endl;
    
    // Check symmetry
    bool is_symmetric = true;
    double max_asymmetry = 0.0;
    for (int i = 0; i < num_taps / 2; i++) {
        double diff = std::abs(taps[i].real() - taps[num_taps - 1 - i].real());
        max_asymmetry = std::max(max_asymmetry, diff);
        if (diff > 1e-6) {
            is_symmetric = false;
        }
    }
    std::cout << "[RRC DESIGN] Symmetric: " << (is_symmetric ? "YES" : "NO") << std::endl;
    if (!is_symmetric) {
        std::cout << "[RRC DESIGN] Max asymmetry: " << max_asymmetry << std::endl;
    }
    
    // Show first few taps for debugging
    std::cout << "[RRC DESIGN] First 10 taps:" << std::endl;
    for (int i = 0; i < std::min(10, num_taps); i++) {
        std::cout << "  tap[" << i << "] = " << taps[i].real() << std::endl;
    }
    
    std::cout << "[RRC DESIGN] ✓ Design complete!" << std::endl;
    std::cout << std::endl;

    return taps;
}

// ============================================================================
// RAISED COSINE FILTER DESIGN (for reference)
// ============================================================================

template<typename T>
std::vector<std::complex<T>> design_rc_taps(
    double sample_rate,
    double symbol_rate,
    double alpha,
    int num_taps)
{
    std::cout << "[RC DESIGN] Raised Cosine Filter Design" << std::endl;
    std::cout << "[RC DESIGN] Sample rate: " << sample_rate / 1e6 << " MHz" << std::endl;
    std::cout << "[RC DESIGN] Symbol rate: " << symbol_rate / 1e6 << " MHz" << std::endl;
    std::cout << "[RC DESIGN] Roll-off (α): " << alpha << std::endl;

    if (num_taps % 2 == 0) num_taps++;

    double sps = sample_rate / symbol_rate;
    std::vector<std::complex<T>> taps(num_taps);
    int center = num_taps / 2;

    for (int i = 0; i < num_taps; i++) {
        double t = (i - center) / sps;
        double h;

        if (std::abs(t) < 1e-10) {
            h = 1.0;
        } else if (std::abs(std::abs(2.0 * alpha * t) - 1.0) < 1e-10) {
            h = (M_PI / 4.0) * std::sin(M_PI * t) / (M_PI * t);
        } else {
            h = std::sin(M_PI * t) / (M_PI * t) * 
                std::cos(M_PI * alpha * t) / (1.0 - std::pow(2.0 * alpha * t, 2));
        }

        taps[i] = std::complex<T>(static_cast<T>(h), 0.0);
    }

    // Normalize
    double energy = 0.0;
    for (const auto& tap : taps) {
        energy += std::norm(tap);
    }
    double norm_factor = 1.0 / std::sqrt(energy);
    for (auto& tap : taps) {
        tap *= static_cast<T>(norm_factor);
    }

    std::cout << "[RC DESIGN] ✓ Design complete!" << std::endl;
    return taps;
}

void rrc_pulse(std::complex<float>* h, int len, int U, int D, float beta)
{
    // float beta = float(U - D)/D; //roffoff factor
    h[len] = 1.0-beta+4.0*beta/M_PI;
    float scale = std::norm(h[len]);
    for (int n=1; n<=len; n++) {
        if (n == U/beta/4.0) {
            h[len+n] = beta/sqrt(2.0)*((1.0+2.0/M_PI)*sin(M_PI/4.0/beta)+(1.0-2.0/M_PI)*cos(M_PI/4.0/beta));
        } else {
            h[len+n] = (sin(n*M_PI*(1.0-beta)/U) + 4.0*n*beta/U*cos(n*M_PI*(1.0+beta)/U))*U/n/M_PI/(1.0-16.0*n*n*beta*beta/U/U);
        }
        h[len-n] = h[len+n];
        scale += 2.0*std::norm(h[len+n]);
    }
    scale = sqrt(scale);
    for (int n=0; n<2*len+1; n++) {
        h[n] /=  scale;
    }
}

#endif