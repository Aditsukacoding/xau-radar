import 'dart:math';
import 'dart:ui' as ui;
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/wib_date_time.dart';
import '../../data/models/price_candle_model.dart';
import '../../data/models/trade_setup_model.dart';
import 'ios_glass_card.dart';
import 'ios_segmented_control.dart';

class CandlestickChartWidget extends StatefulWidget {
  final List<PriceCandleModel> candles;
  final List<double> supportLevels;
  final List<double> resistanceLevels;
  final String activeTimeframe;
  final Function(String) onTimeframeChanged;
  final TradeSetupModel? tradeSetup;

  // Optional legacy fields retained for Hot Reload runtime compatibility
  final double? resistanceZoneHigh;
  final double? resistanceZoneLow;
  final double? targetZoneHigh;
  final double? targetZoneLow;
  final double? tp1;
  final double? tp2;
  final double? majorSupport;
  final double? sellPrice;
  final double? buyPrice;
  final int spread;
  final double? high24h;
  final double? low24h;
  final double? changePct24h;
  final String feedSource;

  const CandlestickChartWidget({
    super.key,
    required this.candles,
    this.supportLevels = const [],
    this.resistanceLevels = const [],
    required this.activeTimeframe,
    required this.onTimeframeChanged,
    this.tradeSetup,
    this.resistanceZoneHigh,
    this.resistanceZoneLow,
    this.targetZoneHigh,
    this.targetZoneLow,
    this.tp1,
    this.tp2,
    this.majorSupport,
    this.sellPrice,
    this.buyPrice,
    this.spread = 69,
    this.high24h,
    this.low24h,
    this.changePct24h,
    this.feedSource = 'Twelve Data',
  });

  @override
  State<CandlestickChartWidget> createState() => _CandlestickChartWidgetState();
}

class _CandlestickChartWidgetState extends State<CandlestickChartWidget> {
  int? _selectedIndex;
  Color _priceFlashColor = Colors.transparent;
  bool _showTradeSetupOverlay = true;

