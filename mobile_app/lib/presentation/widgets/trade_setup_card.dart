import 'package:flutter/cupertino.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../core/constants/app_colors.dart';
import '../../core/theme/app_theme.dart';
import '../../data/models/trade_setup_model.dart';
import 'ios_glass_card.dart';

class TradeSetupCard extends StatefulWidget {
  final TradeSetupModel setup;
  final VoidCallback? onViewOnChart;
  final VoidCallback? onViewChart;
  final bool initiallyExpanded;

  const TradeSetupCard({
    super.key,
    required this.setup,
    this.onViewOnChart,
    this.onViewChart,
    this.initiallyExpanded = false,
  });

  @override
  State<TradeSetupCard> createState() => _TradeSetupCardState();
}

class _TradeSetupCardState extends State<TradeSetupCard> {
  late bool _isRationaleExpanded;

  @override
  void initState() {
    super.initState();
    _isRationaleExpanded = widget.initiallyExpanded;
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.setup;
    final isBuy = s.action.toUpperCase() == 'BUY';
    final isSell = s.action.toUpperCase() == 'SELL';

    final Color actionColor = isBuy
        ? AppColors.bullish
        : (isSell ? AppColors.bearish : AppColors.gold);

    final String shortBadge = isBuy
        ? (s.actionLabel.toUpperCase().contains('LIMIT') ? 'BUY LIMIT' : 'BUY SETUP')
        : (isSell
            ? (s.actionLabel.toUpperCase().contains('LIMIT') ? 'SELL LIMIT' : 'SELL SETUP')
            : 'WAIT');

    return IosGlassCard(
      borderRadius: 20,
      padding: const EdgeInsets.all(18),
      borderColor: actionColor.withValues(alpha: 0.22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Clean Institutional Header Row: Title + RRR & Action Badges
          Row(
            children: [
              Container(
                width: 7,
                height: 7,
                decoration: BoxDecoration(
                  color: AppColors.gold,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(color: AppColors.gold.withValues(alpha: 0.5), blurRadius: 6),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'RADAR TRADE SETUP',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.7,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 6),
              // RRR Pill (Sky Cyan Monospace)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                decoration: BoxDecoration(
                  color: AppColors.cyan.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.cyan.withValues(alpha: 0.30), width: 0.8),
                ),
                child: Text(
                  'RRR ${s.riskRewardRatio}',
                  style: AppTypography.mono(
                    color: AppColors.cyan,
                    fontSize: 10,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const SizedBox(width: 6),
              // Action Pill (BUY / SELL)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                decoration: BoxDecoration(
                  color: actionColor.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: actionColor.withValues(alpha: 0.38), width: 0.8),
                ),
                child: Text(
                  shortBadge,
                  style: TextStyle(
                    color: actionColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.4,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Compact Lifecycle Status Strip
          Builder(
            builder: (context) {
              final setupStatus = s.safeStatus.toUpperCase();
              final setupMessage = s.safeStatusMessage;
              final isTp1 = setupStatus.contains('TP1');
              final isStop = setupStatus.contains('STOP');

              final Color statusColor = isTp1
                  ? AppColors.bullish
                  : (isStop ? AppColors.bearish : AppColors.cyan);

              final IconData statusIcon = isTp1
                  ? LucideIcons.circleCheck
                  : (isStop
                      ? LucideIcons.octagonAlert
                      : LucideIcons.shieldCheck);

              return Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
                decoration: BoxDecoration(
                  color: AppColors.surfaceInset,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: statusColor.withValues(alpha: 0.22), width: 0.8),
                ),
                child: Row(
                  children: [
                    Icon(statusIcon, color: statusColor, size: 13),
                    const SizedBox(width: 7),
                    Expanded(
                      child: Text(
                        setupMessage,
                        style: TextStyle(
                          color: isTp1 || isStop ? statusColor : AppColors.textSecondary,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 14),

          // 2. Precision 2x2 Grid: Zona Entri, Stop Loss, TP1, TP2
          Row(
            children: [
              Expanded(
                child: _buildMetricTile(
                  label: 'ZONA ENTRI',
                  value: s.entryZone.isNotEmpty ? s.entryZone : '\$${s.entryPrice.toStringAsFixed(2)}',
                  pipBadge: 'Acuan \$${s.entryPrice.toStringAsFixed(1)}',
                  valueColor: AppColors.textPrimary,
                  accentColor: AppColors.cyan,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildMetricTile(
                  label: 'STOP LOSS',
                  value: '\$${s.stopLoss.toStringAsFixed(2)}',
                  pipBadge: s.riskPips > 0 ? '-${s.riskPips.toStringAsFixed(0)} pips' : 'Risk Guard',
                  valueColor: AppColors.bearish,
                  accentColor: AppColors.bearish,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _buildMetricTile(
                  label: 'TAKE PROFIT 1',
                  value: '\$${s.takeProfit1.toStringAsFixed(2)}',
                  pipBadge: s.rewardTp1Pips > 0 ? '+${s.rewardTp1Pips.toStringAsFixed(0)} pips' : 'Target 1',
                  valueColor: AppColors.bullish,
                  accentColor: AppColors.bullish,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildMetricTile(
                  label: 'TAKE PROFIT 2',
                  value: '\$${s.takeProfit2.toStringAsFixed(2)}',
                  pipBadge: s.rewardTp2Pips > 0 ? '+${s.rewardTp2Pips.toStringAsFixed(0)} pips' : 'Ekspansi',
                  valueColor: AppColors.gold,
                  accentColor: AppColors.gold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // 3. Clean Accordion: "Rasional Eksekusi Setup"
          Container(
            decoration: BoxDecoration(
              color: AppColors.surfaceInset,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border, width: 0.8),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () {
                    setState(() {
                      _isRationaleExpanded = !_isRationaleExpanded;
                    });
                  },
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Expanded(
                          child: Row(
                            children: [
                              Icon(LucideIcons.fileSearch, color: AppColors.gold, size: 14),
                              SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Rasional Eksekusi Setup',
                                  style: TextStyle(
                                    color: AppColors.textSecondary,
                                    fontSize: 12,
                                    fontWeight: FontWeight.w700,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Icon(
                          _isRationaleExpanded ? LucideIcons.chevronUp : LucideIcons.chevronDown,
                          color: AppColors.textMuted,
                          size: 13,
                        ),
                      ],
                    ),
                  ),
                ),
                if (_isRationaleExpanded) ...[
                  Container(height: 0.8, color: AppColors.borderSubtle),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(14, 10, 14, 14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          s.technicalRationale,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12.5,
                            height: 1.5,
                          ),
                        ),
                        if (s.invalidationLevel.isNotEmpty) ...[
                          const SizedBox(height: 10),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
                            decoration: BoxDecoration(
                              color: AppColors.bearish.withValues(alpha: 0.10),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: AppColors.bearish.withValues(alpha: 0.25), width: 0.8),
                            ),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(LucideIcons.circleAlert, color: AppColors.bearish, size: 13),
                                const SizedBox(width: 6),
                                Expanded(
                                  child: Text(
                                    'Invalidasi: ${s.invalidationLevel}',
                                    style: const TextStyle(
                                      color: AppColors.bearish,
                                      fontSize: 11,
                                      height: 1.35,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),

          if (widget.onViewChart != null || widget.onViewOnChart != null) ...[
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: CupertinoButton(
                padding: const EdgeInsets.symmetric(vertical: 11),
                color: AppColors.surfaceElevated,
                borderRadius: BorderRadius.circular(12),
                onPressed: widget.onViewChart ?? widget.onViewOnChart,
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(LucideIcons.chartCandlestick, color: AppColors.gold, size: 14),
                    SizedBox(width: 7),
                    Text(
                      'Lihat Chart TradingView',
                      style: TextStyle(
                        color: AppColors.gold,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    SizedBox(width: 4),
                    Icon(LucideIcons.chevronRight, color: AppColors.gold, size: 12),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMetricTile({
    required String label,
    required String value,
    required String pipBadge,
    required Color valueColor,
    required Color accentColor,
  }) {
    return Container(
      padding: const EdgeInsets.all(13),
      decoration: BoxDecoration(
        color: AppColors.surfaceInset,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                  color: accentColor,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(
                    color: AppColors.textMuted,
                    fontSize: 9.5,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 7),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              style: AppTypography.mono(
                color: valueColor,
                fontSize: 15,
                fontWeight: FontWeight.w700,
                letterSpacing: -0.3,
              ),
            ),
          ),
          const SizedBox(height: 5),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: accentColor.withValues(alpha: 0.11),
              borderRadius: BorderRadius.circular(5),
            ),
            child: Text(
              pipBadge,
              style: AppTypography.mono(
                color: accentColor,
                fontSize: 9.5,
                fontWeight: FontWeight.w600,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
