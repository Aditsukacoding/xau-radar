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
    final isInstant = s.executionType.toUpperCase() == 'INSTANT';

    final Color actionColor = isBuy
        ? AppColors.bullish
        : (isSell ? AppColors.bearish : AppColors.gold);

    final String shortBadge = isBuy
        ? (isInstant ? 'BUY NOW' : 'BUY LIMIT')
        : (isSell ? (isInstant ? 'SELL NOW' : 'SELL LIMIT') : 'WAIT');

    return IosGlassCard(
      borderRadius: 20,
      padding: const EdgeInsets.all(18),
      borderColor: actionColor.withValues(alpha: 0.24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 1. Institutional Header Row: Title + RRR & Action Badges
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
                  'RADAR SCALP SETUP',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.6,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              const SizedBox(width: 6),
              // RRR Pill
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
              // Action Pill (BUY NOW / SELL NOW / LIMIT)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8.5, vertical: 3.5),
                decoration: BoxDecoration(
                  color: actionColor.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: actionColor.withValues(alpha: 0.45), width: 0.9),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (isInstant && (isBuy || isSell)) ...[
                      Icon(LucideIcons.zap, color: actionColor, size: 10),
                      const SizedBox(width: 3),
                    ],
                    Text(
                      shortBadge,
                      style: TextStyle(
                        color: actionColor,
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Meta Context Chips (Timeframe + Session + ATR)
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _buildMetaPill(LucideIcons.clock, s.scalpTimeframe, AppColors.gold),
              if (s.sessionName.isNotEmpty)
                _buildMetaPill(LucideIcons.globe, s.sessionName, AppColors.textSecondary),
              if (s.atrPips > 0)
                _buildMetaPill(LucideIcons.activity, 'ATR ${s.atrPips.toStringAsFixed(0)}p', AppColors.cyan),
            ],
          ),
          const SizedBox(height: 10),

          // Compact Lifecycle Status Strip (ACTIVE / TP1 HIT / TP2 HIT)
          Builder(
            builder: (context) {
              final setupStatus = s.safeStatus.toUpperCase();
              final setupMessage = s.safeStatusMessage;
              final isTpHit = setupStatus.contains('TP1') || setupStatus.contains('TP2');
              final isStop = setupStatus.contains('STOP');

              final Color statusColor = isTpHit
                  ? AppColors.bullish
                  : (isStop ? AppColors.bearish : AppColors.cyan);

              final IconData statusIcon = isTpHit
                  ? LucideIcons.circleCheck
                  : (isStop ? LucideIcons.octagonAlert : LucideIcons.shieldCheck);

              return Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7.5),
                decoration: BoxDecoration(
                  color: AppColors.surfaceInset,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: statusColor.withValues(alpha: 0.24), width: 0.8),
                ),
                child: Row(
                  children: [
                    Icon(statusIcon, color: statusColor, size: 13.5),
                    const SizedBox(width: 7),
                    Expanded(
                      child: Text(
                        setupMessage,
                        style: TextStyle(
                          color: isTpHit || isStop ? statusColor : AppColors.textSecondary,
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

          // 2. Top 2-Column Row: ZONA ENTRI & STOP LOSS
          Row(
            children: [
              Expanded(
                child: _buildPrimaryTile(
                  label: 'ZONA ENTRI',
                  value: s.entryZone.isNotEmpty ? s.entryZone : '\$${s.entryPrice.toStringAsFixed(2)}',
                  badge: '${isInstant ? 'Market' : 'Acuan'} \$${s.entryPrice.toStringAsFixed(2)}',
                  valueColor: AppColors.textPrimary,
                  accentColor: AppColors.cyan,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildPrimaryTile(
                  label: 'STOP LOSS (SL)',
                  value: '\$${s.stopLoss.toStringAsFixed(2)}',
                  badge: s.riskPips > 0 ? '-${s.riskPips.toStringAsFixed(0)} pips' : 'Risk Guard',
                  valueColor: AppColors.bearish,
                  accentColor: AppColors.bearish,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // 3. 3-Column Target Scaling Ladder: TP1 (40%) | TP2 (40%) | TP3 (20%)
          Row(
            children: [
              Expanded(
                child: _buildTargetTile(
                  tier: 'TP 1',
                  lotPct: '40%',
                  value: '\$${s.takeProfit1.toStringAsFixed(2)}',
                  pips: s.rewardTp1Pips > 0 ? '+${s.rewardTp1Pips.toStringAsFixed(0)}p' : 'Quick',
                  actionHint: 'SL → BEP',
                  accentColor: AppColors.bullish,
                  isHit: s.safeStatus.toUpperCase().contains('TP1') || s.safeStatus.toUpperCase().contains('TP2'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildTargetTile(
                  tier: 'TP 2',
                  lotPct: '40%',
                  value: '\$${s.takeProfit2.toStringAsFixed(2)}',
                  pips: s.rewardTp2Pips > 0 ? '+${s.rewardTp2Pips.toStringAsFixed(0)}p' : 'Main',
                  actionHint: 'SL → TP1',
                  accentColor: AppColors.bullish,
                  isHit: s.safeStatus.toUpperCase().contains('TP2'),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildTargetTile(
                  tier: 'TP 3',
                  lotPct: '20%',
                  value: '\$${s.takeProfit3.toStringAsFixed(2)}',
                  pips: s.rewardTp3Pips > 0 ? '+${s.rewardTp3Pips.toStringAsFixed(0)}p' : 'Runner',
                  actionHint: 'Runner',
                  accentColor: AppColors.gold,
                  isHit: false,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Lot Management Strip
          if (s.lotManagement.isNotEmpty) ...[
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
              decoration: BoxDecoration(
                color: AppColors.gold.withValues(alpha: 0.07),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.gold.withValues(alpha: 0.20), width: 0.7),
              ),
              child: Row(
                children: [
                  const Icon(LucideIcons.layers, color: AppColors.gold, size: 12.5),
                  const SizedBox(width: 7),
                  Expanded(
                    child: Text(
                      s.lotManagement,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
          ],

          // 4. Accordion: "Rasional Eksekusi Setup"
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

  Widget _buildMetaPill(IconData icon, String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7.5, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.surfaceInset,
        borderRadius: BorderRadius.circular(7),
        border: Border.all(color: AppColors.border, width: 0.7),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 10.5),
          const SizedBox(width: 4),
          Text(
            text,
            style: TextStyle(
              color: color,
              fontSize: 10,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPrimaryTile({
    required String label,
    required String value,
    required String badge,
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
                decoration: BoxDecoration(color: accentColor, shape: BoxShape.circle),
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
                fontSize: 14.5,
                fontWeight: FontWeight.w700,
                letterSpacing: -0.2,
              ),
            ),
          ),
          const SizedBox(height: 5),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: accentColor.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(5),
            ),
            child: Text(
              badge,
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

  Widget _buildTargetTile({
    required String tier,
    required String lotPct,
    required String value,
    required String pips,
    required String actionHint,
    required Color accentColor,
    required bool isHit,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 11),
      decoration: BoxDecoration(
        color: isHit ? accentColor.withValues(alpha: 0.12) : AppColors.surfaceInset,
        borderRadius: BorderRadius.circular(13),
        border: Border.all(
          color: isHit ? accentColor.withValues(alpha: 0.55) : AppColors.border,
          width: isHit ? 1.0 : 0.8,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 5.5,
                    height: 5.5,
                    decoration: BoxDecoration(color: accentColor, shape: BoxShape.circle),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    tier,
                    style: const TextStyle(
                      color: AppColors.textMuted,
                      fontSize: 9.5,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.4,
                    ),
                  ),
                ],
              ),
              Text(
                lotPct,
                style: AppTypography.mono(
                  color: AppColors.textTertiary,
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              style: AppTypography.mono(
                color: accentColor,
                fontSize: 13.5,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.2,
              ),
            ),
          ),
          const SizedBox(height: 5),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Flexible(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                  decoration: BoxDecoration(
                    color: accentColor.withValues(alpha: 0.13),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    pips,
                    style: AppTypography.mono(
                      color: accentColor,
                      fontSize: 9,
                      fontWeight: FontWeight.w700,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
              const SizedBox(width: 3),
              Flexible(
                child: Text(
                  actionHint,
                  style: const TextStyle(
                    color: AppColors.textTertiary,
                    fontSize: 8.5,
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