  @override
  void didUpdateWidget(covariant CandlestickChartWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.candles.isNotEmpty && oldWidget.candles.isNotEmpty) {
      final oldClose = oldWidget.candles.last.close;
      final newClose = widget.candles.last.close;
      if (newClose != oldClose) {
        setState(() {
          _priceFlashColor = newClose > oldClose
              ? AppColors.bullish.withValues(alpha: 0.3)
              : AppColors.bearish.withValues(alpha: 0.3);
        });
        Future.delayed(const Duration(milliseconds: 400), () {
          if (mounted) {
            setState(() {
              _priceFlashColor = Colors.transparent;
            });
          }
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.candles.isEmpty) {
      return Container(
        height: 350,
        alignment: Alignment.center,
        child: const Text('Memuat grafik pasar...', style: TextStyle(color: AppColors.textMuted)),
      );
    }

    final selectedCandle = _selectedIndex != null && _selectedIndex! < widget.candles.length
        ? widget.candles[_selectedIndex!]
        : widget.candles.last;

    final double candleDiff = selectedCandle.close - selectedCandle.open;
    final double candleDiffPct = selectedCandle.open != 0 ? (candleDiff / selectedCandle.open) * 100 : 0.0;

    return IosGlassCard(
      padding: EdgeInsets.zero,
      borderRadius: 22,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 1. Header: Asset Title & Timeframe Selector
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Text(
                            'Gold Spot / U.S. Dollar',
                            style: TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                              letterSpacing: -0.2,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: const Color(0x25F59E0B),
                              borderRadius: BorderRadius.circular(5),
                              border: Border.all(color: const Color(0x60F59E0B), width: 0.8),
                            ),
                            child: Text(
                              widget.feedSource,
                              style: const TextStyle(
                                color: Color(0xFFF59E0B),
                                fontSize: 9.5,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 3),
                      Row(
                        children: [
                          Text(
                            selectedCandle.timestamp.formatWibFull(),
                            style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                          ),
                          const SizedBox(width: 8),
                          // Live indicator
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: AppColors.bullish.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(
                                color: AppColors.bullish.withValues(alpha: 0.5),
                                width: 0.8,
                              ),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.circle, size: 5, color: AppColors.bullish),
                                SizedBox(width: 3.5),
                                Text(
                                  'LIVE',
                                  style: TextStyle(
                                    color: AppColors.bullish,
                                    fontSize: 8.5,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                // Timeframe Selector
                IosSegmentedControl<String>(
                  items: const {
                    '5m': '5M',
                    '15m': '15M',
                    '1h': '1H',
                    '4h': '4H',
                    '1d': '1D',
                  },
                  selectedValue: widget.activeTimeframe.toLowerCase(),
                  onValueChanged: widget.onTimeframeChanged,
                ),
              ],
            ),
          ),

          // 2. Price Bar & 24h Performance
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 2, 16, 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 250),
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        color: _priceFlashColor,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        '\$${selectedCandle.close.toStringAsFixed(2)}',
                        style: TextStyle(
                          color: selectedCandle.isBullish ? AppColors.bullish : AppColors.bearish,
                          fontSize: 24,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -0.5,
                          fontFamily: 'monospace',
                        ),
                      ),
                    ),
                    const SizedBox(height: 2),
                    Builder(
                      builder: (context) {
                        final double computedHigh = widget.high24h ?? (widget.candles.isNotEmpty ? widget.candles.map((c) => c.high).reduce(max) : 0.0);
                        final double computedLow = widget.low24h ?? (widget.candles.isNotEmpty ? widget.candles.map((c) => c.low).reduce(min) : 0.0);
                        final double computedChgPct = widget.changePct24h ?? candleDiffPct;
                        final bool isUp = computedChgPct >= 0;

                        return Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: isUp ? AppColors.bullish.withValues(alpha: 0.15) : AppColors.bearish.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(5),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(isUp ? Icons.arrow_drop_up : Icons.arrow_drop_down, color: isUp ? AppColors.bullish : AppColors.bearish, size: 14),
                                  Text(
                                    '${isUp ? '+' : ''}${computedChgPct.toStringAsFixed(2)}%',
                                    style: TextStyle(
                                      color: isUp ? AppColors.bullish : AppColors.bearish,
                                      fontSize: 11,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              '24H H: ${computedHigh.toStringAsFixed(2)}  L: ${computedLow.toStringAsFixed(2)}',
                              style: const TextStyle(color: AppColors.textMuted, fontSize: 10.5, fontFamily: 'monospace'),
                            ),
                          ],
                        );
                      },
                    ),
                  ],
                ),
              ],
            ),
          ),

          // 3. Sub-bar OHLC & Volume metrics
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: const Color(0x351F2636),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildOhlcTag('O', selectedCandle.open),
                _buildOhlcTag('H', selectedCandle.high),
                _buildOhlcTag('L', selectedCandle.low),
                _buildOhlcTag('C', selectedCandle.close),
                Text(
                  '${candleDiff >= 0 ? '+' : ''}${candleDiff.toStringAsFixed(2)} (${candleDiffPct >= 0 ? '+' : ''}${candleDiffPct.toStringAsFixed(2)}%)',
                  style: TextStyle(
                    color: candleDiff >= 0 ? AppColors.bullish : AppColors.bearish,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    fontFamily: 'monospace',
                  ),
                ),
              ],
            ),
          ),
          // 3.5 AI Trade Setup Visual Overlay Toggle Bar
          if (widget.tradeSetup != null && widget.tradeSetup!.entryPrice > 0) ...[
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  GestureDetector(
                    onTap: () {
                      setState(() {
                        _showTradeSetupOverlay = !_showTradeSetupOverlay;
                      });
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                      decoration: BoxDecoration(
                        color: _showTradeSetupOverlay
                            ? (widget.tradeSetup!.action == 'BUY'
                                ? AppColors.bullish.withValues(alpha: 0.15)
                                : AppColors.bearish.withValues(alpha: 0.15))
                            : const Color(0x351F2636),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: _showTradeSetupOverlay
                              ? (widget.tradeSetup!.action == 'BUY'
                                  ? AppColors.bullish.withValues(alpha: 0.45)
                                  : AppColors.bearish.withValues(alpha: 0.45))
                              : AppColors.borderSubtle,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            _showTradeSetupOverlay ? CupertinoIcons.checkmark_circle_fill : CupertinoIcons.circle,
                            color: widget.tradeSetup!.action == 'BUY' ? AppColors.bullish : AppColors.bearish,
                            size: 13,
                          ),
                          const SizedBox(width: 5),
                          Text(
                            'Overlay Setup AI (${widget.tradeSetup!.action})',
                            style: TextStyle(
                              color: widget.tradeSetup!.action == 'BUY' ? AppColors.bullish : AppColors.bearish,
                              fontSize: 10,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  Row(
                    children: [
                      _buildMiniLevelBadge('SL', widget.tradeSetup!.stopLoss, AppColors.bearish),
                      const SizedBox(width: 4),
                      _buildMiniLevelBadge('TP1', widget.tradeSetup!.takeProfit1, AppColors.bullish),
                      const SizedBox(width: 4),
                      _buildMiniLevelBadge('TP2', widget.tradeSetup!.takeProfit2, const Color(0xFF00E676)),
                    ],
                  ),
                ],
              ),
            ),
          ],
          const Divider(height: 1, color: AppColors.borderSubtle),

          // 4. Pure Native Candlestick & Volume Canvas
          SizedBox(
            height: 290,
            child: GestureDetector(
              onHorizontalDragUpdate: (details) {
                _handleTouch(details.localPosition);
              },
              onTapDown: (details) {
                _handleTouch(details.localPosition);
              },
              child: CustomPaint(
                painter: _PureCandlePainter(
                  candles: widget.candles,
                  selectedIndex: _selectedIndex,
                  tradeSetup: widget.tradeSetup,
                  showTradeSetupOverlay: _showTradeSetupOverlay,
                ),
                size: const Size(double.infinity, 290),
              ),
            ),
          ),
          const Divider(height: 1, color: AppColors.borderSubtle),

          // 5. Clean Legend Footer
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    _buildLegendItem('SMA 20', AppColors.maFast),
                    const SizedBox(width: 14),
                    _buildLegendItem('Volume', const Color(0xFF6B7280)),
                  ],
                ),
                const Text(
                  'Sentuh untuk inspeksi candle',
                  style: TextStyle(color: AppColors.textTertiary, fontSize: 10, fontStyle: FontStyle.italic),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOhlcTag(String label, double val) {
    return Row(
      children: [
        Text(
          '$label ',
          style: const TextStyle(color: AppColors.textMuted, fontSize: 10.5, fontWeight: FontWeight.w600),
        ),
        Text(
          val.toStringAsFixed(2),
          style: const TextStyle(
            color: AppColors.textPrimary,
            fontSize: 10.5,
            fontWeight: FontWeight.w600,
            fontFamily: 'monospace',
          ),
        ),
      ],
    );
  }

  void _handleTouch(Offset localPos) {
    if (widget.candles.isEmpty) return;
    final chartWidth = (context.size?.width ?? 320) - 62.0;
    final candleWidth = chartWidth / widget.candles.length;
    final index = (localPos.dx / candleWidth).clamp(0, widget.candles.length - 1).toInt();
    setState(() {
      _selectedIndex = index;
    });
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 10,
          height: 3,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(2),
          ),
        ),
        const SizedBox(width: 5),
        Text(
          label,
          style: const TextStyle(color: AppColors.textMuted, fontSize: 10.5, fontWeight: FontWeight.w500),
        ),
      ],
    );
  }

  Widget _buildMiniLevelBadge(String label, double val, Color color) {
    if (val <= 0) return const SizedBox.shrink();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.35), width: 0.7),
      ),
      child: Text(
        '$label \$${val.toStringAsFixed(1)}',
        style: TextStyle(
          color: color,
          fontSize: 9,
          fontWeight: FontWeight.w800,
          fontFamily: 'monospace',
        ),
      ),
    );
  }
}

