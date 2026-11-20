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
    this.initiallyExpanded = true,
  });

  @override
  State<TradeSetupCard> createState() => _TradeSetupCardState();
}

class _TradeSetupCardState extends State<TradeSetupCard> {
  late bool _isReasonsExpanded;
  int _selectedTfIndex = 2; // Default to M15; user can tap M1, M5, M15, M30, H1, H4, D1

  @override
  void initState() {
    super.initState();
    _isReasonsExpanded = widget.initiallyExpanded;
  }

  Color _trendColor(String trend) {
    final u = trend.toUpperCase();
    if (u == 'BULLISH') return AppColors.bullish;
    if (u == 'BEARISH') return AppColors.bearish;
    return AppColors.gold;
  }

  Color _toneColor(String tone) {
    switch (tone.toLowerCase()) {
      case 'bullish':
        return AppColors.bullish;
      case 'bearish':
        return AppColors.bearish;
      case 'cyan':
        return AppColors.cyan;
      default:
        return AppColors.gold;
    }
  }

  IconData _trendIcon(String trend) {
    final u = trend.toUpperCase();
    if (u == 'BULLISH') return LucideIcons.trendingUp;
    if (u == 'BEARISH') return LucideIcons.trendingDown;
    return LucideIcons.minus;
  }

  IconData _reasonIcon(int index, String title) {
    final lower = title.toLowerCase();
    if (lower.contains('arah') || lower.contains('timeframe')) return LucideIcons.compass;
    if (lower.contains('zona') || lower.contains('entry')) return LucideIcons.crosshair;
    if (lower.contains('sl') || lower.contains('proteksi')) return LucideIcons.shield;
    if (lower.contains('tp') || lower.contains('target')) return LucideIcons.target;
    const fallbacks = [
      LucideIcons.compass,
      LucideIcons.crosshair,
      LucideIcons.shield,
      LucideIcons.target,
    ];
    return fallbacks[index % fallbacks.length];
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.setup;
    final isBuy = s.action.toUpperCase() == 'BUY';
    final isSell = s.action.toUpperCase() == 'SELL';
    final isInstant = s.executionType.toUpperCase() == 'INSTANT';
    final isWait = !isBuy && !isSell;

    final Color actionColor = isBuy
        ? AppColors.bullish
        : (isSell ? AppColors.bearish : AppColors.gold);

    final String heroActionTitle = s.actionLabel.isNotEmpty
        ? s.actionLabel
        : (isBuy
            ? (isInstant ? 'BUY NOW (SNIPER)' : 'BUY LIMIT (SNIPER)')
            : (isSell
                ? (isInstant ? 'SELL NOW (SNIPER)' : 'SELL LIMIT (SNIPER)')
                : 'WAIT • NEWS GUARD'));

    final IconData heroIcon = isWait
        ? LucideIcons.shieldAlert
        : (isInstant ? LucideIcons.zap : LucideIcons.crosshair);

    final setupStatus = s.safeStatus.toUpperCase();
    final isTp1Hit = setupStatus.contains('TP1') || setupStatus.contains('TP2');
    final isTp2Hit = setupStatus.contains('TP2');

    return IosGlassCard(
      borderRadius: 22,
      padding: const EdgeInsets.all(18),
      borderColor: actionColor.withValues(alpha: 0.28),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ═══════════════════════════════════════════════════════════════════
          // BLOK 1: HEADER & KEPUTUSAN UTAMA (LANGSUNG JELAS APA AKSI SEKARANG)
          // ═══════════════════════════════════════════════════════════════════
          Row(
            children: [
              Container(
                width: 7,
                height: 7,
                decoration: BoxDecoration(
                  color: AppColors.gold,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(color: AppColors.gold.withValues(alpha: 0.55), blurRadius: 6),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'SNIPER SCALP SETUP',
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
              if (s.sessionName.isNotEmpty) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceInset,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.border, width: 0.7),
                  ),
                  child: Text(
                    s.sessionName,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 12),

          // Action Hero Banner (Signal + RRR + 1-line clear instruction)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: actionColor.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(15),
              border: Border.all(color: actionColor.withValues(alpha: 0.35), width: 0.9),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: actionColor.withValues(alpha: 0.18),
                        borderRadius: BorderRadius.circular(9),
                      ),
                      child: Icon(heroIcon, color: actionColor, size: 15),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        heroActionTitle,
                        style: TextStyle(
                          color: actionColor,
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.2,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8.5, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceInset,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: AppColors.cyan.withValues(alpha: 0.35), width: 0.8),
                      ),
                      child: Text(
                        'RRR ${s.riskRewardRatio}',
                        style: AppTypography.mono(
                          color: AppColors.cyan,
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 9),
                Text(
                  s.safeStatusMessage,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 12,
                    height: 1.4,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // ═══════════════════════════════════════════════════════════════════
          // BLOK 2: ANGKA EKSEKUSI (ENTRY, SL KETAT 30–50P, TP1 60P, TP2, TP3)
          // ═══════════════════════════════════════════════════════════════════
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'LEVEL EKSEKUSI',
                style: TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.7,
                ),
              ),
              Text(
                'SL 30–50p • TP1 60p',
                style: AppTypography.mono(
                  color: AppColors.gold,
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 9),

          // Top 2-Column Row: ZONA ENTRI & STOP LOSS
          Row(
            children: [
              Expanded(
                child: _buildPrimaryTile(
                  label: 'ZONA ENTRI',
                  value: s.entryZone.isNotEmpty ? s.entryZone : '\$${s.entryPrice.toStringAsFixed(2)}',
                  badge: '${isInstant ? 'Market' : 'Limit'} \$${s.entryPrice.toStringAsFixed(2)}',
                  valueColor: AppColors.textPrimary,
                  accentColor: AppColors.cyan,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildPrimaryTile(
                  label: 'STOP LOSS (SL)',
                  value: '\$${s.stopLoss.toStringAsFixed(2)}',
                  badge: s.riskPips > 0 ? '-${s.riskPips.toStringAsFixed(0)} pips' : 'Ketat',
                  valueColor: AppColors.bearish,
                  accentColor: AppColors.bearish,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // 3-Column Target Scaling Ladder: TP1 (40%) | TP2 (40%) | TP3 (20%)
          Row(
            children: [
              Expanded(
                child: _buildTargetTile(
                  tier: 'TP 1',
                  lotPct: '40%',
                  value: '\$${s.takeProfit1.toStringAsFixed(2)}',
                  pips: s.rewardTp1Pips > 0 ? '+${s.rewardTp1Pips.toStringAsFixed(0)}p' : '+60p',
                  actionHint: 'SL → BEP',
                  accentColor: AppColors.bullish,
                  isHit: isTp1Hit,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildTargetTile(
                  tier: 'TP 2',
                  lotPct: '40%',
                  value: '\$${s.takeProfit2.toStringAsFixed(2)}',
                  pips: s.rewardTp2Pips > 0 ? '+${s.rewardTp2Pips.toStringAsFixed(0)}p' : 'Struktur',
                  actionHint: 'SL → TP1',
                  accentColor: AppColors.bullish,
                  isHit: isTp2Hit,
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
          const SizedBox(height: 16),

          // ═══════════════════════════════════════════════════════════════════
          // BLOK 3: KENAPA ENTRY INI? (4 POIN TERSTRUKTUR — TERBUKA LANGSUNG!)
          // ═══════════════════════════════════════════════════════════════════
          _buildEntryReasonsSection(s),
          const SizedBox(height: 14),

          // ═══════════════════════════════════════════════════════════════════
          // BLOK 4: VERIFIKASI 7 TIMEFRAME (M1–D1 INTERAKTIF, RAPI 2 BARIS)
          // ═══════════════════════════════════════════════════════════════════
          if (s.mtfOverview.isNotEmpty) ...[
            _buildMtfComparisonPanel(s),
            const SizedBox(height: 14),
          ],

          // ═══════════════════════════════════════════════════════════════════
          // BLOK 5: CTA CHART TRADINGVIEW
          // ═══════════════════════════════════════════════════════════════════
          if (widget.onViewChart != null || widget.onViewOnChart != null)
            SizedBox(
              width: double.infinity,
              child: CupertinoButton(
                padding: const EdgeInsets.symmetric(vertical: 12),
                color: AppColors.surfaceElevated,
                borderRadius: BorderRadius.circular(13),
                onPressed: widget.onViewChart ?? widget.onViewOnChart,
                child: const Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(LucideIcons.chartCandlestick, color: AppColors.gold, size: 15),
                    SizedBox(width: 8),
                    Text(
                      'Lihat Chart TradingView',
                      style: TextStyle(
                        color: AppColors.gold,
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    SizedBox(width: 4),
                    Icon(LucideIcons.chevronRight, color: AppColors.gold, size: 13),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildEntryReasonsSection(TradeSetupModel s) {
    final reasons = s.entryReasons;

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceInset,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: () {
              setState(() {
                _isReasonsExpanded = !_isReasonsExpanded;
              });
            },
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              child: Row(
                children: [
                  const Icon(LucideIcons.lightbulb, color: AppColors.gold, size: 15),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'KENAPA ENTRY INI?',
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.6,
                      ),
                    ),
                  ),
                  Text(
                    _isReasonsExpanded ? 'Ringkas' : 'Lihat Alasan',
                    style: const TextStyle(
                      color: AppColors.textMuted,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    _isReasonsExpanded ? LucideIcons.chevronUp : LucideIcons.chevronDown,
                    color: AppColors.textMuted,
                    size: 13,
                  ),
                ],
              ),
            ),
          ),
          if (_isReasonsExpanded) ...[
            Container(height: 0.8, color: AppColors.borderSubtle),
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 12, 14, 14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (reasons.isNotEmpty)
                    ...List.generate(reasons.length, (i) {
                      final r = reasons[i];
                      final accent = _toneColor(r.tone);
                      final icon = _reasonIcon(i, r.title);
                      return Padding(
                        padding: EdgeInsets.only(bottom: i == reasons.length - 1 ? 0 : 12),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              margin: const EdgeInsets.only(top: 1),
                              padding: const EdgeInsets.all(5.5),
                              decoration: BoxDecoration(
                                color: accent.withValues(alpha: 0.13),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Icon(icon, color: accent, size: 12.5),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          r.title,
                                          style: const TextStyle(
                                            color: AppColors.textPrimary,
                                            fontSize: 12,
                                            fontWeight: FontWeight.w700,
                                          ),
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                      if (r.tag.isNotEmpty) ...[
                                        const SizedBox(width: 6),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 6.5, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: accent.withValues(alpha: 0.13),
                                            borderRadius: BorderRadius.circular(5),
                                          ),
                                          child: Text(
                                            r.tag,
                                            style: AppTypography.mono(
                                              color: accent,
                                              fontSize: 9.5,
                                              fontWeight: FontWeight.w700,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ],
                                  ),
                                  const SizedBox(height: 3.5),
                                  Text(
                                    r.detail,
                                    style: const TextStyle(
                                      color: AppColors.textSecondary,
                                      fontSize: 11.8,
                                      height: 1.45,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      );
                    })
                  else
                    Text(
                      s.technicalRationale,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                        height: 1.5,
                      ),
                    ),
                  if (s.invalidationLevel.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      decoration: BoxDecoration(
                        color: AppColors.bearish.withValues(alpha: 0.09),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.bearish.withValues(alpha: 0.24), width: 0.8),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Padding(
                            padding: EdgeInsets.only(top: 1),
                            child: Icon(LucideIcons.circleAlert, color: AppColors.bearish, size: 13),
                          ),
                          const SizedBox(width: 7),
                          Expanded(
                            child: Text(
                              'Batal jika: ${s.invalidationLevel}',
                              style: const TextStyle(
                                color: AppColors.bearish,
                                fontSize: 11,
                                height: 1.38,
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
    );
  }

  Widget _buildMtfComparisonPanel(TradeSetupModel s) {
    final items = s.mtfOverview;
    final int safeIdx = _selectedTfIndex.clamp(0, items.length - 1);
    final selectedItem = items[safeIdx];
    final selectedColor = _trendColor(selectedItem.trend);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surfaceInset,
        borderRadius: BorderRadius.circular(15),
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with interactive hint
          Row(
            children: [
              const Icon(LucideIcons.layers, color: AppColors.gold, size: 13.5),
              const SizedBox(width: 7),
              const Expanded(
                child: Text(
                  'CEK ZONA 7 TIMEFRAME',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.6,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6.5, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.gold.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(5),
                ),
                child: const Text(
                  'Ketuk TF',
                  style: TextStyle(
                    color: AppColors.gold,
                    fontSize: 9.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // 7-TF Interactive Pill Matrix (M1 | M5 | M15 | M30 | H1 | H4 | D1)
          Row(
            children: List.generate(items.length, (i) {
              final tfItem = items[i];
              final isSelected = i == safeIdx;
              final tColor = _trendColor(tfItem.trend);

              return Expanded(
                child: Padding(
                  padding: EdgeInsets.only(right: i == items.length - 1 ? 0 : 4),
                  child: GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: () {
                      setState(() {
                        _selectedTfIndex = i;
                      });
                    },
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 160),
                      padding: const EdgeInsets.symmetric(vertical: 7),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? tColor.withValues(alpha: 0.18)
                            : const Color(0xFF141824),
                        borderRadius: BorderRadius.circular(9),
                        border: Border.all(
                          color: isSelected
                              ? AppColors.gold.withValues(alpha: 0.80)
                              : tColor.withValues(alpha: 0.22),
                          width: isSelected ? 1.15 : 0.7,
                        ),
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            tfItem.tf,
                            style: TextStyle(
                              color: isSelected ? AppColors.textPrimary : AppColors.textSecondary,
                              fontSize: 10,
                              fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Icon(
                            _trendIcon(tfItem.trend),
                            color: tColor,
                            size: 12,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            }),
          ),
          const SizedBox(height: 10),

          // Spacious 2-Row Selected TF Inspector (Zero crowding on narrow screens!)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xFF141824),
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: AppColors.borderSubtle, width: 0.7),
            ),
            child: Column(
              children: [
                // Row 1: TF + Trend | RSI + ATR
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          selectedItem.tf,
                          style: const TextStyle(
                            color: AppColors.gold,
                            fontSize: 11.5,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                          decoration: BoxDecoration(
                            color: selectedColor.withValues(alpha: 0.14),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            selectedItem.trend,
                            style: TextStyle(
                              color: selectedColor,
                              fontSize: 9.5,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                      ],
                    ),
                    Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (selectedItem.rsi != null) ...[
                          Text(
                            'RSI ${selectedItem.rsi!.toStringAsFixed(0)}',
                            style: AppTypography.mono(
                              color: AppColors.cyan,
                              fontSize: 10.5,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(width: 8),
                        ],
                        if (selectedItem.atrPips > 0)
                          Text(
                            'ATR ${selectedItem.atrPips.toStringAsFixed(0)}p',
                            style: AppTypography.mono(
                              color: AppColors.textTertiary,
                              fontSize: 10.5,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Container(height: 0.7, color: AppColors.borderSubtle),
                const SizedBox(height: 8),
                // Row 2: Support | Resistance side-by-side cleanly
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'SUPPORT TERDEKAT',
                            style: TextStyle(
                              color: AppColors.textMuted,
                              fontSize: 9,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.4,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            '\$${selectedItem.sup.toStringAsFixed(2)}',
                            style: AppTypography.mono(
                              color: AppColors.bullish,
                              fontSize: 13,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Container(width: 0.8, height: 28, color: AppColors.borderSubtle),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'RESISTANCE TERDEKAT',
                            style: TextStyle(
                              color: AppColors.textMuted,
                              fontSize: 9,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.4,
                            ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            '\$${selectedItem.res.toStringAsFixed(2)}',
                            style: AppTypography.mono(
                              color: AppColors.bearish,
                              fontSize: 13,
                              fontWeight: FontWeight.w800,
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

          if (s.confluenceNote.isNotEmpty) ...[
            const SizedBox(height: 9),
            Text(
              s.confluenceNote,
              style: const TextStyle(
                color: AppColors.textTertiary,
                fontSize: 11,
                height: 1.42,
              ),
            ),
          ],
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
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.5,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              style: AppTypography.mono(
                color: valueColor,
                fontSize: 15,
                fontWeight: FontWeight.w800,
                letterSpacing: -0.2,
              ),
            ),
          ),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6.5, vertical: 2.5),
            decoration: BoxDecoration(
              color: accentColor.withValues(alpha: 0.13),
              borderRadius: BorderRadius.circular(5),
            ),
            child: Text(
              badge,
              style: AppTypography.mono(
                color: accentColor,
                fontSize: 10,
                fontWeight: FontWeight.w700,
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
                  fontSize: 9.5,
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
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Flexible(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5.5, vertical: 2),
                  decoration: BoxDecoration(
                    color: accentColor.withValues(alpha: 0.13),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    pips,
                    style: AppTypography.mono(
                      color: accentColor,
                      fontSize: 9.5,
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
