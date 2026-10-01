import 'package:flutter/cupertino.dart';
import '../../core/constants/app_colors.dart';
import '../../data/models/trade_setup_model.dart';
import 'ios_glass_card.dart';

class TradeSetupCard extends StatefulWidget {
  final TradeSetupModel setup;
  final VoidCallback? onViewOnChart;
  final VoidCallback? onViewChart;

  const TradeSetupCard({
    super.key,
    required this.setup,
    this.onViewOnChart,
    this.onViewChart,
  });

  @override
  State<TradeSetupCard> createState() => _TradeSetupCardState();
}

class _TradeSetupCardState extends State<TradeSetupCard> {
  bool _isRationaleExpanded = true;

  @override
  Widget build(BuildContext context) {
    final s = widget.setup;
    final isBuy = s.action.toUpperCase() == 'BUY';
    final isSell = s.action.toUpperCase() == 'SELL';

    final Color actionColor = isBuy
        ? AppColors.bullish
        : (isSell ? AppColors.bearish : AppColors.neutral);

    final IconData actionIcon = isBuy
        ? CupertinoIcons.arrow_up_right_circle_fill
        : (isSell
            ? CupertinoIcons.arrow_down_right_circle_fill
            : CupertinoIcons.pause_circle_fill);

    return IosGlassCard(
      borderRadius: 24,
      padding: const EdgeInsets.all(18),
      borderColor: actionColor.withValues(alpha: 0.35),
      glowColor: actionColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Header Row: Badge & RRR
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Row(
                  children: [
                    Icon(actionIcon, color: actionColor, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        s.actionLabel,
                        style: TextStyle(
                          color: actionColor,
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
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3.5),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.primary.withValues(alpha: 0.4), width: 0.8),
                ),
                child: Text(
                  'RRR ${s.riskRewardRatio}',
                  style: const TextStyle(
                    color: AppColors.primary,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    fontFamily: 'monospace',
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Lifecycle & Persistence Status Pill
          Builder(
            builder: (context) {
              final setupStatus = s.safeStatus.toUpperCase();
              final setupMessage = s.safeStatusMessage;
              final isTp1 = setupStatus.contains('TP1');
              final isStop = setupStatus.contains('STOP');

              final Color statusColor = isTp1
                  ? AppColors.bullish
                  : (isStop ? AppColors.bearish : const Color(0xFF2979FF));

              final IconData statusIcon = isTp1
                  ? CupertinoIcons.check_mark_circled_solid
                  : (isStop
                      ? CupertinoIcons.exclamationmark_octagon_fill
                      : CupertinoIcons.lock_shield_fill);

              return Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6.5),
                decoration: BoxDecoration(
                  color: const Color(0x351F2636),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: statusColor.withValues(alpha: 0.35),
                    width: 0.8,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(statusIcon, color: statusColor, size: 14),
                    const SizedBox(width: 7),
                    Expanded(
                      child: Text(
                        setupMessage,
                        style: TextStyle(
                          color: isTp1 || isStop ? statusColor : AppColors.textPrimary,
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
          const SizedBox(height: 14),

          // 2. 4-Box Grid: Entry Zone, SL, TP1, TP2
          Row(
            children: [
              Expanded(
                child: _buildMetricTile(
                  label: 'ZONA ENTRY',
                  value: s.entryZone.isNotEmpty ? s.entryZone : '\$${s.entryPrice.toStringAsFixed(2)}',
                  subValue: 'Titik Acuan: \$${s.entryPrice.toStringAsFixed(2)}',
                  valueColor: AppColors.textPrimary,
                  accentColor: const Color(0xFF2979FF),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildMetricTile(
                  label: 'STOP LOSS (SL)',
                  value: '\$${s.stopLoss.toStringAsFixed(2)}',
                  subValue: s.riskPips > 0 ? '-${s.riskPips.toStringAsFixed(0)} pips / Risk' : 'Proteksi Batas',
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
                  label: 'TARGET TP 1',
                  value: '\$${s.takeProfit1.toStringAsFixed(2)}',
                  subValue: s.rewardTp1Pips > 0 ? '+${s.rewardTp1Pips.toStringAsFixed(0)} pips (Kunci 50% & BE)' : 'Batas 1',
                  valueColor: AppColors.bullish,
                  accentColor: AppColors.bullish,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildMetricTile(
                  label: 'TARGET TP 2',
                  value: '\$${s.takeProfit2.toStringAsFixed(2)}',
                  subValue: s.rewardTp2Pips > 0 ? '+${s.rewardTp2Pips.toStringAsFixed(0)} pips (Ekspansi)' : 'Batas 2',
                  valueColor: AppColors.bullish,
                  accentColor: AppColors.bullish,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // 3. Technical & News Synthesis Rationale Box
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0x351F2636),
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
                      _isRationaleExpanded = !_isRationaleExpanded;
                    });
                  },
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Expanded(
                        child: Row(
                          children: [
                            Icon(CupertinoIcons.chart_bar_alt_fill, color: AppColors.primary, size: 14),
                            SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                'RASIONAL TEKNIKAL & KATALIS NEWS',
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
                        _isRationaleExpanded ? CupertinoIcons.chevron_up : CupertinoIcons.chevron_down,
                        color: AppColors.textTertiary,
                        size: 13,
                      ),
                    ],
                  ),
                ),
                if (_isRationaleExpanded) ...[
                  const SizedBox(height: 8),
                  Text(
                    s.technicalRationale,
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 12.5,
                      height: 1.45,
                    ),
                  ),
                  if (s.invalidationLevel.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: AppColors.bearish.withValues(alpha: 0.10),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppColors.bearish.withValues(alpha: 0.25)),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(CupertinoIcons.exclamationmark_circle_fill, color: AppColors.bearish, size: 13),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              'Level Pembatalan: ${s.invalidationLevel}',
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
              ],
            ),
          ),

          // 4. TradingView Context Banner or Action
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
            decoration: BoxDecoration(
              color: const Color(0x251F2636),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.borderSubtle),
            ),
            child: const Row(
              children: [
                Icon(CupertinoIcons.chart_bar_alt_fill, color: Color(0xFF10B981), size: 14),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Level Entry, SL, TP1, dan TP2 di atas disintesis otomatis dari pembacaan chart TradingView & katalis ekonomi real-time.',
                    style: TextStyle(color: AppColors.textMuted, fontSize: 11, height: 1.35),
                  ),
                ),
              ],
            ),
          ),
          if (widget.onViewChart != null || widget.onViewOnChart != null) ...[
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: CupertinoButton(
                padding: const EdgeInsets.symmetric(vertical: 10),
                color: const Color(0xFF1E2433),
                borderRadius: BorderRadius.circular(12),
                onPressed: widget.onViewChart ?? widget.onViewOnChart,
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(CupertinoIcons.waveform_path, color: AppColors.primary, size: 16),
                    SizedBox(width: 8),
                    Text(
                      'Buka Chart TradingView Interaktif',
                      style: TextStyle(
                        color: AppColors.primary,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    SizedBox(width: 4),
                    Icon(CupertinoIcons.chevron_right, color: AppColors.primary, size: 13),
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
    required String subValue,
    required Color valueColor,
    required Color accentColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
      decoration: BoxDecoration(
        color: const Color(0x351F2636),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.borderSubtle),
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
              const SizedBox(width: 5),
              Text(
                label,
                style: const TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 9.5,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.4,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              style: TextStyle(
                color: valueColor,
                fontSize: 14,
                fontWeight: FontWeight.w800,
                fontFamily: 'monospace',
                letterSpacing: -0.2,
              ),
            ),
          ),
          const SizedBox(height: 2),
          Text(
            subValue,
            style: const TextStyle(
              color: AppColors.textMuted,
              fontSize: 10,
              height: 1.2,
            ),
          ),
        ],
      ),
    );
  }
}
