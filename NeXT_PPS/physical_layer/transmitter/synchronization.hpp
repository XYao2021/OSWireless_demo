#include <iostream>
#include <complex>
#include <vector>
#include <cmath>
#include <queue>
#include <mutex>
#include <algorithm>
#include <atomic>

#include "FIFO.hpp"

// -------------------------------------------------------- ACQ Symbol Synchronization Class ------------------------------------------------ //
class ACQSynchronizer {

private:
    std::vector<std::complex<float>> SignatureSequence;
    int samples_per_symbol;  // sps * U / D -> e.g. 1.25 * 4 / 1 = 5 
    float ACQThreshold;
    int HeaderPayloadLength;
    bool UseLastSymbolReference;

    size_t TotalCorrelations;

    float ComputeCorrelation(const std::vector<std::complex<float>>& input_vector, int tau){
        std::complex<float> sum(0.0f, 0.0f);

        for (size_t n = 0; n < SignatureSequence.size(); n++){
            int index = tau + n * samples_per_symbol;
            if (index >= input_vector.size()){
                break;
            }
            sum += std::conj(SignatureSequence[n]) * input_vector[index];
        }
        return std::abs(sum);
    }

    float EstimateNoiseFloor(const std::vector<std::complex<float>>& input_vector, int PeakTau, int PeakWidth){
        std::vector<float> NoiseCorrelation;
        int SampleStep = samples_per_symbol * 10;  // Sampling every 10 symbol
        int ExclusionZone = PeakWidth * 2;

        for (int tau = 0; tau <= input_vector.size() - PeakWidth; tau += SampleStep){
            if (std::abs(tau - PeakTau) < ExclusionZone){
                continue;
            }
            float correlation = ComputeCorrelation(input_vector, tau);
            NoiseCorrelation.push_back(correlation);

            if (NoiseCorrelation.size() >= 20) break;
        }

        if (NoiseCorrelation.empty()){return 0.1f;}
        std::sort(NoiseCorrelation.begin(), NoiseCorrelation.end());
        return NoiseCorrelation[NoiseCorrelation.size() / 2];
    }

    std::vector<std::complex<float>> ExtractDecisionStats(const std::vector<std::complex<float>>& input_vector, int tau_opt){
        std::vector<std::complex<float>> Decisions;

        int StartOffset = UseLastSymbolReference ? 30 : 31;
        // int StartOffset = 30;
        std::cout << "[ACQ DECISION] The Sign of UseLastSymbolReference: " << UseLastSymbolReference << std::endl;
        int StartIdex = tau_opt + StartOffset * samples_per_symbol;

        std::cout << "[ACQ] Extracting decision statistics..." << std::endl;
        std::cout << "[ACQ]   Start index: " << StartIdex 
             << " (tau* + " << StartOffset << "T)" << std::endl;
            
        Decisions.reserve(HeaderPayloadLength);
        for (int i = 0; i < HeaderPayloadLength; i++){
            int index = StartIdex + i * samples_per_symbol;
            if (index >= input_vector.size()){
                std::cout << "[ACQ WARNING] Ran out of samples at symbol " << i << std::endl;
                break;
            }
            Decisions.push_back(input_vector[index]);
        }
        return Decisions;
    }

public:
    struct ACQResult {
        bool PacketDetected;
        int tau_opt;
        float MaxCorrelation;
        float CorrelationSNR;
        std::vector<std::complex<float>> DecisionStats;
        int NumCorrelationComputed;
        double ProcessingTime_ms;

        int ThresholdCorssingTau;
        int SearchRangeSize;
    };

    ACQSynchronizer(const std::vector<std::complex<float>>& SigSequence,
                    int sps, float threshold, int HeaderPayload_len = 1016, bool UseLast = false)
        : SignatureSequence(SigSequence),
          samples_per_symbol(sps),
          ACQThreshold(threshold),
          HeaderPayloadLength(HeaderPayload_len),
          UseLastSymbolReference(UseLast),
          TotalCorrelations(0)
    {
        std::cout << "========================================" << std::endl;
        std::cout << "ACQ SYNCHRONIZER INITIALIZED" << std::endl;
        std::cout << "========================================" << std::endl;
        std::cout << "[ACQ] Signature length: " << SignatureSequence.size() << " symbols" << std::endl;
        std::cout << "[ACQ] Samples per symbol: " << samples_per_symbol << std::endl;
        std::cout << "[ACQ] Threshold: " << ACQThreshold << std::endl;
        std::cout << "[ACQ] Header+Payload: " << HeaderPayloadLength << " symbols" << std::endl;
        std::cout << "[ACQ] Use last symbol as ref: " << (UseLastSymbolReference ? "YES" : "NO") << std::endl;
        std::cout << "========================================" << std::endl;
    }

