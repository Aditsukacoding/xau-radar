import 'package:flutter/cupertino.dart';
import '../../core/constants/app_colors.dart';
import 'ios_glass_card.dart';

class MarketAnalysisCard extends StatefulWidget {
  final String bias;
  final int confidenceScore;
  final String trendDirection;
  final double? rsi;
  final String? rsiCondition;
  final List<double> supportLevels;
  final List<double> resistanceLevels;
  final String? summary;
  final String? technicalRationale;
  final String? upcomingEventTitle;
  final String? upcomingEventTime;

  const MarketAnalysisCard({
    super.key,
    required this.bias,
    this.confidenceScore = 75,
    this.trendDirection = 'BULLISH',
    this.rsi,
    this.rsiCondition,
    this.supportLevels = const [],
    this.resistanceLevels = const [],
    this.summary,
    this.technicalRationale,
    this.upcomingEventTitle,
    this.upcomingEventTime,
  });

  @override
  State<MarketAnalysisCard> createState() => _MarketAnalysisCardState();
}

class _MarketAnalysisCardState extends State<MarketAnalysisCard> {
  bool _isExpanded = true;

  @override
  Widget build(BuildContext context) {
    final isBullish = widget.bias.toUpperCase() == 'BULLISH';
    final isBearish = widget.bias.toUpperCase() == 'BEARISH';

    final Color biasColor = isBullish
        ? AppColors.bullish
        : (isBearish ? AppColors.bearish : AppColors.neutral);

    final IconData biasIcon = isBullish
        ? CupertinoIcons.arrow_up_right_circle_fill
        : (isBearish
            ? CupertinoIcons.arrow_down_right_circle_fill
            : CupertinoIcons.pause_circle_fill);

    return IosGlassCard(
      borderRadius: 22,
      padding: const EdgeInsets.all(18),
      borderColor: biasColor.withValues(alpha: 0.35),
      glowColor: biasColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Header: Bias Badge & Key Confidence / Status
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Row(
                  children: [
                    Icon(biasIcon, color: biasColor, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'BIAS PASAR: ${widget.bias.toUpperCase()}',
                        style: TextStyle(
                          color: biasColor,
                          fontSize: 13,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.5,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: biasColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: biasColor.withValues(alpha: 0.4), width: 0.8),
                ),
                child: Text(
                  '${widget.confidenceScore}% KEYAKINAN',
                  style: TextStyle(
                    color: biasColor,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    fontFamily: 'monospace',
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // 2. Ringkasan Arah Analisa Pasar
          if (widget.summary != null && widget.summary!.isNotEmpty) ...[
            Text(
              widget.summary!,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 13.5,
                fontWeight: FontWeight.w500,
                height: 1.45,
              ),
            ),
            const SizedBox(height: 14),
          ],

          // 3. Level Acuan Nyata di Chart TradingView (Support & Resistance)
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0x351F2636),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.borderSubtle),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(CupertinoIcons.arrow_down_to_line, size: 12, color: AppColors.bullish),
                          SizedBox(width: 4),
                          Text(
                            'SUPPORT DI CHART',
                            style: TextStyle(color: AppColors.textMuted, fontSize: 9.5, fontWeight: FontWeight.w700),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      FittedBox(
                        fit: BoxFit.scaleDown,
                        alignment: Alignment.centerLeft,
                        child: Text(
                          widget.supportLevels.isNotEmpty
                              ? widget.supportLevels.take(2).map((s) => '\$${s.toStringAsFixed(1)}').join(' • ')
                              : 'Mengikuti Chart',
                          style: const TextStyle(
                            color: AppColors.bullish,
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            fontFamily: 'monospace',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                Container(width: 1, height: 28, color: AppColors.borderSubtle),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(CupertinoIcons.arrow_up_to_line, size: 12, color: AppColors.bearish),
                          SizedBox(width: 4),
                          Text(
                            'RESISTANCE DI CHART',
                            style: TextStyle(color: AppColors.textMuted, fontSize: 9.5, fontWeight: FontWeight.w700),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      FittedBox(
                        fit: BoxFit.scaleDown,
                        alignment: Alignment.centerLeft,
                        child: Text(
                          widget.resistanceLevels.isNotEmpty
                              ? widget.resistanceLevels.take(2).map((r) => '\$${r.toStringAsFixed(1)}').join(' • ')
                              : 'Mengikuti Chart',
                          style: const TextStyle(
                            color: AppColors.bearish,
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            fontFamily: 'monospace',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // 4. Panduan Praktis untuk Scalper & Day Trader
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0x25141926),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.borderSubtle),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () {
                    setState(() {
                      _isExpanded = !_isExpanded;
                    });
                  },
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Expanded(
                        child: Row(
                          children: [
                            Icon(CupertinoIcons.bolt_fill, color: AppColors.primary, size: 13),
                            SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                'PANDUAN AKSI SCALPING & INTRADAY',
                                style: TextStyle(
                                  color: AppColors.primary,
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 0.5,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Icon(
                        _isExpanded ? CupertinoIcons.chevron_up : CupertinoIcons.chevron_down,
                        color: AppColors.textTertiary,
                        size: 13,
                      ),
                    ],
                  ),
                ),
                if (_isExpanded) ...[
                  const SizedBox(height: 10),
                  Text(
                    widget.technicalRationale != null && widget.technicalRationale!.isNotEmpty
                        ? widget.technicalRationale!
                        : (isBullish
                            ? 'Amati aksi harga di chart TradingView saat menguji area Support. Scalper dapat mencari konfirmasi pantulan bullish pada timeframe M1/M5 dengan target terdekat ke area Resistance.'
                            : (isBearish
                                ? 'Amati penolakan harga di dekat Resistance. Scalper dapat mencari konfirmasi penurunan saat momentum melemah dengan target Support terdekat.'
                                : 'Pasar berada dalam fase konsolidasi/sideways. Scalper disarankan bermain cepat di rentang Support-Resistance atau menunggu rilis katalis berita.')),
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                      height: 1.45,
                    ),
                  ),
                  if (widget.upcomingEventTitle != null && widget.upcomingEventTitle!.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(CupertinoIcons.exclamationmark_triangle_fill, size: 12, color: AppColors.impactHigh),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            'Waspadai Katalis: ${widget.upcomingEventTitle} (${widget.upcomingEventTime ?? 'Hari Ini'})',
                            style: const TextStyle(color: AppColors.impactHigh, fontSize: 11, fontWeight: FontWeight.w600),
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}
