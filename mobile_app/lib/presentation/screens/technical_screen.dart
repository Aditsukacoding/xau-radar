import 'dart:async';
import 'dart:math';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/network/api_service.dart';
import '../../data/models/price_candle_model.dart';
import '../../data/models/technical_indicators_model.dart';
import '../../data/models/trade_setup_model.dart';
import '../widgets/ios_glass_card.dart';
import '../widgets/tradingview_chart_widget.dart';
import '../widgets/trade_setup_card.dart';
import '../widgets/market_analysis_card.dart';

class TechnicalScreen extends StatefulWidget {
  const TechnicalScreen({super.key});

  @override
  State<TechnicalScreen> createState() => _TechnicalScreenState();
}

class _TechnicalScreenState extends State<TechnicalScreen> {
  final ApiService _api = ApiService();
  List<PriceCandleModel> _candles = [];
  TechnicalIndicatorsModel? _indicators;
  TradeSetupModel? _tradeSetup;
  bool _isLoading = true;
  String? _error;
  String _activeTimeframe = '5m';

  Timer? _livePricePollTimer;
  Timer? _indicatorsAutoSyncTimer;
  bool _isPollingTick = false;

  @override
  void initState() {
    super.initState();
    _loadTechnicalData();
    _startRealtimeStreaming();
  }

  @override
  void dispose() {
    _livePricePollTimer?.cancel();
    _indicatorsAutoSyncTimer?.cancel();
    super.dispose();
  }

  void _startRealtimeStreaming() {
    _livePricePollTimer?.cancel();
    _indicatorsAutoSyncTimer?.cancel();

    // 1. Continuous genuine market tick poll from FOREX.com every 700ms (High-frequency sub-second)
    _livePricePollTimer = Timer.periodic(const Duration(milliseconds: 700), (timer) async {
      if (!mounted || _isPollingTick) return;
      _isPollingTick = true;
      try {
        final tick = await _api.getLivePriceTick(symbol: 'XAUUSD');
        final double? price = (tick['current_price'] as num?)?.toDouble();
        if (price != null && mounted) {
          _applyPriceTick(price);
        }
      } catch (_) {
      } finally {
        _isPollingTick = false;
      }
    });

    // 2. Periodic background silent sync of indicators & candles every 15s
    _indicatorsAutoSyncTimer = Timer.periodic(const Duration(seconds: 15), (_) {
      _loadTechnicalData(silent: true);
    });
  }

  void _applyPriceTick(double newPrice) {
    if (_candles.isEmpty) return;
    final last = _candles.last;
    final updatedHigh = max(last.high, newPrice);
    final updatedLow = min(last.low, newPrice);

    setState(() {
      _candles[_candles.length - 1] = last.copyWith(
        close: newPrice,
        high: updatedHigh,
        low: updatedLow,
      );
    });
  }

