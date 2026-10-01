import 'dart:async';
import 'dart:math';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/network/api_service.dart';
import '../../core/utils/wib_date_time.dart';
import '../../data/models/dashboard_summary_model.dart';
import '../widgets/bias_badge.dart';
import '../widgets/confidence_meter.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/ios_glass_card.dart';
import '../../data/models/news_article_model.dart';
import '../widgets/news_detail_sheet.dart';
import '../widgets/trade_setup_card.dart';
import '../widgets/market_analysis_card.dart';
import '../widgets/news_scenario_sheet.dart';
import '../widgets/modern_toast.dart';

class DashboardScreen extends StatefulWidget {
  final Function(int)? onNavigateTab;

  const DashboardScreen({super.key, this.onNavigateTab});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _api = ApiService();
  DashboardSummaryModel? _summary;
  bool _isLoading = true;
  bool _isSynthesizing = false;
  bool _isLiveSyncing = false;
  String? _error;
  Timer? _liveTickerTimer;
  Timer? _dashboardAutoSyncTimer;
  Timer? _clockTimer;
  DateTime _currentWibTime = DateTime.now();
  Color _priceFlashColor = Colors.transparent;
  bool _isSilentlyPolling = false;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
    // Live ticking WIB clock
    _clockTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) {
        setState(() {
          _currentWibTime = DateTime.now();
        });
      }
    });
    // 1. Continuous genuine market tick poll from FOREX.com every 700ms (High-frequency sub-second)
    _liveTickerTimer = Timer.periodic(const Duration(milliseconds: 700), (_) {
      _pollLivePriceSilently();
    });
    // 2. Periodic background silent auto-sync of full AI bias & headlines every 20s
    _dashboardAutoSyncTimer = Timer.periodic(const Duration(seconds: 20), (_) {
      _loadDashboardData(silent: true);
    });
  }

  @override
  void dispose() {
    _clockTimer?.cancel();
    _liveTickerTimer?.cancel();
    _dashboardAutoSyncTimer?.cancel();
    super.dispose();
  }

  Future<void> _pollLivePriceSilently() async {
    if (_isSilentlyPolling || _summary == null) return;
    _isSilentlyPolling = true;
    try {
      final tick = await _api.getLivePriceTick(symbol: 'XAUUSD');
      final double? newPrice = (tick['current_price'] as num?)?.toDouble();
      final double? chg = (tick['change_24h'] as num?)?.toDouble();
      final double? pct = (tick['change_pct_24h'] as num?)?.toDouble();
      final double? h = (tick['high'] as num?)?.toDouble();
      final double? l = (tick['low'] as num?)?.toDouble();

      if (newPrice != null && mounted) {
        if (_summary!.currentPrice != newPrice) {
          final isUp = newPrice > _summary!.currentPrice;
          setState(() {
            _priceFlashColor = isUp ? AppColors.bullish.withValues(alpha: 0.3) : AppColors.bearish.withValues(alpha: 0.3);
            _summary = _summary!.copyWith(
              currentPrice: newPrice,
              priceChange24h: chg ?? _summary!.priceChange24h,
              priceChangePct24h: pct ?? _summary!.priceChangePct24h,
              high24h: h != null ? max(_summary!.high24h, h) : _summary!.high24h,
              low24h: l != null ? min(_summary!.low24h, l) : _summary!.low24h,
            );
          });
          Future.delayed(const Duration(milliseconds: 380), () {
            if (mounted) {
              setState(() {
                _priceFlashColor = Colors.transparent;
              });
            }
          });
        }
      }
    } catch (_) {
    } finally {
      _isSilentlyPolling = false;
    }
  }

  Future<void> _loadDashboardData({bool silent = false}) async {
    if (!silent && _summary == null) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    }
    try {
      final data = await _api.getDashboardSummary(symbol: 'XAUUSD');
      if (mounted) {
        setState(() {
          _summary = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted && _summary == null) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _triggerFreshAnalysis() async {
    setState(() {
      _isSynthesizing = true;
    });
    try {
      await _api.triggerFreshAnalysis(symbol: 'XAUUSD');
      await _loadDashboardData();
      if (mounted) {
        ModernToast.showSuccess(
          context,
          'Analisis AI berhasil diperbarui dengan data pasar terbaru!',
          title: 'Analisis AI Terkini',
        );
      }
    } catch (e) {
      if (mounted) {
        ModernToast.showError(
          context,
          'Gagal memperbarui analisis: $e',
          title: 'Gagal Memperbarui',
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSynthesizing = false;
        });
      }
    }
  }

  Future<void> _triggerFullLiveSync() async {
    setState(() {
      _isLiveSyncing = true;
    });
    try {
      final synced = await _api.triggerFullLiveSync(symbol: 'XAUUSD');
      if (mounted) {
        setState(() {
          _summary = synced;
        });
        ModernToast.showInfo(
          context,
          'Harga, kalender ekonomi & berita pasar live berhasil diperbarui.',
          title: 'Sinkronisasi Real-Time Sukses',
        );
      }
    } catch (e) {
      if (mounted) {
        ModernToast.showError(
          context,
          'Gagal sinkronisasi data live: $e',
          title: 'Sinkronisasi Gagal',
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLiveSyncing = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CupertinoActivityIndicator(radius: 14, color: AppColors.primary),
            SizedBox(height: 16),
            Text('Mengumpulkan data pasar...', style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(CupertinoIcons.wifi_slash, color: AppColors.bearish, size: 48),
              const SizedBox(height: 12),
              const Text(
                'Tidak Dapat Terhubung ke Backend',
                style: TextStyle(color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                'Pastikan backend FastAPI sudah berjalan di ${ApiService.baseUrl}',
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
              ),
              const SizedBox(height: 20),
              CupertinoButton.filled(
                onPressed: _loadDashboardData,
                child: const Text('Coba Lagi', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ),
      );
    }

    final data = _summary!;
    final isPriceUp = data.priceChange24h >= 0;
    final mediaQuery = MediaQuery.of(context);
    const double topPadding = 14.0;
    final bottomPadding = mediaQuery.padding.bottom + 64 + 24;

    return RefreshIndicator(
      onRefresh: _loadDashboardData,
      color: AppColors.primary,
      backgroundColor: const Color(0xFF1C1C1E),
      edgeOffset: 0,
      child: SingleChildScrollView(
        physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
        padding: EdgeInsets.fromLTRB(16, topPadding, 16, bottomPadding),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // iOS Section Header with Live WIB Time Indicator
            Padding(
              padding: const EdgeInsets.only(left: 4, right: 4, bottom: 10),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Expanded(
                    child: Text(
                      'RINGKASAN PASAR',
                      style: TextStyle(
                        color: AppColors.textMuted,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.8,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                    decoration: BoxDecoration(
                      color: const Color(0x351F2636),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppColors.borderSubtle),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(CupertinoIcons.clock_fill, color: AppColors.primary, size: 11),
                        const SizedBox(width: 4),
                        Text(
                          _currentWibTime.formatWibTime(withSeconds: true),
                          style: const TextStyle(
                            color: AppColors.primary,
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            fontFamily: 'monospace',
                            letterSpacing: 0.3,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // 1. Hero Instrument & Live Price Glass Card
            IosGlassCard(
              borderRadius: 24,
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: AppColors.neutral.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Icon(CupertinoIcons.circle_grid_hex_fill, color: AppColors.neutral, size: 22),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    data.symbol,
                                    style: const TextStyle(
                                      color: AppColors.textPrimary,
                                      fontSize: 18,
                                      fontWeight: FontWeight.w800,
                                      letterSpacing: 0.6,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  Text(
                                    data.instrumentName,
                                    style: const TextStyle(color: AppColors.textMuted, fontSize: 11.5),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      // Live Real-Time Indicator & Manual Sync Button
                      Row(
                        children: [
                          GestureDetector(
                            onTap: _isLiveSyncing ? null : _triggerFullLiveSync,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppColors.bullish.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: AppColors.bullish.withValues(alpha: 0.4), width: 0.8),
                              ),
                              child: Row(
                                children: [
                                  if (_isLiveSyncing) ...[
                                    const CupertinoActivityIndicator(radius: 6, color: AppColors.bullish),
                                    const SizedBox(width: 5),
                                  ] else ...[
                                    Container(
                                      width: 7,
                                      height: 7,
                                      decoration: const BoxDecoration(
                                        color: AppColors.bullish,
                                        shape: BoxShape.circle,
                                        boxShadow: [
                                          BoxShadow(color: AppColors.bullish, blurRadius: 6, spreadRadius: 1),
                                        ],
                                      ),
                                    ),
                                    const SizedBox(width: 6),
                                  ],
                                  const Text(
                                    'LIVE REAL-TIME',
                                    style: TextStyle(color: AppColors.bullish, fontSize: 9.5, fontWeight: FontWeight.w800, letterSpacing: 0.5),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Current Price & 24h Change with Flash Animation
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            AnimatedContainer(
                              duration: const Duration(milliseconds: 300),
                              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                              decoration: BoxDecoration(
                                color: _priceFlashColor,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: FittedBox(
                                fit: BoxFit.scaleDown,
                                alignment: Alignment.centerLeft,
                                child: Text(
                                  '\$${data.currentPrice.toStringAsFixed(2)}',
                                  style: const TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 34,
                                    fontWeight: FontWeight.w800,
                                    fontFamily: 'monospace',
                                    letterSpacing: -1.0,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 2),
                            Row(
                              children: [
                                Icon(
                                  isPriceUp ? CupertinoIcons.arrow_up_right : CupertinoIcons.arrow_down_right,
                                  color: isPriceUp ? AppColors.bullish : AppColors.bearish,
                                  size: 14,
                                ),
                                const SizedBox(width: 4),
                                Expanded(
                                  child: Text(
                                    '${isPriceUp ? '+' : ''}\$${data.priceChange24h.toStringAsFixed(2)} (${isPriceUp ? '+' : ''}${data.priceChangePct24h.toStringAsFixed(2)}%)',
                                    style: TextStyle(
                                      color: isPriceUp ? AppColors.bullish : AppColors.bearish,
                                      fontSize: 12.5,
                                      fontWeight: FontWeight.w700,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 10),
                      // 24h High/Low Stats (Apple Inset Style)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                        decoration: BoxDecoration(
                          color: const Color(0x351F2636),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              'H: \$${data.high24h.toStringAsFixed(1)}',
                              style: const TextStyle(color: AppColors.textSecondary, fontSize: 11, fontFamily: 'monospace', fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'L:  \$${data.low24h.toStringAsFixed(1)}',
                              style: const TextStyle(color: AppColors.textMuted, fontSize: 11, fontFamily: 'monospace'),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 2. Core AI Market Bias Glass Card
            IosGlassCard(
              borderRadius: 24,
              padding: const EdgeInsets.all(18),
              glowColor: data.bias == 'BULLISH'
                  ? AppColors.bullish
                  : (data.bias == 'BEARISH' ? AppColors.bearish : AppColors.neutral),
              borderColor: (data.bias == 'BULLISH'
                      ? AppColors.bullish
                      : (data.bias == 'BEARISH' ? AppColors.bearish : AppColors.neutral))
                  .withValues(alpha: 0.5),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Row(
                        children: [
                          Icon(CupertinoIcons.sparkles, color: AppColors.primary, size: 18),
                          SizedBox(width: 8),
                          Text(
                            'SINTESIS BIAS PASAR (3 PILAR)',
                            style: TextStyle(
                              color: AppColors.primary,
                              fontSize: 11.5,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.8,
                            ),
                          ),
                        ],
                      ),
                      GestureDetector(
                        onTap: _isSynthesizing ? null : _triggerFreshAnalysis,
                        child: Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: _isSynthesizing
                              ? const SizedBox(
                                  width: 14,
                                  height: 14,
                                  child: CupertinoActivityIndicator(radius: 7, color: AppColors.primary),
                                )
                              : const Icon(CupertinoIcons.arrow_2_circlepath, color: AppColors.primary, size: 15),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Bias Badge + Confidence Meter Row
                  Row(
                    children: [
                      ConfidenceMeter(score: data.confidenceScore, size: 95),
                      const SizedBox(width: 18),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            BiasBadge(bias: data.bias, isLarge: true),
                            const SizedBox(height: 10),
                            Text(
                              data.biasSummary,
                              style: const TextStyle(
                                color: AppColors.textPrimary,
                                fontSize: 13,
                                height: 1.4,
                                letterSpacing: -0.2,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Divider(height: 1, color: AppColors.borderSubtle),
                  const SizedBox(height: 12),

                  // Link to Detail Tab
                  InkWell(
                    onTap: () => widget.onNavigateTab?.call(4),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Lihat rincian bukti pilar, risiko & key levels',
                          style: TextStyle(
                            color: AppColors.primary,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Icon(CupertinoIcons.chevron_right, color: AppColors.primary, size: 13),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 2.5 Hasil Setup Trading (Entry, SL, TP1, TP2)
            if (data.tradeSetup != null && data.tradeSetup!.entryPrice > 0) ...[
              _buildSectionHeader('HASIL SETUP TRADING (DARI CHART)', 2),
              TradeSetupCard(
                setup: data.tradeSetup!,
                onViewChart: () => widget.onNavigateTab?.call(2),
              ),
              const SizedBox(height: 16),
            ],

            // 2.6 Analisis Pasar & Panduan Scalping / Intraday
            _buildSectionHeader('ANALISIS PASAR & PANDUAN TRADING', 4),
            MarketAnalysisCard(
              bias: data.bias,
              confidenceScore: data.confidenceScore,
              trendDirection: (data.technicalSnapshot['trend'] as String?) ?? 'BULLISH',
              rsi: (data.technicalSnapshot['rsi'] as num?)?.toDouble(),
              rsiCondition: data.technicalSnapshot['rsi_status'] as String?,
              summary: data.biasSummary,
              technicalRationale: data.tradeSetup?.technicalRationale,
              upcomingEventTitle: data.upcomingHighImpactEvent?['title'] as String?,
              upcomingEventTime: data.upcomingHighImpactEvent?['scheduled_at'] != null
                  ? DateTime.tryParse(data.upcomingHighImpactEvent!['scheduled_at'].toString())?.formatWibWithDay()
                  : null,
            ),
            const SizedBox(height: 16),

            // 3. Modul Fundamental Radar Card
            if (data.upcomingHighImpactEvent != null) ...[
              _buildSectionHeader('RADAR HIGH-IMPACT (24-48 JAM)', 1),
              IosGlassCard(
                borderRadius: 20,
                padding: const EdgeInsets.all(16),
                onTap: () => widget.onNavigateTab?.call(1),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppColors.impactHigh.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Icon(CupertinoIcons.exclamationmark_triangle_fill, color: AppColors.impactHigh, size: 20),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                data.upcomingHighImpactEvent!['currency'] ?? 'USD',
                                style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.w700, fontSize: 11),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                                decoration: BoxDecoration(
                                  color: AppColors.impactHigh.withValues(alpha: 0.2),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: const Text(
                                  'HIGH IMPACT',
                                  style: TextStyle(color: AppColors.impactHigh, fontSize: 8.5, fontWeight: FontWeight.w800),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            data.upcomingHighImpactEvent!['title'] ?? '',
                            style: const TextStyle(color: AppColors.textPrimary, fontSize: 13.5, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Forecast: ${data.upcomingHighImpactEvent!['forecast'] ?? '-'}  •  Sebelumnya: ${data.upcomingHighImpactEvent!['previous'] ?? '-'}',
                            style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                          ),
                          if (data.upcomingHighImpactEvent!['scheduled_at'] != null) ...[
                            const SizedBox(height: 3),
                            Text(
                              'Jadwal: ${DateTime.tryParse(data.upcomingHighImpactEvent!['scheduled_at'] ?? '')?.formatWibWithDay() ?? '-'}',
                              style: const TextStyle(color: AppColors.primary, fontSize: 10.5, fontWeight: FontWeight.w600),
                            ),
                          ],
                          const SizedBox(height: 8),
                          GestureDetector(
                            onTap: () async {
                              try {
                                final scenario = await _api.getNewsIntelligence(
                                  symbol: 'XAUUSD',
                                  eventTitle: data.upcomingHighImpactEvent!['title'],
                                );
                                if (context.mounted) {
                                  NewsScenarioSheet.show(context, scenario);
                                }
                              } catch (e) {
                                if (context.mounted) {
                                  ModernToast.showError(context, 'Gagal memuat skenario: $e');
                                }
                              }
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                              decoration: BoxDecoration(
                                color: AppColors.primary.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: AppColors.primary.withValues(alpha: 0.35)),
                              ),
                              child: const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(CupertinoIcons.sparkles, color: AppColors.primary, size: 12),
                                  SizedBox(width: 5),
                                  Text(
                                    'Buka Skenario Pre-News (9 Langkah)',
                                    style: TextStyle(
                                      color: AppColors.primary,
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Icon(CupertinoIcons.chevron_right, color: AppColors.textTertiary, size: 14),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // 4. Modul Geopolitik Snapshot
            if (data.latestGeopoliticalHeadline != null) ...[
              _buildSectionHeader('SENTIMEN GEOPOLITIK TERKINI', 2),
              IosGlassCard(
                borderRadius: 20,
                padding: const EdgeInsets.all(16),
                onTap: () {
                  final h = data.latestGeopoliticalHeadline!;
                  final article = NewsArticleModel(
                    id: 0,
                    symbol: 'XAUUSD',
                    title: h['title'] ?? '',
                    source: h['source'] ?? 'Global News',
                    url: h['url'],
                    summary: h['summary'] ?? h['title'],
                    sentimentLabel: h['sentiment_label'] ?? 'NEUTRAL',
                    sentimentScore: (h['sentiment_score'] as num?)?.toDouble() ?? 0.0,
                    publishedAt: DateTime.tryParse(h['published_at'] ?? '') ?? DateTime.now(),
                  );
                  NewsDetailSheet.show(context, article);
                },
                child: Builder(
                  builder: (context) {
                    final h = data.latestGeopoliticalHeadline!;
                    final sentimentLabel = h['sentiment_label'] ?? 'NEUTRAL';
                    final Color sentimentColor = sentimentLabel == 'POSITIVE'
                        ? AppColors.bullish
                        : (sentimentLabel == 'NEGATIVE' ? AppColors.bearish : AppColors.neutral);

                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Row(
                                children: [
                                  Flexible(
                                    child: Text(
                                      h['source'] ?? 'Global News',
                                      style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  if (h['published_at'] != null) ...[
                                    const Text(' • ', style: TextStyle(color: AppColors.textMuted, fontSize: 10)),
                                    Text(
                                      DateTime.tryParse(h['published_at'] ?? '')?.formatWibShort() ?? '',
                                      style: const TextStyle(color: AppColors.textMuted, fontSize: 10),
                                    ),
                                  ],
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                              decoration: BoxDecoration(
                                color: sentimentColor.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: sentimentColor.withValues(alpha: 0.35), width: 0.8),
                              ),
                              child: Text(
                                'Sentimen: $sentimentLabel',
                                style: TextStyle(
                                  color: sentimentColor,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(
                          h['title'] ?? '',
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            height: 1.35,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            Text(
                              'Buka & Baca Penjelasan',
                              style: TextStyle(
                                color: AppColors.primary.withValues(alpha: 0.85),
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            const SizedBox(width: 3),
                            const Icon(CupertinoIcons.chevron_right, color: AppColors.primary, size: 11),
                          ],
                        ),
                      ],
                    );
                  },
                ),
              ),
              const SizedBox(height: 16),
            ],

            // 5. Technical Quick Snapshot
            _buildSectionHeader('STRUKTUR TEKNIKAL', 3),
            IosGlassCard(
              borderRadius: 20,
              padding: const EdgeInsets.all(16),
              onTap: () => widget.onNavigateTab?.call(3),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Row(
                          children: [
                            const Icon(CupertinoIcons.chart_bar_alt_fill, color: AppColors.primary, size: 18),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'Trend: ${data.technicalSnapshot['trend'] ?? 'NEUTRAL'}',
                                style: TextStyle(
                                  color: data.technicalSnapshot['trend'] == 'BULLISH'
                                      ? AppColors.bullish
                                      : (data.technicalSnapshot['trend'] == 'BEARISH' ? AppColors.bearish : AppColors.neutral),
                                  fontWeight: FontWeight.w700,
                                  fontSize: 13,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'RSI: ${data.technicalSnapshot['rsi'] ?? '-'} (${data.technicalSnapshot['rsi_status'] ?? '-'})',
                        style: const TextStyle(color: AppColors.textSecondary, fontSize: 12, fontFamily: 'monospace'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    data.technicalSnapshot['summary'] ?? '',
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 11.5, height: 1.35),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 6. Mandatory Legal Disclaimer
            DisclaimerBanner(customText: data.disclaimer),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, int tabIndex) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8, right: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Text(
              title,
              style: const TextStyle(
                color: AppColors.textMuted,
                fontSize: 11.5,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.6,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: () => widget.onNavigateTab?.call(tabIndex),
            child: const Text(
              'Buka Modul',
              style: TextStyle(color: AppColors.primary, fontSize: 11.5, fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}
