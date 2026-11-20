import 'dart:async';
import 'dart:math';
import 'package:flutter/cupertino.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../core/constants/app_colors.dart';
import '../../core/theme/app_theme.dart';
import '../../core/network/api_service.dart';
import '../../core/utils/wib_date_time.dart';
import '../../data/models/dashboard_summary_model.dart';
import '../../data/models/news_article_model.dart';
import '../widgets/bias_badge.dart';
import '../widgets/confidence_meter.dart';
import '../widgets/disclaimer_banner.dart';
import '../widgets/ios_glass_card.dart';
import '../widgets/news_detail_sheet.dart';
import '../widgets/trade_setup_card.dart';
import '../widgets/news_scenario_sheet.dart';
import '../widgets/modern_toast.dart';
import 'analysis_detail_screen.dart';

class DashboardScreen extends StatefulWidget {
  final Function(int)? onNavigateTab;
  final VoidCallback? onOpenSettings;

  const DashboardScreen({super.key, this.onNavigateTab, this.onOpenSettings});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _api = ApiService();
  final NumberFormat _priceFmt = NumberFormat('#,##0.00', 'en_US');
  final NumberFormat _priceCompactFmt = NumberFormat('#,##0.0', 'en_US');

  DashboardSummaryModel? _summary;
  bool _isLoading = true;
  bool _isSynthesizing = false;
  bool _isLiveSyncing = false;
  String? _error;
  Timer? _liveTickerTimer;
  Timer? _dashboardAutoSyncTimer;
  Color _priceFlashColor = Colors.transparent;
  bool _isSilentlyPolling = false;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
    // 1. High-frequency live tick poll every 700ms
    _liveTickerTimer = Timer.periodic(const Duration(milliseconds: 700), (_) {
      _pollLivePriceSilently();
    });
    // 2. Background silent auto-sync of AI bias & headlines every 20s
    _dashboardAutoSyncTimer = Timer.periodic(const Duration(seconds: 20), (_) {
      _loadDashboardData(silent: true);
    });
  }

  @override
  void dispose() {
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
            _priceFlashColor = isUp
                ? AppColors.bullish.withValues(alpha: 0.22)
                : AppColors.bearish.withValues(alpha: 0.22);
            _summary = _summary!.copyWith(
              currentPrice: newPrice,
              priceChange24h: chg ?? _summary!.priceChange24h,
              priceChangePct24h: pct ?? _summary!.priceChangePct24h,
              high24h: h != null ? max(_summary!.high24h, h) : _summary!.high24h,
              low24h: l != null ? min(_summary!.low24h, l) : _summary!.low24h,
            );
          });
          Future.delayed(const Duration(milliseconds: 350), () {
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
          'Analisis 3-Pilar AI diperbarui dengan data pasar terkini.',
          title: 'Sintesis AI Terkini',
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
          'Harga spot, kalender ekonomi & berita global berhasil disinkronkan.',
          title: 'Sinkronisasi Real-Time',
        );
      }
    } catch (e) {
      if (mounted) {
        ModernToast.showError(
          context,
          'Gagal sinkronisasi live: $e',
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

  /// Derives dynamic 3-pillar confidence metrics from live telemetry
  ({int fundamental, int geopolitical, int technical}) _computePillarScores(DashboardSummaryModel data) {
    final base = data.confidenceScore.clamp(40, 95);

    // 1. Fundamental strength
    int funda = base - 2;
    if (data.upcomingHighImpactEvent != null) {
      funda = (base + 4).clamp(45, 96);
    }

    // 2. Geopolitical strength from live news sentiment score
    final rawSent = (data.latestGeopoliticalHeadline?['sentiment_score'] as num?)?.toDouble() ?? 0.35;
    int geopol = (base + (rawSent.abs() * 14).round()).clamp(48, 96);

    // 3. Technical strength from trend alignment & RSI
    final trend = (data.technicalSnapshot['trend'] as String?)?.toUpperCase() ?? 'NEUTRAL';
    final rsi = (data.technicalSnapshot['rsi'] as num?)?.toDouble() ?? 52.0;
    int tech = base - 6;
    if (trend == data.bias.toUpperCase()) {
      tech = (base + 2).clamp(45, 95);
    } else if (trend == 'NEUTRAL') {
      tech = (base - 12).clamp(40, 82);
    }
    if (rsi > 72 || rsi < 28) {
      tech = (tech - 6).clamp(38, 90);
    }

    return (fundamental: funda, geopolitical: geopol, technical: tech);
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CupertinoActivityIndicator(radius: 14, color: AppColors.gold),
            SizedBox(height: 16),
            Text(
              'Memuat data institusional XAU/USD...',
              style: TextStyle(color: AppColors.textMuted, fontSize: 13),
            ),
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
              const Icon(LucideIcons.wifiOff, color: AppColors.bearish, size: 44),
              const SizedBox(height: 14),
              const Text(
                'Tidak Dapat Terhubung ke Engine',
                style: TextStyle(color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 8),
              Text(
                'Server aktif: ${ApiService.baseUrl}',
                textAlign: TextAlign.center,
                style: AppTypography.mono(color: AppColors.textMuted, fontSize: 11.5),
              ),
              const SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CupertinoButton(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 11),
                    color: AppColors.gold,
                    borderRadius: BorderRadius.circular(12),
                    onPressed: _loadDashboardData,
                    child: const Text(
                      'Coba Lagi',
                      style: TextStyle(color: Color(0xFF08090C), fontWeight: FontWeight.w800, fontSize: 13),
                    ),
                  ),
                  if (widget.onOpenSettings != null) ...[
                    const SizedBox(width: 10),
                    CupertinoButton(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 11),
                      color: AppColors.surfaceElevated,
                      borderRadius: BorderRadius.circular(12),
                      onPressed: widget.onOpenSettings,
                      child: const Text(
                        'Server',
                        style: TextStyle(color: AppColors.textSecondary, fontWeight: FontWeight.w700, fontSize: 13),
                      ),
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      );
    }

    final data = _summary!;
    final isPriceUp = data.priceChange24h >= 0;
    final Color priceTrendColor = isPriceUp ? AppColors.bullish : AppColors.bearish;
    final Color biasColor = data.bias.toUpperCase() == 'BULLISH'
        ? AppColors.bullish
        : (data.bias.toUpperCase() == 'BEARISH' ? AppColors.bearish : AppColors.gold);
    final pillars = _computePillarScores(data);

    // Dynamic realistic raw spread readout (0.12 - 0.18 pip range)
    final double estSpread = (data.high24h - data.low24h) > 45 ? 0.18 : 0.15;

    final mediaQuery = MediaQuery.of(context);
    final bottomPadding = mediaQuery.padding.bottom + 76 + 24;

    return RefreshIndicator(
      onRefresh: _loadDashboardData,
      color: AppColors.gold,
      backgroundColor: AppColors.surfaceElevated,
      edgeOffset: 0,
      child: SingleChildScrollView(
        physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
        padding: EdgeInsets.fromLTRB(16, 16, 16, bottomPadding),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ─────────────────────────────────────────────────────────────────
            // 1. HERO PRICE CARD (Clean Obsidian & Gold Bullion)
            // ─────────────────────────────────────────────────────────────────
            IosGlassCard(
              borderRadius: 20,
              padding: const EdgeInsets.all(18),
              borderColor: AppColors.gold.withValues(alpha: 0.18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Top Row: Symbol + Live Sync Pill
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 38,
                            height: 38,
                            decoration: BoxDecoration(
                              color: AppColors.gold.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(11),
                              border: Border.all(color: AppColors.gold.withValues(alpha: 0.28), width: 0.8),
                            ),
                            child: const Icon(
                              LucideIcons.coins,
                              color: AppColors.gold,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'XAU/USD',
                                style: TextStyle(
                                  color: AppColors.textPrimary,
                                  fontSize: 17,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 0.4,
                                ),
                              ),
                              const SizedBox(height: 1),
                              Text(
                                'Gold Spot • ${data.instrumentName}',
                                style: const TextStyle(
                                  color: AppColors.textMuted,
                                  fontSize: 11.5,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: _isLiveSyncing ? null : _triggerFullLiveSync,
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5.5),
                          decoration: BoxDecoration(
                            color: AppColors.bullish.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: AppColors.bullish.withValues(alpha: 0.35), width: 0.8),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              if (_isLiveSyncing) ...[
                                const CupertinoActivityIndicator(radius: 5.5, color: AppColors.bullish),
                                const SizedBox(width: 6),
                              ] else ...[
                                Container(
                                  width: 6.5,
                                  height: 6.5,
                                  decoration: BoxDecoration(
                                    color: AppColors.bullish,
                                    shape: BoxShape.circle,
                                    boxShadow: [
                                      BoxShadow(color: AppColors.bullish.withValues(alpha: 0.8), blurRadius: 6),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 6),
                              ],
                              Text(
                                _isLiveSyncing ? 'SYNCING' : 'LIVE',
                                style: const TextStyle(
                                  color: AppColors.bullish,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 0.6,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),

                  // Hero 34px Tabular Spot Price + Change Badge
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.baseline,
                    textBaseline: TextBaseline.alphabetic,
                    children: [
                      Flexible(
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 280),
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                          decoration: BoxDecoration(
                            color: _priceFlashColor,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: FittedBox(
                            fit: BoxFit.scaleDown,
                            alignment: Alignment.centerLeft,
                            child: Text(
                              '\$${_priceFmt.format(data.currentPrice)}',
                              style: AppTypography.mono(
                                color: AppColors.textPrimary,
                                fontSize: 34,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -1.2,
                              ),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: priceTrendColor.withValues(alpha: 0.14),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              isPriceUp ? LucideIcons.arrowUpRight : LucideIcons.arrowDownRight,
                              color: priceTrendColor,
                              size: 12,
                            ),
                            const SizedBox(width: 3),
                            Text(
                              '${isPriceUp ? '+' : ''}${data.priceChangePct24h.toStringAsFixed(2)}%',
                              style: AppTypography.mono(
                                color: priceTrendColor,
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${isPriceUp ? '+' : ''}\$${data.priceChange24h.toStringAsFixed(2)} sesi 24 jam',
                    style: AppTypography.mono(
                      color: AppColors.textMuted,
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 3-Column Horizontal Metrics Strip (24H High | 24H Low | Spread)
                  Container(
                    padding: const EdgeInsets.symmetric(vertical: 11, horizontal: 12),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceInset,
                      borderRadius: BorderRadius.circular(13),
                      border: Border.all(color: AppColors.border, width: 0.8),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: _buildPriceStatCol(
                            label: '24H HIGH',
                            value: '\$${_priceCompactFmt.format(data.high24h)}',
                            valueColor: AppColors.textPrimary,
                          ),
                        ),
                        Container(width: 0.8, height: 26, color: AppColors.border),
                        Expanded(
                          child: _buildPriceStatCol(
                            label: '24H LOW',
                            value: '\$${_priceCompactFmt.format(data.low24h)}',
                            valueColor: AppColors.textSecondary,
                          ),
                        ),
                        Container(width: 0.8, height: 26, color: AppColors.border),
                        Expanded(
                          child: _buildPriceStatCol(
                            label: 'SPREAD',
                            value: '${estSpread.toStringAsFixed(2)} pip',
                            valueColor: AppColors.cyan,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // ─────────────────────────────────────────────────────────────────
            // 2. CORE AI BIAS ENGINE CARD (Gauge + 3-Pillar Progress Bars)
            // ─────────────────────────────────────────────────────────────────
            IosGlassCard(
              borderRadius: 20,
              padding: const EdgeInsets.all(18),
              glowColor: biasColor,
              borderColor: biasColor.withValues(alpha: 0.25),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header Row
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Row(
                        children: [
                          Icon(LucideIcons.sparkles, color: AppColors.gold, size: 15),
                          SizedBox(width: 7),
                          Text(
                            'CORE AI BIAS ENGINE',
                            style: TextStyle(
                              color: AppColors.gold,
                              fontSize: 11.5,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.8,
                            ),
                          ),
                        ],
                      ),
                      GestureDetector(
                        behavior: HitTestBehavior.opaque,
                        onTap: _isSynthesizing ? null : _triggerFreshAnalysis,
                        child: Container(
                          width: 32,
                          height: 32,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: AppColors.surfaceElevated,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AppColors.border, width: 0.8),
                          ),
                          child: _isSynthesizing
                              ? const CupertinoActivityIndicator(radius: 6.5, color: AppColors.gold)
                              : const Icon(LucideIcons.refreshCw, color: AppColors.gold, size: 14),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Circular Gauge + Bias Badge + Concise Institutional Analysis
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      ConfidenceMeter(
                        score: data.confidenceScore,
                        size: 86,
                        bias: data.bias,
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            BiasBadge(
                              bias: data.bias,
                              isLarge: true,
                              confidenceScore: data.confidenceScore,
                            ),
                            const SizedBox(height: 10),
                            Text(
                              data.biasSummary,
                              style: const TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 12.5,
                                height: 1.45,
                              ),
                              maxLines: 3,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),

                  // 3-Pillar Symmetrical Progress Breakdown
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceInset,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppColors.border, width: 0.8),
                    ),
                    child: Column(
                      children: [
                        _buildPillarProgressRow(
                          index: '1',
                          label: 'Fundamental',
                          percent: pillars.fundamental,
                          color: AppColors.cyan,
                        ),
                        const SizedBox(height: 11),
                        _buildPillarProgressRow(
                          index: '2',
                          label: 'Geopolitik',
                          percent: pillars.geopolitical,
                          color: AppColors.gold,
                        ),
                        const SizedBox(height: 11),
                        _buildPillarProgressRow(
                          index: '3',
                          label: 'Teknikal',
                          percent: pillars.technical,
                          color: biasColor,
                        ),
                      ],
                    ),
                  ),
                  if (data.technicalSnapshot['intermarket'] is Map) ...[
                    const SizedBox(height: 12),
                    _buildIntermarketStrip(
                      Map<String, dynamic>.from(data.technicalSnapshot['intermarket'] as Map),
                    ),
                  ],
                  const SizedBox(height: 14),

                  // Clean Deep Link to 3-Pillar Detail Page
                  GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: () => Navigator.of(context).push(
                      CupertinoPageRoute(
                        builder: (_) => const AnalysisDetailScreen(showAppBar: true),
                      ),
                    ),
                    child: const Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          'Lihat rincian 3 pilar, risiko & key levels',
                          style: TextStyle(
                            color: AppColors.gold,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        Icon(LucideIcons.chevronRight, color: AppColors.gold, size: 13),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // ─────────────────────────────────────────────────────────────────
            // 3. INSTITUTIONAL TRADE SETUP CARD (Grid 2x2 + Accordion)
            // ─────────────────────────────────────────────────────────────────
            if (data.tradeSetup != null && data.tradeSetup!.entryPrice > 0) ...[
              TradeSetupCard(
                setup: data.tradeSetup!,
                onViewChart: () => widget.onNavigateTab?.call(3),
              ),
              const SizedBox(height: 16),
            ],

            // ─────────────────────────────────────────────────────────────────
            // 4. QUICK INTRADAY NOTE (Technical Pulse Strip)
            // ─────────────────────────────────────────────────────────────────
            IosGlassCard(
              borderRadius: 20,
              padding: const EdgeInsets.all(18),
              onTap: () => widget.onNavigateTab?.call(3),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Row(
                        children: [
                          Icon(LucideIcons.zap, color: AppColors.cyan, size: 14),
                          SizedBox(width: 7),
                          Text(
                            'QUICK INTRADAY NOTE',
                            style: TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 11.5,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.7,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          _buildTinyChip(
                            'RSI ${data.technicalSnapshot['rsi'] ?? '-'}',
                            AppColors.cyan,
                          ),
                          const SizedBox(width: 6),
                          _buildTinyChip(
                            (data.technicalSnapshot['trend'] as String?) ?? 'NEUTRAL',
                            (data.technicalSnapshot['trend'] == 'BULLISH')
                                ? AppColors.bullish
                                : (data.technicalSnapshot['trend'] == 'BEARISH'
                                    ? AppColors.bearish
                                    : AppColors.gold),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    (data.technicalSnapshot['summary'] as String?)?.isNotEmpty == true
                        ? data.technicalSnapshot['summary'] as String
                        : 'Pantau struktur harga H1 & konfirmasi momentum M5 di area Support/Resistance kunci sebelum eksekusi.',
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12.5,
                      height: 1.48,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // ─────────────────────────────────────────────────────────────────
            // 5. HIGH-IMPACT CATALYST RADAR CARD (Pre-News 9-Step CTA)
            // ─────────────────────────────────────────────────────────────────
            if (data.upcomingHighImpactEvent != null) ...[
              IosGlassCard(
                borderRadius: 20,
                padding: const EdgeInsets.all(18),
                borderColor: AppColors.impactHigh.withValues(alpha: 0.25),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(7),
                              decoration: BoxDecoration(
                                color: AppColors.impactHigh.withValues(alpha: 0.14),
                                borderRadius: BorderRadius.circular(9),
                              ),
                              child: const Icon(
                                LucideIcons.triangleAlert,
                                color: AppColors.impactHigh,
                                size: 15,
                              ),
                            ),
                            const SizedBox(width: 10),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'HIGH-IMPACT CATALYST',
                                  style: TextStyle(
                                    color: AppColors.impactHigh,
                                    fontSize: 10.5,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 0.7,
                                  ),
                                ),
                                Text(
                                  '${data.upcomingHighImpactEvent!['currency'] ?? 'USD'} • Kalender Ekonomi',
                                  style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                                ),
                              ],
                            ),
                          ],
                        ),
                        GestureDetector(
                          behavior: HitTestBehavior.opaque,
                          onTap: () => widget.onNavigateTab?.call(1),
                          child: const Text(
                            'Semua',
                            style: TextStyle(
                              color: AppColors.textMuted,
                              fontSize: 11.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    Text(
                      data.upcomingHighImpactEvent!['title'] ?? '',
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 15,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -0.2,
                      ),
                    ),
                    if (data.upcomingHighImpactEvent!['scheduled_at'] != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        data.upcomingHighImpactEvent!['scheduled_at'] != null
                            ? parseUtcDateTime(data.upcomingHighImpactEvent!['scheduled_at'].toString()).formatWibWithDay()
                            : '-',
                        style: AppTypography.mono(
                          color: AppColors.gold,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                    const SizedBox(height: 12),

                    // Clean 2-Column Forecast & Previous Strip
                    Container(
                      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 14),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceInset,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border, width: 0.8),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: _buildPriceStatCol(
                              label: 'FORECAST',
                              value: '${data.upcomingHighImpactEvent!['forecast'] ?? '-'}',
                              valueColor: AppColors.textPrimary,
                            ),
                          ),
                          Container(width: 0.8, height: 24, color: AppColors.border),
                          Expanded(
                            child: _buildPriceStatCol(
                              label: 'SEBELUMNYA',
                              value: '${data.upcomingHighImpactEvent!['previous'] ?? '-'}',
                              valueColor: AppColors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Radiant Gold Primary CTA Button
                    SizedBox(
                      width: double.infinity,
                      child: CupertinoButton(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        color: AppColors.gold,
                        borderRadius: BorderRadius.circular(12),
                        onPressed: () async {
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
                        child: const Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(LucideIcons.sparkles, color: Color(0xFF08090C), size: 15),
                            SizedBox(width: 7),
                            Text(
                              'Buka Skenario Pre-News (9 Langkah)',
                              style: TextStyle(
                                color: Color(0xFF08090C),
                                fontSize: 12.5,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
            ],

            // ─────────────────────────────────────────────────────────────────
            // 6. LATEST GEOPOLITICAL HEADLINE SNAPSHOT
            // ─────────────────────────────────────────────────────────────────
            if (data.latestGeopoliticalHeadline != null) ...[
              IosGlassCard(
                borderRadius: 20,
                padding: const EdgeInsets.all(18),
                onTap: () {
                  final h = data.latestGeopoliticalHeadline!;
                  final article = NewsArticleModel(
                    id: 0,
                    symbol: 'XAUUSD',
                    title: h['title'] ?? '',
                    source: h['source'] ?? 'Global Wire',
                    url: h['url'],
                    summary: h['summary'] ?? h['title'],
                    sentimentLabel: h['sentiment_label'] ?? 'NEUTRAL',
                    sentimentScore: (h['sentiment_score'] as num?)?.toDouble() ?? 0.0,
                    publishedAt: parseUtcDateTime(h['published_at']?.toString()),
                  );
                  NewsDetailSheet.show(context, article);
                },
                child: Builder(
                  builder: (context) {
                    final h = data.latestGeopoliticalHeadline!;
                    final sentimentLabel = (h['sentiment_label'] ?? 'NEUTRAL').toString().toUpperCase();
                    final Color sentimentColor = sentimentLabel == 'POSITIVE'
                        ? AppColors.bullish
                        : (sentimentLabel == 'NEGATIVE' ? AppColors.bearish : AppColors.gold);
                    final String displaySent = sentimentLabel == 'POSITIVE'
                        ? 'BULLISH'
                        : (sentimentLabel == 'NEGATIVE' ? 'BEARISH' : 'NETRAL');

                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Row(
                              children: [
                                Icon(LucideIcons.globe, color: AppColors.gold, size: 14),
                                SizedBox(width: 7),
                                Text(
                                  'BERITA GEOPOLITIK TERKINI',
                                  style: TextStyle(
                                    color: AppColors.textMuted,
                                    fontSize: 11,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 0.7,
                                  ),
                                ),
                              ],
                            ),
                            _buildTinyChip(displaySent, sentimentColor),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Text(
                          h['title'] ?? '',
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            height: 1.4,
                          ),
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 10),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Text(
                                '${h['source'] ?? 'Global Wire'}${h['published_at'] != null ? ' • ${parseUtcDateTime(h['published_at'].toString()).formatWibShort()}' : ''}',
                                style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Row(
                              children: [
                                Text(
                                  'Baca',
                                  style: TextStyle(
                                    color: AppColors.gold,
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                SizedBox(width: 2),
                                Icon(LucideIcons.chevronRight, color: AppColors.gold, size: 11),
                              ],
                            ),
                          ],
                        ),
                      ],
                    );
                  },
                ),
              ),
              const SizedBox(height: 16),
            ],

            // 7. Clean Legal Disclaimer
            DisclaimerBanner(customText: data.disclaimer),
          ],
        ),
      ),
    );
  }

  Widget _buildPriceStatCol({
    required String label,
    required String value,
    required Color valueColor,
  }) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: AppColors.textTertiary,
            fontSize: 9.5,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.6,
          ),
        ),
        const SizedBox(height: 4),
        FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(
            value,
            style: AppTypography.mono(
              color: valueColor,
              fontSize: 12.5,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPillarProgressRow({
    required String index,
    required String label,
    required int percent,
    required Color color,
  }) {
    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Text(
                  '$index. ',
                  style: AppTypography.mono(
                    color: AppColors.textTertiary,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  label,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            Text(
              '+$percent%',
              style: AppTypography.mono(
                color: color,
                fontSize: 11.5,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: SizedBox(
            height: 5,
            child: TweenAnimationBuilder<double>(
              tween: Tween<double>(begin: 0, end: (percent.clamp(0, 100)) / 100.0),
              duration: const Duration(milliseconds: 900),
              curve: Curves.easeOutCubic,
              builder: (context, val, _) {
                return LinearProgressIndicator(
                  value: val,
                  backgroundColor: const Color(0xFF1A1F2C),
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                );
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildIntermarketStrip(Map<String, dynamic> im) {
    final dxy = im['dxy'] is Map ? Map<String, dynamic>.from(im['dxy'] as Map) : null;
    final us10y = im['us10y'] is Map ? Map<String, dynamic>.from(im['us10y'] as Map) : null;
    final wti = im['wti'] is Map ? Map<String, dynamic>.from(im['wti'] as Map) : null;
    if (dxy == null && us10y == null && wti == null) {
      return const SizedBox.shrink();
    }

    Widget cell(String label, Map<String, dynamic>? q, {String prefix = '', String suffix = ''}) {
      if (q == null) {
        return Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 9.5, fontWeight: FontWeight.w700)),
              const SizedBox(height: 3),
              Text('-', style: AppTypography.mono(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.w700)),
            ],
          ),
        );
      }
      final price = (q['price'] as num?)?.toDouble() ?? 0.0;
      final pct = (q['change_pct'] as num?)?.toDouble() ?? 0.0;
      final effect = q['gold_effect']?.toString() ?? 'NEUTRAL';
      final color = effect == 'BULLISH_GOLD'
          ? AppColors.bullish
          : (effect == 'BEARISH_GOLD' ? AppColors.bearish : AppColors.textSecondary);
      final sign = pct >= 0 ? '+' : '';
      return Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Text(
              label,
              style: const TextStyle(
                color: AppColors.textMuted,
                fontSize: 9.5,
                fontWeight: FontWeight.w700,
                letterSpacing: 0.4,
              ),
            ),
            const SizedBox(height: 3),
            FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(
                '$prefix${price.toStringAsFixed(2)}$suffix',
                style: AppTypography.mono(
                  color: AppColors.textPrimary,
                  fontSize: 12.5,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
            const SizedBox(height: 2),
            Text(
              '$sign${pct.toStringAsFixed(2)}%',
              style: AppTypography.mono(
                color: color,
                fontSize: 10,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surfaceInset,
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: Row(
        children: [
          cell('DXY', dxy),
          Container(width: 0.8, height: 32, color: AppColors.borderSubtle),
          cell('US10Y', us10y, suffix: '%'),
          Container(width: 0.8, height: 32, color: AppColors.borderSubtle),
          cell('WTI OIL', wti, prefix: '\$'),
        ],
      ),
    );
  }

  Widget _buildTinyChip(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7.5, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.13),
        borderRadius: BorderRadius.circular(7),
        border: Border.all(color: color.withValues(alpha: 0.30), width: 0.7),
      ),
      child: Text(
        text,
        style: AppTypography.mono(
          color: color,
          fontSize: 9.5,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