    ACQResult PerformACQOptimized(const std::vector<std::complex<float>>& input_vector){
        auto StartTime = std::chrono::high_resolution_clock::now();

        ACQResult result;
        result.PacketDetected = false;
        result.tau_opt = -1;
        result.MaxCorrelation = 0.0f;
        result.NumCorrelationComputed = 0;
        result.ThresholdCorssingTau = -1;

        int SigLengthSamples = SignatureSequence.size() * samples_per_symbol;
        // int PacketLenSamples = (SignatureSequence.size() + HeaderPayloadLength) * samples_per_symbol;
        int PacketLenSamples = HeaderPayloadLength * samples_per_symbol;
        int MaxTau = input_vector.size() - PacketLenSamples;
        // int MaxTau = input_vector.size() - SigLengthSamples;

        if (MaxTau < 0) {
            std::cout << "[ACQ ERROR] MF output too short for packet detection!" << std::endl;
            std::cout << "  MF output size: " << input_vector.size() << " samples" << std::endl;
            std::cout << "  Required: " << PacketLenSamples << " samples" << std::endl;
            return result;
        }

        std::cout << "\n[ACQ] Starting optimized search..." << std::endl;
        std::cout << "[ACQ] Search range: tau = 0 to " << MaxTau << " samples" << std::endl;

        // Phase 1: Coarse Search -> Check every T samples to find the rough boundaries
        int CoarseStep = samples_per_symbol;
        int CoarseSearches = 0;
        
        std::cout << "[ACQ] Phase 1: Coarse search (stride = " << CoarseStep << " samples)..." << std::endl;
        for (int tau = 0; tau <= MaxTau; tau += CoarseStep){
            float correlation = ComputeCorrelation(input_vector, tau);
            result.NumCorrelationComputed++;
            CoarseSearches++;

            if (correlation > result.MaxCorrelation){
                result.MaxCorrelation = correlation;
                result.tau_opt = tau;
            }

            if (correlation > ACQThreshold && result.ThresholdCorssingTau < 0){
                result.ThresholdCorssingTau = tau;
                std::cout << "[ACQ] Threshold crossed at tau = " << tau 
                     << " (correlation = " << correlation << ")" << std::endl;
                break;  // Exit coarse search early
            }
        }
        std::cout << "[ACQ] Coarse search complete: " << CoarseSearches << " correlations" << std::endl;

        // 2. Phase 2: Fine Search (around threshold crossing)
        if (result.ThresholdCorssingTau >= 0){
            int FineSearchStart = std::max(0, result.ThresholdCorssingTau - samples_per_symbol);
            int FineSearchEnd = std::min(MaxTau, result.ThresholdCorssingTau + samples_per_symbol);

            std::cout << "[ACQ] Phase 2: Fine search from tau = " << FineSearchStart 
                 << " to " << FineSearchEnd << "..." << std::endl;

            int FineSearches = 0;
            for (int tau = FineSearchStart; tau <= FineSearchEnd; tau++){
                float correlation = ComputeCorrelation(input_vector, tau);
                result.NumCorrelationComputed++;
                FineSearches++;

                // Update maximum
                if (correlation > result.MaxCorrelation){
                    result.MaxCorrelation = correlation;
                    result.tau_opt = tau;
                }
            }

            std::cout << "[ACQ] Fine search complete: " << FineSearches << " correlations" << std::endl;
            result.SearchRangeSize = FineSearchEnd - FineSearchStart + 1;
        } else {
            // No threshold crossing - use result from coarse search
            std::cout << "[ACQ] No threshold crossing detected in coarse search!" << std::endl;
            result.SearchRangeSize = MaxTau / CoarseStep;
        }

        // Phase 3: Decision and Statistic Extraction
        float NoiseFloor = EstimateNoiseFloor(input_vector, result.tau_opt, SigLengthSamples);
        result.CorrelationSNR = 20.0f * std::log10(result.MaxCorrelation / (NoiseFloor + 1e-10));

        // Check if packet detected
        result.PacketDetected = (result.MaxCorrelation > ACQThreshold);

        // if (result.PacketDetected){
        //     std::cout << "\n[ACQ] ✓ PACKET DETECTED!" << std::endl;
        //     std::cout << "[ACQ]   tau* = " << result.tau_opt << " samples" << std::endl;
        //     std::cout << "[ACQ]   Peak correlation = " << result.MaxCorrelation << std::endl;
        //     std::cout << "[ACQ]   Threshold = " << ACQThreshold << std::endl;
        //     std::cout << "[ACQ]   Margin = " << (result.MaxCorrelation - ACQThreshold) << std::endl;
        //     std::cout << "[ACQ]   Correlation SNR = " << result.CorrelationSNR << " dB" << std::endl;

        //     // Extract decision statistics for demodulation
        //     result.DecisionStats = ExtractDecisionStats(input_vector, result.tau_opt);
        //     std::cout << "[ACQ]   Decision stats extracted: " << result.DecisionStats.size() << " symbols" << std::endl;

        // } else {
        //     std::cout << "\n[ACQ] ✗ NO PACKET DETECTED" << std::endl;
        //     std::cout << "[ACQ]   Max correlation = " << result.MaxCorrelation << std::endl;
        //     std::cout << "[ACQ]   tau_max = " << result.tau_opt << " samples" << std::endl;
        //     std::cout << "[ACQ]   Threshold = " << ACQThreshold << std::endl;
        //     std::cout << "[ACQ]   Below threshold by = " << (ACQThreshold - result.MaxCorrelation) << std::endl;
        // }

        // Performance metrics
        auto EndTime = std::chrono::high_resolution_clock::now();
        result.ProcessingTime_ms = std::chrono::duration<double, std::milli>(EndTime - StartTime).count();
        
        // std::cout << "[ACQ] Performance:" << std::endl;
        // std::cout << "[ACQ]   Correlations computed: " << result.NumCorrelationComputed << std::endl;
        // std::cout << "[ACQ]   Processing time: " << result.ProcessingTime_ms << " ms" << std::endl;
        // std::cout << "[ACQ]   Speedup vs brute force: " 
        //      << (float)(MaxTau + 1) / result.NumCorrelationComputed << "x" << std::endl;
        // std::cout << "========================================" << std::endl;
        
        TotalCorrelations += result.NumCorrelationComputed;
        return result;
    }

