import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../core/constants/app_colors.dart';
import '../../core/theme/app_theme.dart';
import '../../core/network/api_service.dart';
import '../../data/models/signal_history_model.dart';
import '../widgets/ios_glass_card.dart';
import '../widgets/ios_segmented_control.dart';
import '../widgets/modern_toast.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final ApiService _api = ApiService();
  SignalHistoryResponseModel? _data;
  bool _isLoading = true;
  bool _isSyncing = false;
  String? _error;

  String _outcomeFilter = 'ALL'; // ALL | WIN | LOSS | OPEN
  String _actionFilter = 'ALL'; // ALL | BUY | SELL
  final Set<int> _expandedIds = {};

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory({bool silent = false}) async {
    if (!silent) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    }
    try {
      final res = await _api.getSignalHistory(
        symbol: 'XAUUSD',
        action: _actionFilter,
        outcome: _outcomeFilter,
        limit: 40,
      );
      if (mounted) {
        setState(() {
          _data = res;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString().replaceFirst('Exception: ', '');
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _triggerSync() async {
    if (_isSyncing) return;
    setState(() => _isSyncing = true);
    try {
      await _api.refreshSignalHistory(symbol: 'XAUUSD');
      await _loadHistory(silent: true);
      if (mounted) {
        ModernToast.showSuccess(
          context,
          'Verifikasi SL & TP1–TP3 diperbarui terhadap candle XAU/USD terbaru.',
          title: 'Riwayat Diperbarui',
        );
      }
    } catch (e) {
      if (mounted) {
        ModernToast.showError(
          context,
          'Gagal sinkronisasi riwayat: ${e.toString().replaceFirst('Exception: ', '')}',
        );
      }
    } finally {
      if (mounted) setState(() => _isSyncing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: RefreshIndicator(
        onRefresh: _triggerSync,
        color: AppColors.gold,
        backgroundColor: AppColors.surfaceElevated,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(parent: BouncingScrollPhysics()),
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 120),
          children: [
            _buildHeader(),
            const SizedBox(height: 14),

            if (_isLoading && _data == null)
              _buildLoadingState()
            else if (_error != null && _data == null)
              _buildErrorState()
            else if (_data != null) ...[
              _buildStatsCard(_data!.stats),
              const SizedBox(height: 12),
              if (_data!.selfEvaluation != null && _data!.selfEvaluation!.summary.isNotEmpty) ...[
                _buildSelfEvaluationCard(_data!.selfEvaluation!),
                const SizedBox(height: 14),
              ],
              _buildFilters(),
              const SizedBox(height: 14),

              if (_data!.items.isEmpty)
                _buildEmptyFilterState()
              else
                ..._data!.items.map(_buildSignalCard),

              if (_data!.methodologyNote.isNotEmpty) ...[
                const SizedBox(height: 6),
                _buildMethodologyNote(_data!.methodologyNote, _data!.updatedAtWib),
              ],
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Expanded(
              child: Row(
                children: [
                  Text(
                    'RIWAYAT ENTRY',
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 16.5,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.4,
                    ),
                  ),
                  SizedBox(width: 8),
                  _WibPill(),
                ],
              ),
            ),
            GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: _triggerSync,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6.5),
                decoration: BoxDecoration(
                  color: AppColors.surfaceElevated,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: AppColors.gold.withValues(alpha: 0.30), width: 0.85),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (_isSyncing)
                      const CupertinoActivityIndicator(radius: 6.5, color: AppColors.gold)
                    else
                      const Icon(LucideIcons.refreshCw, color: AppColors.gold, size: 12.5),
                    const SizedBox(width: 5),
                    const Text(
                      'Sync',
                      style: TextStyle(
                        color: AppColors.gold,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 5),
        const Text(
          'Track record objektif SL & TP1–TP3 terhadap candle XAU/USD asli',
          style: TextStyle(
            color: AppColors.textMuted,
            fontSize: 11.5,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildStatsCard(SignalHistoryStatsModel s) {
    final bool isNetPositive = s.netPips >= 0;
    final Color netColor = isNetPositive ? AppColors.bullish : AppColors.bearish;
    final String netStr = '${isNetPositive ? '+' : ''}${s.netPips.toStringAsFixed(0)}p';

    return IosGlassCard(
      borderRadius: 20,
      padding: const EdgeInsets.all(16),
      borderColor: AppColors.gold.withValues(alpha: 0.22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Top 3 Headline KPIs
          Row(
            children: [
              Expanded(
                child: _buildKpiTile(
                  label: 'WIN RATE',
                  value: '${s.winRatePct.toStringAsFixed(1)}%',
                  sub: '${s.wins}W / ${s.losses}L',
                  valueColor: s.winRatePct >= 50 ? AppColors.bullish : AppColors.gold,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildKpiTile(
                  label: 'NET PIPS',
                  value: netStr,
                  sub: '${s.closedTrades} trade selesai',
                  valueColor: netColor,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _buildKpiTile(
                  label: 'PROFIT FACTOR',
                  value: '${s.profitFactor.toStringAsFixed(2)}×',
                  sub: 'Avg +${s.avgWinPips.toStringAsFixed(0)} / -${s.avgLossPips.toStringAsFixed(0)}p',
                  valueColor: s.profitFactor >= 1.2 ? AppColors.cyan : AppColors.gold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Outcome Breakdown Chips
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              _buildCountChip('TP3: ${s.tp3Hits}', AppColors.gold),
              _buildCountChip('TP2: ${s.tp2Hits}', AppColors.bullish),
              _buildCountChip('TP1: ${s.tp1Hits}', AppColors.bullish),
              _buildCountChip('SL: ${s.slHits}', AppColors.bearish),
              if (s.activeOrPending > 0)
                _buildCountChip('Aktif: ${s.activeOrPending}', AppColors.cyan),
              if (s.expired > 0)
                _buildCountChip('Expired: ${s.expired}', AppColors.textMuted),
            ],
          ),
          const SizedBox(height: 11),

          // Transparent BUY vs SELL Split Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.surfaceInset,
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: AppColors.border, width: 0.7),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(LucideIcons.trendingUp, color: AppColors.bullish, size: 13),
                    const SizedBox(width: 5),
                    Text(
                      'BUY: ${s.buyCount} sinyal (${s.buyWins} TP)',
                      style: AppTypography.mono(
                        color: AppColors.bullish,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
                Container(width: 0.8, height: 14, color: AppColors.border),
                Row(
                  children: [
                    const Icon(LucideIcons.trendingDown, color: AppColors.bearish, size: 13),
                    const SizedBox(width: 5),
                    Text(
                      'SELL: ${s.sellCount} sinyal (${s.sellWins} TP)',
                      style: AppTypography.mono(
                        color: AppColors.bearish,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildKpiTile({
    required String label,
    required String value,
    required String sub,
    required Color valueColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surfaceInset,
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: AppColors.border, width: 0.75),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: AppColors.textMuted,
              fontSize: 9,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 5),
          FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text(
              value,
              style: AppTypography.mono(
                color: valueColor,
                fontSize: 16,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          const SizedBox(height: 3),
          Text(
            sub,
            style: const TextStyle(
              color: AppColors.textTertiary,
              fontSize: 9.5,
              fontWeight: FontWeight.w600,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildCountChip(String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(7),
        border: Border.all(color: color.withValues(alpha: 0.28), width: 0.7),
      ),
      child: Text(
        label,
        style: AppTypography.mono(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Widget _buildFilters() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        IosSegmentedControl<String>(
          fullWidth: true,
          selectedValue: _outcomeFilter,
          items: const {
            'ALL': 'Semua',
            'WIN': 'TP Hit',
            'LOSS': 'SL Hit',
            'OPEN': 'Aktif',
          },
          onValueChanged: (val) {
            setState(() => _outcomeFilter = val);
            _loadHistory(silent: true);
          },
        ),
        const SizedBox(height: 9),
        Row(
          children: [
            _buildDirectionChip('ALL', 'Semua Arah', AppColors.gold),
            const SizedBox(width: 7),
            _buildDirectionChip('BUY', 'BUY Only', AppColors.bullish),
            const SizedBox(width: 7),
            _buildDirectionChip('SELL', 'SELL Only', AppColors.bearish),
          ],
        ),
      ],
    );
  }

  Widget _buildDirectionChip(String value, String label, Color accent) {
    final selected = _actionFilter == value;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () {
        if (_actionFilter == value) return;
        setState(() => _actionFilter = value);
        _loadHistory(silent: true);
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
        decoration: BoxDecoration(
          color: selected ? accent.withValues(alpha: 0.16) : AppColors.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: selected ? accent.withValues(alpha: 0.55) : AppColors.border,
            width: 0.85,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? accent : AppColors.textSecondary,
            fontSize: 11,
            fontWeight: selected ? FontWeight.w800 : FontWeight.w600,
          ),
        ),
      ),
    );
  }

  Widget _buildSignalCard(SignalHistoryItemModel item) {
    final isBuy = item.action == 'BUY';
    final sideColor = isBuy ? AppColors.bullish : AppColors.bearish;
    final isExpanded = _expandedIds.contains(item.id);

    late final Color outcomeColor;
    late final String outcomeLabel;
    late final IconData outcomeIcon;

    switch (item.outcome) {
      case 'TP3_HIT':
        outcomeColor = AppColors.gold;
        outcomeLabel = 'TP3 FULL +${item.realizedPips.toStringAsFixed(0)}p';
        outcomeIcon = LucideIcons.trophy;
        break;
      case 'TP2_HIT':
        outcomeColor = AppColors.bullish;
        outcomeLabel = 'TP2 HIT +${item.realizedPips.toStringAsFixed(0)}p';
        outcomeIcon = LucideIcons.circleCheck;
        break;
      case 'TP1_HIT':
        outcomeColor = AppColors.bullish;
        outcomeLabel = 'TP1 HIT +${item.realizedPips.toStringAsFixed(0)}p';
        outcomeIcon = LucideIcons.circleCheck;
        break;
      case 'SL_HIT':
        outcomeColor = AppColors.bearish;
        outcomeLabel = 'SL HIT ${item.realizedPips.toStringAsFixed(0)}p';
        outcomeIcon = LucideIcons.circleX;
        break;
      case 'ACTIVE':
        outcomeColor = AppColors.cyan;
        final sign = item.realizedPips >= 0 ? '+' : '';
        outcomeLabel = 'AKTIF $sign${item.realizedPips.toStringAsFixed(0)}p';
        outcomeIcon = LucideIcons.activity;
        break;
      case 'PENDING_LIMIT':
        outcomeColor = AppColors.gold;
        outcomeLabel = 'MENUNGGU LIMIT';
        outcomeIcon = LucideIcons.clock;
        break;
      default:
        outcomeColor = AppColors.textMuted;
        outcomeLabel = 'EXPIRED (0p)';
        outcomeIcon = LucideIcons.minusCircle;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 11),
      child: IosGlassCard(
        borderRadius: 18,
        padding: const EdgeInsets.all(14),
        borderColor: outcomeColor.withValues(alpha: item.isOpen ? 0.42 : 0.22),
        onTap: () {
          setState(() {
            if (isExpanded) {
              _expandedIds.remove(item.id);
            } else {
              _expandedIds.add(item.id);
            }
          });
        },
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Row 1: Action Pill + Source Tag + Outcome Badge
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                  decoration: BoxDecoration(
                    color: sideColor.withValues(alpha: 0.16),
                    borderRadius: BorderRadius.circular(7),
                    border: Border.all(color: sideColor.withValues(alpha: 0.40), width: 0.8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        isBuy ? LucideIcons.trendingUp : LucideIcons.trendingDown,
                        size: 11.5,
                        color: sideColor,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${item.action} ${item.executionType == 'INSTANT' ? 'NOW' : 'LIMIT'}',
                        style: TextStyle(
                          color: sideColor,
                          fontSize: 10.5,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 6),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6.5, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.cyan.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: AppColors.cyan.withValues(alpha: 0.30), width: 0.7),
                  ),
                  child: const Text(
                    'LIVE',
                    style: TextStyle(
                      color: AppColors.cyan,
                      fontSize: 9,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.4,
                    ),
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8.5, vertical: 4),
                  decoration: BoxDecoration(
                    color: outcomeColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: outcomeColor.withValues(alpha: 0.40), width: 0.8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(outcomeIcon, size: 11.5, color: outcomeColor),
                      const SizedBox(width: 4),
                      Text(
                        outcomeLabel,
                        style: AppTypography.mono(
                          color: outcomeColor,
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Row 2: Compact 4-Column Level Grid (Entry | SL | TP1 | TP3)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
              decoration: BoxDecoration(
                color: AppColors.surfaceInset,
                borderRadius: BorderRadius.circular(11),
                border: Border.all(color: AppColors.border, width: 0.7),
              ),
              child: Row(
                children: [
                  Expanded(
                    flex: 12,
                    child: _buildMiniLevel('ENTRY', '\$${item.entryPrice.toStringAsFixed(2)}', AppColors.textPrimary),
                  ),
                  Expanded(
                    flex: 10,
                    child: _buildMiniLevel('SL (-${item.riskPips.toStringAsFixed(0)}p)', '\$${item.stopLoss.toStringAsFixed(2)}', AppColors.bearish),
                  ),
                  Expanded(
                    flex: 10,
                    child: _buildMiniLevel('TP1 (+${item.rewardTp1Pips.toStringAsFixed(0)}p)', '\$${item.takeProfit1.toStringAsFixed(2)}', AppColors.bullish),
                  ),
                  Expanded(
                    flex: 10,
                    child: _buildMiniLevel('TP3 (+${item.rewardTp3Pips.toStringAsFixed(0)}p)', '\$${item.takeProfit3.toStringAsFixed(2)}', AppColors.gold),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 9),

            // Row 3: WIB Time + MFE/MAE quick metrics + expand icon
            Row(
              children: [
                const Icon(LucideIcons.clock, size: 11.5, color: AppColors.textMuted),
                const SizedBox(width: 5),
                Expanded(
                  child: Text(
                    item.closedAtWib != null
                        ? '${item.createdAtWib}  →  ${item.closedAtWib}'
                        : item.createdAtWib,
                    style: AppTypography.mono(
                      color: AppColors.textSecondary,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 6),
                Icon(
                  isExpanded ? LucideIcons.chevronUp : LucideIcons.chevronDown,
                  size: 14,
                  color: AppColors.textMuted,
                ),
              ],
            ),

            // Compact Post-Mortem Self-Evaluation pill on closed trades (visible immediately!)
            if (item.postMortem != null && item.postMortem!.causeLabel.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
                decoration: BoxDecoration(
                  color: (item.postMortem!.severity == 'WARNING'
                          ? AppColors.bearish
                          : (item.postMortem!.severity == 'POSITIVE' ? AppColors.bullish : AppColors.gold))
                      .withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: (item.postMortem!.severity == 'WARNING'
                            ? AppColors.bearish
                            : (item.postMortem!.severity == 'POSITIVE' ? AppColors.bullish : AppColors.gold))
                        .withValues(alpha: 0.28),
                    width: 0.7,
                  ),
                ),
                child: Row(
                  children: [
                    Icon(
                      LucideIcons.brainCircuit,
                      size: 12,
                      color: item.postMortem!.severity == 'WARNING'
                          ? AppColors.bearish
                          : (item.postMortem!.severity == 'POSITIVE' ? AppColors.bullish : AppColors.gold),
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Evaluasi: ${item.postMortem!.causeLabel}',
                        style: TextStyle(
                          color: item.postMortem!.severity == 'WARNING'
                              ? AppColors.bearish
                              : (item.postMortem!.severity == 'POSITIVE' ? AppColors.bullish : AppColors.gold),
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // Expandable Detailed Proof, Outcome Explanation & MFE/MAE
            if (isExpanded) ...[
              const SizedBox(height: 10),
              Container(height: 0.7, color: AppColors.border),
              const SizedBox(height: 9),
              Text(
                item.outcomeNote,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 11.5,
                  height: 1.45,
                  fontWeight: FontWeight.w500,
                ),
              ),
              if (item.postMortem != null && item.postMortem!.diagnosis.isNotEmpty) ...[
                const SizedBox(height: 8),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceInset,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.gold.withValues(alpha: 0.25), width: 0.75),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'AUTO POST-MORTEM & PELAJARAN AI',
                        style: TextStyle(
                          color: AppColors.gold,
                          fontSize: 9.5,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.5,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        item.postMortem!.diagnosis,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 11,
                          height: 1.4,
                        ),
                      ),
                      if (item.postMortem!.lesson.isNotEmpty) ...[
                        const SizedBox(height: 5),
                        Text(
                          '→ Koreksi: ${item.postMortem!.lesson}',
                          style: const TextStyle(
                            color: AppColors.cyan,
                            fontSize: 11,
                            height: 1.4,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: [
                  _buildDetailTag('Zona: ${item.entryZone}'),
                  _buildDetailTag('TP2: \$${item.takeProfit2.toStringAsFixed(2)} (+${item.rewardTp2Pips.toStringAsFixed(0)}p)'),
                  _buildDetailTag('Puncak Profit: +${item.maxFavorablePips.toStringAsFixed(0)}p'),
                  _buildDetailTag('Maks Drawdown: -${item.maxAdversePips.toStringAsFixed(0)}p'),
                  if (item.mtfAlignment.isNotEmpty) _buildDetailTag(item.mtfAlignment),
                  if (item.zoneProof.isNotEmpty) _buildDetailTag(item.zoneProof),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildMiniLevel(String label, String value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: AppColors.textMuted,
            fontSize: 8.5,
            fontWeight: FontWeight.w700,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: 2.5),
        FittedBox(
          fit: BoxFit.scaleDown,
          alignment: Alignment.centerLeft,
          child: Text(
            value,
            style: AppTypography.mono(
              color: color,
              fontSize: 11.5,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSelfEvaluationCard(SelfEvaluationModel ev) {
    final bool defensiveMode = ev.consecutiveSl >= 2 || ev.inPostSlCooldown;
    final Color accent = defensiveMode ? AppColors.gold : AppColors.cyan;

    return IosGlassCard(
      borderRadius: 18,
      padding: const EdgeInsets.all(14),
      borderColor: accent.withValues(alpha: 0.32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(LucideIcons.brainCircuit, color: accent, size: 14),
              ),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'EVALUASI MANDIRI AI (AUTO-LEARN)',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: accent.withValues(alpha: 0.35), width: 0.7),
                ),
                child: Text(
                  ev.inPostSlCooldown
                      ? 'COOLDOWN ${ev.cooldownRemainingMin}m'
                      : (defensiveMode ? 'DEFENSIF AKTIF' : 'ADAPTIF AKTIF'),
                  style: AppTypography.mono(
                    color: accent,
                    fontSize: 9,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 9),
          Text(
            ev.summary,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11.5,
              height: 1.45,
            ),
          ),
          if (ev.activeAdjustments.isNotEmpty) ...[
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: ev.activeAdjustments.map((adj) {
                return Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4.5),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceInset,
                    borderRadius: BorderRadius.circular(7),
                    border: Border.all(color: accent.withValues(alpha: 0.28), width: 0.7),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(LucideIcons.shieldCheck, size: 11, color: accent),
                      const SizedBox(width: 5),
                      Flexible(
                        child: Text(
                          adj,
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDetailTag(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7.5, vertical: 3.5),
      decoration: BoxDecoration(
        color: AppColors.surfaceInset,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: AppColors.border, width: 0.65),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: AppColors.textSecondary,
          fontSize: 10,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }

  Widget _buildMethodologyNote(String note, String updatedWib) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: AppColors.border, width: 0.75),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(LucideIcons.shieldCheck, color: AppColors.gold, size: 13),
              const SizedBox(width: 6),
              const Text(
                'METODOLOGI VERIFIKASI OBJEKTIF',
                style: TextStyle(
                  color: AppColors.gold,
                  fontSize: 9.5,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.5,
                ),
              ),
              const Spacer(),
              if (updatedWib.isNotEmpty)
                Text(
                  updatedWib.split('•').last.trim(),
                  style: AppTypography.mono(color: AppColors.textMuted, fontSize: 9.5),
                ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            note,
            style: const TextStyle(
              color: AppColors.textMuted,
              fontSize: 10.5,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingState() {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 64),
      child: Center(
        child: Column(
          children: [
            CupertinoActivityIndicator(radius: 13, color: AppColors.gold),
            SizedBox(height: 12),
            Text(
              'Memverifikasi riwayat SL & TP terhadap candle asli...',
              style: TextStyle(color: AppColors.textMuted, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState() {
    return IosGlassCard(
      borderRadius: 18,
      padding: const EdgeInsets.all(18),
      child: Column(
        children: [
          const Icon(LucideIcons.wifiOff, color: AppColors.bearish, size: 28),
          const SizedBox(height: 10),
          Text(
            _error ?? 'Gagal memuat riwayat entry',
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSecondary, fontSize: 12.5),
          ),
          const SizedBox(height: 12),
          CupertinoButton(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 9),
            color: AppColors.gold,
            borderRadius: BorderRadius.circular(10),
            onPressed: _loadHistory,
            child: const Text(
              'Coba Lagi',
              style: TextStyle(color: Color(0xFF08090C), fontSize: 12, fontWeight: FontWeight.w800),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyFilterState() {
    final isFreshAll = _outcomeFilter == 'ALL' && _actionFilter == 'ALL';
    return IosGlassCard(
      borderRadius: 18,
      padding: const EdgeInsets.all(22),
      child: Column(
        children: [
          Icon(
            isFreshAll ? LucideIcons.radar : LucideIcons.filter,
            color: AppColors.gold,
            size: 24,
          ),
          const SizedBox(height: 10),
          Text(
            isFreshAll
                ? 'Pencatatan LIVE Dimulai dari Awal'
                : 'Belum ada riwayat LIVE untuk filter ini',
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            isFreshAll
                ? 'Setiap setup baru yang muncul di Dashboard akan otomatis tercatat di sini dan diverifikasi real-time hingga menyentuh SL atau TP1–TP3.'
                : 'Hasil TP Hit / SL Hit akan tercatat otomatis begitu sinyal live yang berjalan mencapai target atau Stop Loss.',
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: AppColors.textMuted,
              fontSize: 11.5,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }
}

class _WibPill extends StatelessWidget {
  const _WibPill();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7.5, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(7),
        border: Border.all(color: AppColors.gold.withValues(alpha: 0.30), width: 0.7),
      ),
      child: const Text(
        'WIB (UTC+7)',
        style: TextStyle(
          color: AppColors.gold,
          fontSize: 9.5,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}
