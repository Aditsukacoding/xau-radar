import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import 'tradingview_embed.dart' as tv_embed;

class TradingViewChartWidget extends StatefulWidget {
  final String symbol;
  final String activeTimeframe;
  final ValueChanged<String>? onTimeframeChanged;

  const TradingViewChartWidget({
    super.key,
    this.symbol = 'FOREXCOM:XAUUSD',
    this.activeTimeframe = '1h',
    this.onTimeframeChanged,
  });

  @override
  State<TradingViewChartWidget> createState() => _TradingViewChartWidgetState();
}

class _TradingViewChartWidgetState extends State<TradingViewChartWidget> {
  late String _currentTimeframe;
  final List<String> _timeframes = ['1m', '5m', '15m', '1h', '4h', '1D'];

  @override
  void initState() {
    super.initState();
    _currentTimeframe = widget.activeTimeframe;
  }

  @override
  void didUpdateWidget(covariant TradingViewChartWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.activeTimeframe != widget.activeTimeframe) {
      _currentTimeframe = widget.activeTimeframe;
    }
  }

  void _setTimeframe(String tf) {
    if (_currentTimeframe != tf) {
      setState(() {
        _currentTimeframe = tf;
      });
      widget.onTimeframeChanged?.call(tf);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: const Color(0xFF131722),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withValues(alpha: 0.12)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.45),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xFF1C2030),
              border: Border(
                bottom: BorderSide(color: Colors.white.withValues(alpha: 0.08)),
              ),
            ),
            child: Row(
              children: [
                // Symbol Badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppColors.primary.withValues(alpha: 0.4)),
                  ),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(CupertinoIcons.chart_bar_square, size: 13, color: AppColors.primary),
                      SizedBox(width: 5),
                      Text(
                        'XAU/USD',
                        style: TextStyle(
                          color: AppColors.primary,
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.5,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),

                // Source indicator (FOREX.com)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: const Color(0x2010B981),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: const Color(0x6010B981)),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.circle, size: 7, color: Color(0xFF10B981)),
                      SizedBox(width: 4),
                      Text(
                        'FOREX.com • Gold Spot / U.S. Dollar',
                        style: TextStyle(
                          color: Color(0xFF10B981),
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                const Text(
                  'Real-Time',
                  style: TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),

          // Timeframe Ribbon
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            color: const Color(0xFF161A25),
            child: Row(
              children: [
                const Text(
                  'TF:',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 11, fontWeight: FontWeight.bold),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: _timeframes.map((tf) {
                        final isSelected = _currentTimeframe == tf;
                        return Padding(
                          padding: const EdgeInsets.only(right: 6),
                          child: InkWell(
                            onTap: () => _setTimeframe(tf),
                            borderRadius: BorderRadius.circular(6),
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 150),
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: isSelected
                                    ? AppColors.primary.withValues(alpha: 0.25)
                                    : Colors.white.withValues(alpha: 0.04),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                  color: isSelected ? AppColors.primary : Colors.white.withValues(alpha: 0.08),
                                  width: 1,
                                ),
                              ),
                              child: Text(
                                tf,
                                style: TextStyle(
                                  color: isSelected ? Colors.white : AppColors.textMuted,
                                  fontSize: 11,
                                  fontWeight: isSelected ? FontWeight.w800 : FontWeight.w500,
                                ),
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ),
                const SizedBox(width: 4),
                const Text(
                  'Detik/Realtime',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 10, fontStyle: FontStyle.italic),
                ),
              ],
            ),
          ),

          // TradingView Embedded Chart
          SizedBox(
            height: 490,
            width: double.infinity,
            key: ValueKey('tv-${widget.symbol}-$_currentTimeframe'),
            child: tv_embed.buildTradingViewWidget(
              symbol: widget.symbol,
              interval: _currentTimeframe,
              height: 490,
            ),
          ),
        ],
      ),
    );
  }
}
