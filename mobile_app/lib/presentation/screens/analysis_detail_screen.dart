import 'dart:async';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/wib_date_time.dart';
import '../../core/network/api_service.dart';
import '../../data/models/analysis_report_model.dart';
import '../widgets/bias_badge.dart';
import '../widgets/confidence_meter.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/ios_glass_card.dart';
import '../widgets/trade_setup_card.dart';
import '../widgets/market_analysis_card.dart';
import '../widgets/news_scenario_sheet.dart';
import '../widgets/modern_toast.dart';

class AnalysisDetailScreen extends StatefulWidget {
  const AnalysisDetailScreen({super.key});

  @override
  State<AnalysisDetailScreen> createState() => _AnalysisDetailScreenState();
}

class _AnalysisDetailScreenState extends State<AnalysisDetailScreen> {
  final ApiService _api = ApiService();
  AnalysisReportModel? _report;
  bool _isLoading = true;
  bool _isRefreshing = false;
  String? _error;
  Timer? _analysisAutoSyncTimer;

  @override
  void initState() {
    super.initState();
    _loadReport();
    // 25-second background auto-sync to capture newly synthesized AI insights
    _analysisAutoSyncTimer = Timer.periodic(const Duration(seconds: 25), (_) {
      _loadReport(silent: true);
    });
  }