  Future<void> _loadTechnicalData({bool silent = false}) async {
    if (!silent && _candles.isEmpty) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    }
    try {
      // Parallel concurrent load for sub-second page rendering
      final results = await Future.wait([
        _api.getCandles('XAUUSD', timeframe: _activeTimeframe, limit: 60),
        _api.getTechnicalIndicators('XAUUSD', timeframe: _activeTimeframe),
        _api.getLivePriceTick(symbol: 'XAUUSD'),
        _api.getLatestAnalysis(symbol: 'XAUUSD').then<TradeSetupModel?>((rep) => rep.tradeSetup).catchError((_) => null),
      ]);

      final candles = results[0] as List<PriceCandleModel>;
      final indicators = results[1] as TechnicalIndicatorsModel;
      final tradeSetup = results[3] as TradeSetupModel?;

      if (mounted) {
        setState(() {
          _candles = candles;
          _indicators = indicators;
          _tradeSetup = tradeSetup;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted && _candles.isEmpty) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  void _onTimeframeChanged(String tf) {
    if (_activeTimeframe != tf) {
      setState(() {
        _activeTimeframe = tf;
      });
      _loadTechnicalData();
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
                      CupertinoButton.filled(onPressed: _loadTechnicalData, child: const Text('Coba Lagi')),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadTechnicalData,
                  color: AppColors.primary,
                  backgroundColor: const Color(0xFF1C1C1E),
                  edgeOffset: 80,
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
                    padding: const EdgeInsets.fromLTRB(16, 75, 16, 100),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Section Label with FOREX.com indicator
                        Padding(
                          padding: const EdgeInsets.only(left: 4, bottom: 12),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text(
                                'GRAFIK TEKNIKAL REAL-TIME',
                                style: TextStyle(
                                  color: AppColors.textMuted,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 0.8,
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                                decoration: BoxDecoration(
                                  color: const Color(0x2010B981),
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: const Color(0x5010B981), width: 0.8),
                                ),
                                child: const Row(
                                  children: [
                                    Icon(Icons.circle, size: 7, color: Color(0xFF10B981)),
                                    SizedBox(width: 5),
                                    Text(
                                      'FOREX.COM • LIVE REAL-TIME',
                                      style: TextStyle(
                                        color: Color(0xFF10B981),
                                        fontSize: 10,
                                        fontWeight: FontWeight.w700,
                                        letterSpacing: 0.4,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),

                        // Live Real-Time Interactive TradingView Chart
                        TradingViewChartWidget(
                          symbol: 'FOREXCOM:XAUUSD',
                          activeTimeframe: _activeTimeframe,
                          onTimeframeChanged: _onTimeframeChanged,
                        ),
                        const SizedBox(height: 16),

                        // Hasil Pembacaan Chart TradingView: Entry, SL, TP1, TP2
                        if (_tradeSetup != null && _tradeSetup!.entryPrice > 0) ...[
                          const Padding(
                            padding: EdgeInsets.only(left: 4, bottom: 8),
                            child: Text(
                              'HASIL SETUP TRADING (DARI CHART TRADINGVIEW)',
                              style: TextStyle(
                                color: AppColors.textMuted,
                                fontSize: 11.5,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 0.8,
                              ),
                            ),
                          ),
                          TradeSetupCard(
                            setup: _tradeSetup!,
                          ),
                          const SizedBox(height: 16),
                        ],

                        // Analisis Pasar & Panduan Scalping / Intraday
                        MarketAnalysisCard(
                          bias: _indicators?.trendDirection ?? 'BULLISH',
                          confidenceScore: 82,
                          trendDirection: _indicators?.trendDirection ?? 'BULLISH',
                          rsi: _indicators?.rsi14,
                          rsiCondition: _indicators?.rsiCondition,
                          supportLevels: _indicators?.supportLevels ?? const [],
                          resistanceLevels: _indicators?.resistanceLevels ?? const [],
                          summary: _indicators?.summary,
                          technicalRationale: _tradeSetup?.technicalRationale,
                        ),
                        const SizedBox(height: 16),

                        // 2. Trend & Rationale Card
                        if (_indicators != null) ...[
                          IosGlassCard(
                            borderRadius: 20,
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    const Text(
                                      'STRUKTUR MOMENTUM',
                                      style: TextStyle(color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.6),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: _indicators!.trendDirection == 'BULLISH'
                                            ? AppColors.bullish.withValues(alpha: 0.15)
                                            : (_indicators!.trendDirection == 'BEARISH'
                                                ? AppColors.bearish.withValues(alpha: 0.15)
                                                : AppColors.neutral.withValues(alpha: 0.15)),
                                        borderRadius: BorderRadius.circular(10),
                                        border: Border.all(
                                          color: (_indicators!.trendDirection == 'BULLISH'
                                                  ? AppColors.bullish
                                                  : (_indicators!.trendDirection == 'BEARISH' ? AppColors.bearish : AppColors.neutral))
                                              .withValues(alpha: 0.4),
                                        ),
                                      ),
                                      child: Text(
                                        _indicators!.trendDirection,
                                        style: TextStyle(
                                          color: _indicators!.trendDirection == 'BULLISH'
                                              ? AppColors.bullish
                                              : (_indicators!.trendDirection == 'BEARISH'
                                                  ? AppColors.bearish
                                                  : AppColors.neutral),
                                          fontSize: 10,
                                          fontWeight: FontWeight.w700,
                                          letterSpacing: 0.5,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 10),
                                Text(
                                  _indicators!.summary,
                                  style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, height: 1.4),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),

                          // 3. Indicators Grid (RSI & Moving Averages)
                          Row(
                            children: [
                              // RSI Card
                              Expanded(
                                child: IosGlassCard(
                                  borderRadius: 18,
                                  padding: const EdgeInsets.all(14),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text(
                                        'RSI (14)',
                                        style: TextStyle(color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.w700),
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        _indicators!.rsi14?.toStringAsFixed(1) ?? '-',
                                        style: const TextStyle(
                                          color: AppColors.textPrimary,
                                          fontSize: 26,
                                          fontWeight: FontWeight.w800,
                                          fontFamily: 'monospace',
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        _indicators!.rsiCondition ?? 'NEUTRAL',
                                        style: TextStyle(
                                          color: _indicators!.rsiCondition == 'OVERBOUGHT'
                                              ? AppColors.bearish
                                              : (_indicators!.rsiCondition == 'OVERSOLD'
                                                  ? AppColors.bullish
                                                  : AppColors.neutral),
                                          fontSize: 10,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),

                              // EMA Cross Card
                              Expanded(
                                child: IosGlassCard(
                                  borderRadius: 18,
                                  padding: const EdgeInsets.all(14),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text(
                                        'EMA 9 / 21',
                                        style: TextStyle(color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.w700),
                                      ),
                                      const SizedBox(height: 8),
                                      Text(
                                        '${_indicators!.ema9?.toStringAsFixed(1) ?? '-'} / ${_indicators!.ema21?.toStringAsFixed(1) ?? '-'}',
                                        style: const TextStyle(
                                          color: AppColors.primary,
                                          fontSize: 15,
                                          fontWeight: FontWeight.w800,
                                          fontFamily: 'monospace',
                                        ),
                                      ),
                                      const SizedBox(height: 6),
                                      Text(
                                        (_indicators!.ema9 ?? 0) > (_indicators!.ema21 ?? 0)
                                            ? 'Golden Cross'
                                            : 'Death Cross',
                                        style: TextStyle(
                                          color: (_indicators!.ema9 ?? 0) > (_indicators!.ema21 ?? 0)
                                              ? AppColors.bullish
                                              : AppColors.bearish,
                                          fontSize: 10,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),

                          // 4. Moving Averages Table Card
                          IosGlassCard(
                            borderRadius: 20,
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'MOVING AVERAGES',
                                  style: TextStyle(color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5),
                                ),
                                const SizedBox(height: 12),
                                _buildMetricRow('SMA 20 (Cepat)', '\$${_indicators!.sma20?.toStringAsFixed(2) ?? '-'}'),
                                const Divider(height: 16, color: AppColors.borderSubtle),
                                _buildMetricRow('SMA 50 (Menengah)', '\$${_indicators!.sma50?.toStringAsFixed(2) ?? '-'}'),
                                const Divider(height: 16, color: AppColors.borderSubtle),
                                _buildMetricRow('SMA 200 (Tren Utama)', '\$${_indicators!.sma200?.toStringAsFixed(2) ?? '-'}'),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),

                          // 5. Support & Resistance Key Zones
                          IosGlassCard(
                            borderRadius: 20,
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'LEVEL KUNCI HARGA (SUPPORT & RESISTANCE)',
                                  style: TextStyle(color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.5),
                                ),
                                const SizedBox(height: 14),
                                Row(
                                  children: [
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const Row(
                                            children: [
                                              Icon(CupertinoIcons.arrow_down_circle_fill, color: AppColors.supportLine, size: 14),
                                              SizedBox(width: 5),
                                              Text('Area Support', style: TextStyle(color: AppColors.supportLine, fontSize: 11, fontWeight: FontWeight.w700)),
                                            ],
                                          ),
                                          const SizedBox(height: 8),
                                          ...(_indicators!.supportLevels.map((s) => Padding(
                                                padding: const EdgeInsets.only(bottom: 3),
                                                child: Text(
                                                  '\$${s.toStringAsFixed(2)}',
                                                  style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontFamily: 'monospace', fontWeight: FontWeight.w700),
                                                ),
                                              ))),
                                        ],
                                      ),
                                    ),
                                    Container(width: 0.8, height: 60, color: AppColors.borderSubtle),
                                    const SizedBox(width: 14),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const Row(
                                            children: [
                                              Icon(CupertinoIcons.arrow_up_circle_fill, color: AppColors.resistanceLine, size: 14),
                                              SizedBox(width: 5),
                                              Text('Area Resistance', style: TextStyle(color: AppColors.resistanceLine, fontSize: 11, fontWeight: FontWeight.w700)),
                                            ],
                                          ),
                                          const SizedBox(height: 8),
                                          ...(_indicators!.resistanceLevels.map((r) => Padding(
                                                padding: const EdgeInsets.only(bottom: 3),
                                                child: Text(
                                                  '\$${r.toStringAsFixed(2)}',
                                                  style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontFamily: 'monospace', fontWeight: FontWeight.w700),
                                                ),
                                              ))),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildMetricRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        Text(
          value,
          style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontWeight: FontWeight.w700, fontFamily: 'monospace'),
        ),
      ],
    );
  }
}