    // Samples-based ACQ searching
    ACQResult SamplesACQPerformance(const std::vector<std::complex<float>>& input_vector){
        auto StartTime = std::chrono::high_resolution_clock::now();

        ACQResult result;
        result.PacketDetected = false;
        result.tau_opt = -1;
        result.MaxCorrelation = 0.0f;
        result.NumCorrelationComputed = 0;

        // int PackLengthSamples = (SignatureSequence.size() + HeaderPayloadLength) * samples_per_symbol;
        int PackLengthSamples = HeaderPayloadLength * samples_per_symbol;
        int MaxTau = input_vector.size() - PackLengthSamples;

        if (MaxTau < 0){
            std::cout << "[ACQ ERROR] Filtered vector is too short!" << std::endl;
            return result;
        }

        std::cout << "\n[ACQ] Starting brute force search (every sample)..." << std::endl;
        std::cout << "[ACQ] Search range: tau = 0 to " << MaxTau << " samples" << std::endl;

        for (int tau = 0; tau <= MaxTau; tau++){
            float correlation = ComputeCorrelation(input_vector, tau);
            result.NumCorrelationComputed++;

            if (correlation > result.MaxCorrelation){
                result.MaxCorrelation = correlation;
                result.tau_opt = tau;
            }

            // Progress indicator for long searches
            if (tau % 1000 == 0 && tau > 0) {
                std::cout << "[ACQ] Progress: " << tau << "/" << MaxTau << " (" << (100.0*tau/MaxTau) << "%)" << std::endl;
            }
        }

        result.PacketDetected = (result.MaxCorrelation > ACQThreshold);

        // if (result.PacketDetected){
        //     result.DecisionStats = ExtractDecisionStats(input_vector, result.tau_opt);
        // } else {
        //     std::cout << "[ACQ] Fail to find the peak, the current max peak is " << result.MaxCorrelation << std::endl;
        // }
        if (result.PacketDetected){
            std::cout << "\n[ACQ] ✓ PACKET DETECTED!" << std::endl;
            std::cout << "[ACQ]   tau* = " << result.tau_opt << " samples" << std::endl;
            std::cout << "[ACQ]   Peak correlation = " << result.MaxCorrelation << std::endl;
            std::cout << "[ACQ]   Threshold = " << ACQThreshold << std::endl;
            std::cout << "[ACQ]   Margin = " << (result.MaxCorrelation - ACQThreshold) << std::endl;
            std::cout << "[ACQ]   Correlation SNR = " << result.CorrelationSNR << " dB" << std::endl;

            // Extract decision statistics for demodulation
            result.DecisionStats = ExtractDecisionStats(input_vector, result.tau_opt);
            std::cout << "[ACQ]   Decision stats extracted: " << result.DecisionStats.size() << " symbols" << std::endl;

        } else {
            std::cout << "\n[ACQ] ✗ NO PACKET DETECTED" << std::endl;
            std::cout << "[ACQ]   Max correlation = " << result.MaxCorrelation << std::endl;
            std::cout << "[ACQ]   Threshold = " << ACQThreshold << std::endl;
            std::cout << "[ACQ]   Below threshold by = " << (ACQThreshold - result.MaxCorrelation) << std::endl;
        }

        auto EndTime = std::chrono::high_resolution_clock::now();
        result.ProcessingTime_ms = std::chrono::duration<double, std::milli>(EndTime - StartTime).count();

        std::cout << "[ACQ] Brute force complete:" << std::endl;
        std::cout << "[ACQ]   Correlations: " << result.NumCorrelationComputed << std::endl;
        std::cout << "[ACQ]   Time: " << result.ProcessingTime_ms << " ms" << std::endl;
        
        return result;
    }
    
};

void TimeSync_thread(MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>>& detected_fifo,
                     MutexFIFO<std::pair<size_t, std::vector<std::complex<float>>>>& synced_fifo,
                     std::vector<std::complex<float>>& preamble_sequence,
                     size_t U, size_t D, int sps, std::atomic<bool>& stop_sign,
                     int Data_length, float threshold);