class _PureCandlePainter extends CustomPainter {
  final List<PriceCandleModel> candles;
  final int? selectedIndex;
  final TradeSetupModel? tradeSetup;
  final bool showTradeSetupOverlay;

  _PureCandlePainter({
    required this.candles,
    this.selectedIndex,
    this.tradeSetup,
    this.showTradeSetupOverlay = true,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (candles.isEmpty) return;

    final double paddingRight = 62.0; // Margin for Y-axis labels & live pill
    final double chartWidth = size.width - paddingRight;
    final double priceAreaHeight = size.height * 0.76;
    final double volumeAreaHeight = size.height * 0.18;

    // 1. Min / Max Price with 3% padding
    double minPrice = candles.map((c) => c.low).reduce(min);
    double maxPrice = candles.map((c) => c.high).reduce(max);

    // Frame trade setup levels if enabled
    if (showTradeSetupOverlay && tradeSetup != null && tradeSetup!.entryPrice > 0) {
      if (tradeSetup!.stopLoss > 0) minPrice = min(minPrice, tradeSetup!.stopLoss - 1.5);
      if (tradeSetup!.takeProfit2 > 0) maxPrice = max(maxPrice, tradeSetup!.takeProfit2 + 1.5);
    }

    final double pricePadding = (maxPrice - minPrice) * 0.03;
    minPrice -= pricePadding;
    maxPrice += pricePadding;

    final double priceRange = (maxPrice - minPrice) == 0 ? 1.0 : (maxPrice - minPrice);
    final double candleStep = chartWidth / candles.length;
    final double candleWidth = max(2.5, candleStep * 0.72);

    // 2. Horizontal Grid & Price Y-Axis Labels
    final gridPaint = Paint()
      ..color = AppColors.borderSubtle.withValues(alpha: 0.6)
      ..strokeWidth = 0.6;

    final coordStyle = const TextStyle(
      color: AppColors.textMuted,
      fontSize: 9.5,
      fontFamily: 'monospace',
    );

    const int gridLines = 4;
    for (int i = 0; i <= gridLines; i++) {
      final double y = priceAreaHeight * (i / gridLines);
      canvas.drawLine(Offset(0, y), Offset(chartWidth, y), gridPaint);

      final double p = maxPrice - (priceRange * (i / gridLines));
      final textSpan = TextSpan(text: p.toStringAsFixed(1), style: coordStyle);
      final tp = TextPainter(text: textSpan, textDirection: ui.TextDirection.ltr)..layout();
      tp.paint(canvas, Offset(chartWidth + 6, y - 5));
    }

    // 3. Draw Volume Bars at Bottom (Translucent)
    final double maxVolume = candles.map((c) => c.volume).reduce(max);
    if (maxVolume > 0) {
      for (int i = 0; i < candles.length; i++) {
        final c = candles[i];
        final double x = (i * candleStep) + (candleStep / 2);
        final double vHeight = (c.volume / maxVolume) * volumeAreaHeight;
        final double vTop = size.height - vHeight;

        final Color vColor = c.isBullish
            ? AppColors.bullish.withValues(alpha: 0.25)
            : AppColors.bearish.withValues(alpha: 0.25);

        canvas.drawRect(
          Rect.fromLTWH(x - (candleWidth / 2), vTop, candleWidth, vHeight),
          Paint()..color = vColor,
        );
      }
    }

    // 4. Draw Candlesticks (Apple Stocks Clean Aesthetic)
    final upPaint = Paint()..color = AppColors.candleUp;
    final downPaint = Paint()..color = AppColors.candleDown;
    final wickUpPaint = Paint()
      ..color = AppColors.candleUp
      ..strokeWidth = 1.2;
    final wickDownPaint = Paint()
      ..color = AppColors.candleDown
      ..strokeWidth = 1.2;

    for (int i = 0; i < candles.length; i++) {
      final c = candles[i];
      final double x = (i * candleStep) + (candleStep / 2);

      final double openY = priceAreaHeight - ((c.open - minPrice) / priceRange * priceAreaHeight);
      final double closeY = priceAreaHeight - ((c.close - minPrice) / priceRange * priceAreaHeight);
      final double highY = priceAreaHeight - ((c.high - minPrice) / priceRange * priceAreaHeight);
      final double lowY = priceAreaHeight - ((c.low - minPrice) / priceRange * priceAreaHeight);

      final bool isUp = c.isBullish;
      final wickPaint = isUp ? wickUpPaint : wickDownPaint;
      final bodyPaint = isUp ? upPaint : downPaint;

      // Draw Wick
      canvas.drawLine(Offset(x, highY), Offset(x, lowY), wickPaint);

      // Draw Body
      final double top = min(openY, closeY);
      final double bottom = max(openY, closeY);
      final double height = max(2.0, bottom - top);

      canvas.drawRRect(
        RRect.fromRectAndRadius(
          Rect.fromCenter(center: Offset(x, top + (height / 2)), width: candleWidth, height: height),
          const Radius.circular(1.5),
        ),
        bodyPaint,
      );
    }

    // 5. Draw SMA 20 (Cyan Neon Curve)
    final maPaint = Paint()
      ..color = AppColors.maFast
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    final maPath = Path();
    bool maStarted = false;
    for (int i = 19; i < candles.length; i++) {
      final double x = (i * candleStep) + (candleStep / 2);
      final sub = candles.sublist(i - 19, i + 1);
      final avg = sub.map((c) => c.close).reduce((a, b) => a + b) / 20.0;
      final double y = priceAreaHeight - ((avg - minPrice) / priceRange * priceAreaHeight);

      if (!maStarted) {
        maPath.moveTo(x, y);
        maStarted = true;
      } else {
        maPath.lineTo(x, y);
      }
    }
    canvas.drawPath(maPath, maPaint);

    // 6. Selected Candle Crosshair
    if (selectedIndex != null && selectedIndex! < candles.length) {
      final double cx = (selectedIndex! * candleStep) + (candleStep / 2);
      final crossPaint = Paint()
        ..color = Colors.white.withValues(alpha: 0.40)
        ..strokeWidth = 0.8;
      canvas.drawLine(Offset(cx, 0), Offset(cx, priceAreaHeight), crossPaint);
    }

    // 7. Live Price Line, Right Pill & Pulsing Beacon Dot
    final lastCandle = candles.last;
    final double liveCloseY = priceAreaHeight - ((lastCandle.close - minPrice) / priceRange * priceAreaHeight);
    final double lastCandleX = ((candles.length - 1) * candleStep) + (candleStep / 2);
    final Color liveColor = lastCandle.isBullish ? AppColors.bullish : AppColors.bearish;

    // Horizontal dashed line across chart
    final liveLinePaint = Paint()
      ..color = liveColor.withValues(alpha: 0.65)
      ..strokeWidth = 1.0;
    _drawDashedLine(canvas, Offset(0, liveCloseY), Offset(chartWidth, liveCloseY), liveLinePaint, dashWidth: 5, dashSpace: 3);

    // Live Price Pill on Right Axis
    final pillRect = RRect.fromRectAndRadius(
      Rect.fromCenter(center: Offset(chartWidth + 30, liveCloseY), width: 56, height: 18),
      const Radius.circular(4),
    );
    canvas.drawRRect(pillRect, Paint()..color = liveColor);

    final livePriceText = TextSpan(
      text: lastCandle.close.toStringAsFixed(2),
      style: const TextStyle(
        color: Colors.black,
        fontSize: 9.5,
        fontWeight: FontWeight.w900,
        fontFamily: 'monospace',
      ),
    );
    final livePricePainter = TextPainter(text: livePriceText, textDirection: ui.TextDirection.ltr)..layout();
    livePricePainter.paint(
      canvas,
      Offset(chartWidth + 30 - (livePricePainter.width / 2), liveCloseY - (livePricePainter.height / 2)),
    );

    // Live Beacon Dot on last candle close
    canvas.drawCircle(Offset(lastCandleX, liveCloseY), 3.5, Paint()..color = liveColor);
    canvas.drawCircle(
      Offset(lastCandleX, liveCloseY),
      7.0,
      Paint()
        ..color = liveColor.withValues(alpha: 0.35)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.4,
    );

    // 8. Draw AI Trade Setup Overlay Levels (SL, Entry, TP1, TP2)
    if (showTradeSetupOverlay && tradeSetup != null && tradeSetup!.entryPrice > 0) {
      final double? eY = _getY(tradeSetup!.entryPrice, minPrice, priceRange, priceAreaHeight);
      final double? tp2Y = _getY(tradeSetup!.takeProfit2, minPrice, priceRange, priceAreaHeight);
      final double? slY = _getY(tradeSetup!.stopLoss, minPrice, priceRange, priceAreaHeight);

      if (eY != null && tp2Y != null) {
        final tpRect = Rect.fromLTRB(0, min(eY, tp2Y), chartWidth, max(eY, tp2Y));
        canvas.drawRect(tpRect, Paint()..color = AppColors.bullish.withValues(alpha: 0.05));
      }
      if (eY != null && slY != null) {
        final slRect = Rect.fromLTRB(0, min(eY, slY), chartWidth, max(eY, slY));
        canvas.drawRect(slRect, Paint()..color = AppColors.bearish.withValues(alpha: 0.05));
      }

      _drawTradeSetupLevel(canvas, chartWidth, priceAreaHeight, minPrice, priceRange,
          price: tradeSetup!.stopLoss, label: 'SL', color: AppColors.bearish);
      _drawTradeSetupLevel(canvas, chartWidth, priceAreaHeight, minPrice, priceRange,
          price: tradeSetup!.entryPrice, label: 'ENTRY', color: const Color(0xFF2979FF));
      _drawTradeSetupLevel(canvas, chartWidth, priceAreaHeight, minPrice, priceRange,
          price: tradeSetup!.takeProfit1, label: 'TP1', color: AppColors.bullish);
      _drawTradeSetupLevel(canvas, chartWidth, priceAreaHeight, minPrice, priceRange,
          price: tradeSetup!.takeProfit2, label: 'TP2', color: const Color(0xFF00E676));
    }
  }

  double? _getY(double price, double minPrice, double priceRange, double priceAreaHeight) {
    if (price <= 0 || priceRange <= 0) return null;
    return priceAreaHeight - ((price - minPrice) / priceRange * priceAreaHeight);
  }

  void _drawTradeSetupLevel(
    Canvas canvas,
    double chartWidth,
    double priceAreaHeight,
    double minPrice,
    double priceRange, {
    required double price,
    required String label,
    required Color color,
  }) {
    if (price <= 0) return;
    final double? y = _getY(price, minPrice, priceRange, priceAreaHeight);
    if (y == null || y < -10 || y > priceAreaHeight + 10) return;

    // Dashed horizontal level line
    final linePaint = Paint()
      ..color = color.withValues(alpha: 0.85)
      ..strokeWidth = 1.1;
    _drawDashedLine(canvas, Offset(0, y), Offset(chartWidth, y), linePaint, dashWidth: 4, dashSpace: 3);

    // Right-Axis Pill Badge
    final badgeRect = RRect.fromRectAndRadius(
      Rect.fromCenter(center: Offset(chartWidth + 30, y), width: 58, height: 16),
      const Radius.circular(3.5),
    );
    canvas.drawRRect(badgeRect, Paint()..color = color);

    final textSpan = TextSpan(
      text: '$label ${price.toStringAsFixed(1)}',
      style: const TextStyle(
        color: Colors.black,
        fontSize: 8.5,
        fontWeight: FontWeight.w900,
        fontFamily: 'monospace',
      ),
    );
    final painter = TextPainter(text: textSpan, textDirection: ui.TextDirection.ltr)..layout();
    painter.paint(canvas, Offset(chartWidth + 30 - (painter.width / 2), y - (painter.height / 2)));
  }

  void _drawDashedLine(Canvas canvas, Offset start, Offset end, Paint paint, {double dashWidth = 5, double dashSpace = 4}) {
    double currentX = start.dx;
    while (currentX < end.dx) {
      canvas.drawLine(
        Offset(currentX, start.dy),
        Offset(min(currentX + dashWidth, end.dx), start.dy),
        paint,
      );
      currentX += dashWidth + dashSpace;
    }
  }

  @override
  bool shouldRepaint(covariant _PureCandlePainter oldDelegate) {
    if (selectedIndex != oldDelegate.selectedIndex) return true;
    if (showTradeSetupOverlay != oldDelegate.showTradeSetupOverlay) return true;
    if (tradeSetup != oldDelegate.tradeSetup) return true;
    if (candles.length != oldDelegate.candles.length) return true;
    if (candles.isNotEmpty && oldDelegate.candles.isNotEmpty) {
      if (candles.last.close != oldDelegate.candles.last.close) return true;
    }
    return false;
  }
}