  @override
  void dispose() {
    _analysisAutoSyncTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadReport({bool silent = false}) async {
    if (!silent && _report == null) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    }
    try {
      final data = await _api.getLatestAnalysis(symbol: 'XAUUSD');
      if (mounted) {
        setState(() {
          _report = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted && _report == null) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _triggerFreshSynthesis() async {
    setState(() {
      _isRefreshing = true;
    });
    try {
      final updated = await _api.triggerFreshAnalysis(symbol: 'XAUUSD');
      setState(() {
        _report = updated;
      });
      if (mounted) {
        ModernToast.showSuccess(
          context,
          'Sintesis 3 pilar data fundamental, geopolitik & teknikal selesai.',
          title: 'Sintesis AI Berhasil',
        );
      }
    } catch (e) {
      if (mounted) {
        ModernToast.showError(
          context,
          'Gagal membuat sintesis: $e',
          title: 'Gagal Sintesis',
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isRefreshing = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: _isLoading
          ? const Center(child: CupertinoActivityIndicator(radius: 14, color: AppColors.primary))
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(CupertinoIcons.exclamationmark_circle, color: AppColors.bearish, size: 36),
                      const SizedBox(height: 8),
                      Text('Gagal memuat: $_error', style: const TextStyle(color: AppColors.textMuted)),
                      const SizedBox(height: 12),
                      CupertinoButton.filled(onPressed: _loadReport, child: const Text('Coba Lagi')),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadReport,
                  color: AppColors.primary,
                  backgroundColor: const Color(0xFF1C1C1E),
                  edgeOffset: 80,
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
                    padding: const EdgeInsets.fromLTRB(16, 75, 16, 100),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Section Header
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                const Text(
                                  'LAPORAN SINTESIS AI',
                                  style: TextStyle(
                                    color: AppColors.textMuted,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 0.8,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Container(
                                  width: 6,
                                  height: 6,
                                  decoration: BoxDecoration(
                                    color: AppColors.bullish,
                                    shape: BoxShape.circle,
                                    boxShadow: [
                                      BoxShadow(
                                        color: AppColors.bullish.withValues(alpha: 0.6),
                                        blurRadius: 4,
                                        spreadRadius: 1,
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 4),
                                const Text(
                                  'LIVE',
                                  style: TextStyle(
                                    color: AppColors.bullish,
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 0.4,
                                  ),
                                ),
                              ],
                            ),
                            GestureDetector(
                              onTap: _isRefreshing ? null : _triggerFreshSynthesis,
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppColors.primary.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(14),
                                ),
                                child: Row(
                                  children: [
                                    if (_isRefreshing) ...[
                                      const CupertinoActivityIndicator(radius: 6, color: AppColors.primary),
                                      const SizedBox(width: 4),
                                    ] else ...[
                                      const Icon(CupertinoIcons.arrow_2_circlepath, color: AppColors.primary, size: 12),
                                      const SizedBox(width: 4),
                                    ],
                                    const Text(
                                      'Sintesis Ulang',
                                      style: TextStyle(color: AppColors.primary, fontSize: 11, fontWeight: FontWeight.w700),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),

                        // 1. Header Glass Card: Bias + Confidence + Timestamp
                        IosGlassCard(
                          borderRadius: 24,
                          padding: const EdgeInsets.all(18),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  Row(
                                    children: [
                                      BiasBadge(bias: _report!.bias, isLarge: true),
                                      const SizedBox(width: 10),
                                      Text(
                                        _report!.symbol,
                                        style: const TextStyle(color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.w800),
                                      ),
                                    ],
                                  ),
                                  Text(
                                    _report!.createdAt.formatWibShort(),
                                    style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.center,
                                children: [
                                  ConfidenceMeter(score: _report!.confidenceScore, size: 90),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Text(
                                      _report!.summary,
                                      style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, height: 1.45),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Hasil Setup Trading (Entry, SL, TP1, TP2)
                        if (_report!.tradeSetup != null && _report!.tradeSetup!.entryPrice > 0) ...[
                          TradeSetupCard(
                            setup: _report!.tradeSetup!,
                          ),
                          const SizedBox(height: 16),
                        ],

                        // Panduan Scalping & Analisis Pasar Dinamis
                        MarketAnalysisCard(
                          bias: _report!.bias,
                          confidenceScore: _report!.confidenceScore,
                          trendDirection: _report!.bias,
                          supportLevels: _report!.keyLevels.support,
                          resistanceLevels: _report!.keyLevels.resistance,
                          summary: _report!.summary,
                          technicalRationale: _report!.technicalNotes ?? _report!.tradeSetup?.technicalRationale,
                        ),
                        const SizedBox(height: 16),

                        // Action Card: Matriks Skenario Pre-News (9 Langkah)
                        IosGlassCard(
                          borderRadius: 20,
                          padding: const EdgeInsets.all(16),
                          borderColor: AppColors.primary.withValues(alpha: 0.4),
                          onTap: () async {
                            try {
                              final scenario = await _api.getNewsIntelligence(symbol: 'XAUUSD');
                              if (context.mounted) {
                                NewsScenarioSheet.show(context, scenario);
                              }
                            } catch (e) {
                              if (context.mounted) {
                                ModernToast.showError(context, 'Gagal memuat skenario: $e');
                              }
                            }
                          },
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: AppColors.primary.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: const Icon(CupertinoIcons.sparkles, color: AppColors.primary, size: 20),
                              ),
                              const SizedBox(width: 14),
                              const Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'MATRIKS SKENARIO NEWS (9 LANGKAH)',
                                      style: TextStyle(
                                        color: AppColors.primary,
                                        fontSize: 12,
                                        fontWeight: FontWeight.w800,
                                        letterSpacing: 0.5,
                                      ),
                                    ),
                                    SizedBox(height: 3),
                                    Text(
                                      'Skenario Kuat/Sesuai/Lemah, Rezim Suku Bunga & Jalur Transmisi',
                                      style: TextStyle(color: AppColors.textMuted, fontSize: 11),
                                    ),
                                  ],
                                ),
                              ),
                              const Icon(CupertinoIcons.chevron_right, color: AppColors.primary, size: 14),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // 2. Pillars Breakdown Card
                        IosGlassCard(
                          borderRadius: 22,
                          padding: const EdgeInsets.all(18),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'RANGKUMAN 3 PILAR DATA',
                                style: TextStyle(color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.6),
                              ),
                              const SizedBox(height: 14),

                              _buildPillarItem(
                                CupertinoIcons.calendar,
                                'Pilar 1: Analisis Fundamental',
                                _report!.fundamentalNotes ?? 'Tidak ada data fundamental spesifik.',
                                AppColors.primary,
                              ),
                              const Divider(height: 22, color: AppColors.borderSubtle),

                              _buildPillarItem(
                                CupertinoIcons.globe,
                                'Pilar 2: Sentimen Geopolitik',
                                _report!.geopoliticalNotes ?? 'Tidak ada isu geopolitik mayor yang berdampak langsung.',
                                AppColors.secondary,
                              ),
                              const Divider(height: 22, color: AppColors.borderSubtle),

                              _buildPillarItem(
                                CupertinoIcons.chart_bar_alt_fill,
                                'Pilar 3: Konfirmasi Teknikal',
                                _report!.technicalNotes ?? 'Grafik harga menunjukkan pola konsolidasi.',
                                AppColors.bullish,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // 3. Key Levels Card
                        IosGlassCard(
                          borderRadius: 20,
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'LEVEL HARGA KRUSIAL (KEY LEVELS)',
                                style: TextStyle(color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5),
                              ),
                              const SizedBox(height: 14),
                              Row(
                                children: [
                                  Expanded(
                                    child: Container(
                                      padding: const EdgeInsets.all(12),
                                      decoration: BoxDecoration(
                                        color: const Color(0x351F2636),
                                        borderRadius: BorderRadius.circular(12),
                                        border: Border.all(color: AppColors.supportLine.withValues(alpha: 0.3)),
                                      ),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const Text(
                                            'Area Support',
                                            style: TextStyle(color: AppColors.supportLine, fontSize: 11, fontWeight: FontWeight.w700),
                                          ),
                                          const SizedBox(height: 6),
                                          ...(_report!.keyLevels.support.map((s) => Text(
                                                '\$${s.toStringAsFixed(2)}',
                                                style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontFamily: 'monospace', fontWeight: FontWeight.w700),
                                              ))),
                                        ],
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Container(
                                      padding: const EdgeInsets.all(12),
                                      decoration: BoxDecoration(
                                        color: const Color(0x351F2636),
                                        borderRadius: BorderRadius.circular(12),
                                        border: Border.all(color: AppColors.resistanceLine.withValues(alpha: 0.3)),
                                      ),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const Text(
                                            'Area Resistance',
                                            style: TextStyle(color: AppColors.resistanceLine, fontSize: 11, fontWeight: FontWeight.w700),
                                          ),
                                          const SizedBox(height: 6),
                                          ...(_report!.keyLevels.resistance.map((r) => Text(
                                                '\$${r.toStringAsFixed(2)}',
                                                style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontFamily: 'monospace', fontWeight: FontWeight.w700),
                                              ))),
                                        ],
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // 4. Risk Factors List (Faktor Risiko Pembatal Bias)
                        IosGlassCard(
                          borderRadius: 20,
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Row(
                                children: [
                                  Icon(CupertinoIcons.exclamationmark_triangle_fill, color: AppColors.impactHigh, size: 16),
                                  SizedBox(width: 8),
                                  Text(
                                    'FAKTOR RISIKO PEMBATAL BIAS',
                                    style: TextStyle(color: AppColors.impactHigh, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              ...(_report!.riskFactors.map((rf) => Padding(
                                    padding: const EdgeInsets.only(bottom: 8),
                                    child: Row(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        const Text('• ', style: TextStyle(color: AppColors.impactHigh, fontWeight: FontWeight.bold)),
                                        Expanded(
                                          child: Text(
                                            rf,
                                            style: const TextStyle(color: AppColors.textPrimary, fontSize: 12.5, height: 1.35),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ))),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // 5. Traceable Sources (Transparansi Data)
                        IosGlassCard(
                          borderRadius: 20,
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Row(
                                children: [
                                  Icon(CupertinoIcons.checkmark_seal_fill, color: AppColors.primary, size: 16),
                                  SizedBox(width: 8),
                                  Text(
                                    'TRANSPARANSI DATA (TRACEABLE SOURCES)',
                                    style: TextStyle(color: AppColors.primary, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              const Text(
                                'Kesimpulan di atas didasarkan secara terverifikasi pada data berikut:',
                                style: TextStyle(color: AppColors.textMuted, fontSize: 11),
                              ),
                              const SizedBox(height: 10),
                              ...(_report!.sources.map((src) => Padding(
                                    padding: const EdgeInsets.only(bottom: 6),
                                    child: Row(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        const Icon(CupertinoIcons.check_mark_circled_solid, color: AppColors.bullish, size: 14),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            src,
                                            style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ))),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),

                        // 6. Mandatory Legal Disclaimer
                        DisclaimerBanner(customText: _report!.disclaimer),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildPillarItem(IconData icon, String title, String description, Color accent) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: accent.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: accent, size: 18),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(color: accent, fontSize: 12.5, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(
                description,
                style: const TextStyle(color: AppColors.textPrimary, fontSize: 12.5, height: 1.35),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
