import 'dart:math' as math;
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../data/models/news_intelligence_model.dart';
import 'ios_glass_card.dart';

class NewsScenarioSheet extends StatelessWidget {
  final NewsIntelligenceModel data;
  final bool isModalDialog;

  const NewsScenarioSheet({
    super.key,
    required this.data,
    this.isModalDialog = false,
  });

  static void show(BuildContext context, NewsIntelligenceModel model) {
    final isDesktop = MediaQuery.of(context).size.width > 720;

    if (isDesktop) {
      showGeneralDialog(
        context: context,
        barrierDismissible: true,
        barrierLabel: 'NewsScenarioModal',
        barrierColor: Colors.black.withValues(alpha: 0.75),
        transitionDuration: const Duration(milliseconds: 280),
        pageBuilder: (context, anim1, anim2) {
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxWidth: 740,
                maxHeight: 820,
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
                child: Material(
                  color: Colors.transparent,
                  child: NewsScenarioSheet(data: model, isModalDialog: true),
                ),
              ),
            ),
          );
        },
        transitionBuilder: (context, anim1, anim2, child) {
          final curve = CurvedAnimation(parent: anim1, curve: Curves.easeOutCubic);
          return ScaleTransition(
            scale: Tween<double>(begin: 0.94, end: 1.0).animate(curve),
            child: FadeTransition(opacity: anim1, child: child),
          );
        },
      );
    } else {
      showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        backgroundColor: Colors.transparent,
        barrierColor: Colors.black.withValues(alpha: 0.75),
        builder: (ctx) => Material(
          color: Colors.transparent,
          child: NewsScenarioSheet(data: model),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isBearish = data.bias.toUpperCase() == 'BEARISH';
    final isBullish = data.bias.toUpperCase() == 'BULLISH';
    final Color biasColor = isBullish
        ? AppColors.bullish
        : (isBearish ? AppColors.bearish : AppColors.neutral);

    return Material(
      color: Colors.transparent,
      child: Container(
        height: isModalDialog ? double.infinity : MediaQuery.of(context).size.height * 0.92,
        decoration: BoxDecoration(
          color: const Color(0xFF10141F), // 100% Opaque solid background - no ghosting!
          borderRadius: isModalDialog
              ? BorderRadius.circular(24)
              : const BorderRadius.vertical(top: Radius.circular(28)),
          border: Border.all(color: AppColors.borderSubtle, width: 1.0),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.8),
              blurRadius: 35,
              spreadRadius: 5,
            ),
          ],
        ),
        child: Column(
        children: [
          // Drag handle
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 8),
              width: 38,
              height: 4.5,
              decoration: BoxDecoration(
                color: const Color(0x40FFFFFF),
                borderRadius: BorderRadius.circular(3),
              ),
            ),
          ),

          // Header Bar
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 4, 16, 12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
                            decoration: BoxDecoration(
                              color: AppColors.impactHigh.withValues(alpha: 0.18),
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: AppColors.impactHigh.withValues(alpha: 0.4)),
                            ),
                            child: const Text(
                              'NEWS INTELLIGENCE',
                              style: TextStyle(
                                color: AppColors.impactHigh,
                                fontSize: 9.5,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 0.6,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            data.scheduledAtWib,
                            style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        data.eventTitle,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.2,
                        ),
                      ),
                    ],
                  ),
                ),
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: const Color(0x351F2636),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Icon(CupertinoIcons.xmark, color: AppColors.textMuted, size: 16),
                  ),
                ),
              ],
            ),
          ),
          Container(height: 1, color: AppColors.borderSubtle),

          // Body Content
          Expanded(
            child: SingleChildScrollView(
              physics: const BouncingScrollPhysics(),
              padding: EdgeInsets.fromLTRB(16, 14, 16, math.max(30.0, MediaQuery.paddingOf(context).bottom + 20)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Event Key Numbers (Consensus vs Previous)
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0x351F2636),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.borderSubtle),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildStat('KONSENSUS PASAR', data.consensus, AppColors.primary),
                        Container(width: 1, height: 32, color: AppColors.borderSubtle),
                        _buildStat('ANGKA SEBELUMNYA', data.previous, AppColors.textSecondary),
                        Container(width: 1, height: 32, color: AppColors.borderSubtle),
                        _buildStat('BIAS & KEYAKINAN', '${data.bias} (${data.confidenceLevel})', biasColor),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // 1. Rezim Pasar Saat Ini
                  _buildSectionCard(
                    icon: CupertinoIcons.flame_fill,
                    iconColor: const Color(0xFFF59E0B),
                    title: '1. REZIM PASAR SAAT INI',
                    content: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          data.marketRegime,
                          style: const TextStyle(
                            color: Color(0xFFF59E0B),
                            fontSize: 13.5,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          data.marketRegimeEvidence,
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 12.5,
                            height: 1.45,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),

                  // 2. Fundamental & Jalur Transmisi Geopolitik
                  _buildSectionCard(
                    icon: CupertinoIcons.arrow_branch,
                    iconColor: AppColors.primary,
                    title: '2. FUNDAMENTAL & JALUR TRANSMISI GEOPOLITIK',
                    content: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          data.fundamentalSummary,
                          style: const TextStyle(color: AppColors.textPrimary, fontSize: 12.5, height: 1.45),
                        ),
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: const Color(0x251F2636),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AppColors.borderSubtle),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Row(
                                children: [
                                  Icon(CupertinoIcons.link, color: AppColors.primary, size: 12),
                                  SizedBox(width: 5),
                                  Text(
                                    'JALUR TRANSMISI DAMPAK KE EMAS',
                                    style: TextStyle(color: AppColors.primary, fontSize: 10, fontWeight: FontWeight.w700),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 5),
                              Text(
                                data.geopoliticalSummary,
                                style: const TextStyle(color: AppColors.textPrimary, fontSize: 12, height: 1.4),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),

                  // 3. Positioning & Sentimen Pasar
                  _buildSectionCard(
                    icon: CupertinoIcons.person_3_fill,
                    iconColor: const Color(0xFF8B5CF6),
                    title: '3. POSITIONING & SENTIMEN PASAR',
                    content: Text(
                      data.positioningSentiment,
                      style: const TextStyle(color: AppColors.textPrimary, fontSize: 12.5, height: 1.45),
                    ),
                  ),
                  const SizedBox(height: 14),

                  // 4. Kondisi Chart Multi-Timeframe & Level Invalidasi
                  _buildSectionCard(
                    icon: CupertinoIcons.chart_bar_alt_fill,
                    iconColor: const Color(0xFF10B981),
                    title: '4. KONDISI CHART & LEVEL INVALIDASI',
                    content: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildTimeframeRow('H4 (Bias & Zona Besar)', data.chartConditionH4),
                        const SizedBox(height: 6),
                        _buildTimeframeRow('M30 (Struktur Area)', data.chartConditionM30),
                        const SizedBox(height: 6),
                        _buildTimeframeRow('M5 (Timing Eksekusi)', data.chartConditionM5),
                        const SizedBox(height: 10),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppColors.bearish.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AppColors.bearish.withValues(alpha: 0.3)),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(CupertinoIcons.exclamationmark_octagon_fill, color: AppColors.bearish, size: 14),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Level Invalidasi: ${data.invalidationLevel}',
                                  style: const TextStyle(
                                    color: AppColors.bearish,
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.w700,
                                    height: 1.35,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),

                  // 5. Matriks 3 Skenario Terukur
                  const Padding(
                    padding: EdgeInsets.only(left: 4, bottom: 8),
                    child: Text(
                      '5. MATRIKS 3 SKENARIO TERUKUR (BUKAN TEBAKAN)',
                      style: TextStyle(
                        color: AppColors.primary,
                        fontSize: 11.5,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.6,
                      ),
                    ),
                  ),
                  for (final sc in data.scenarios) ...[
                    _buildScenarioCard(sc),
                    const SizedBox(height: 10),
                  ],
                  const SizedBox(height: 14),

                  // 6. Hal yang Bisa Mengubah Kesimpulan
                  _buildSectionCard(
                    icon: CupertinoIcons.arrow_2_circlepath,
                    iconColor: const Color(0xFFEC4899),
                    title: '6. HAL YANG DAPAT MENGUBAH KESIMPULAN',
                    content: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        for (final c in data.catalystsToWatch) ...[
                          Padding(
                            padding: const EdgeInsets.only(bottom: 6),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('• ', style: TextStyle(color: Color(0xFFEC4899), fontSize: 14, fontWeight: FontWeight.bold)),
                                Expanded(
                                  child: Text(c, style: const TextStyle(color: AppColors.textPrimary, fontSize: 12, height: 1.35)),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),

                  // 7. Daftar Katalis Tertunda
                  _buildSectionCard(
                    icon: CupertinoIcons.clock_fill,
                    iconColor: AppColors.primary,
                    title: '7. DATA YANG BELUM KELUAR (WIB)',
                    content: Column(
                      children: [
                        for (final p in data.pendingCatalysts) ...[
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4),
                            child: Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: const Color(0x351F2636),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    p['time_wib'] ?? '',
                                    style: const TextStyle(
                                      color: AppColors.primary,
                                      fontSize: 10,
                                      fontFamily: 'monospace',
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    p['event'] ?? '',
                                    style: const TextStyle(color: AppColors.textSecondary, fontSize: 11.5),
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),

                  // Mandatory Disclaimer Note
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0x181F2636),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.borderSubtle),
                    ),
                    child: Text(
                      data.disclaimer,
                      style: const TextStyle(color: AppColors.textMuted, fontSize: 10.5, height: 1.4),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    ),
  );
  }

  Widget _buildStat(String label, String value, Color valueColor) {
    return Expanded(
      child: Column(
        children: [
          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textMuted, fontSize: 9.5, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 3),
          FittedBox(
            fit: BoxFit.scaleDown,
            child: Text(
              value,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: valueColor,
                fontSize: 12,
                fontWeight: FontWeight.w800,
                fontFamily: 'monospace',
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionCard({
    required IconData icon,
    required Color iconColor,
    required String title,
    required Widget content,
  }) {
    return IosGlassCard(
      borderRadius: 18,
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: iconColor, size: 14),
              const SizedBox(width: 7),
              Text(
                title,
                style: TextStyle(
                  color: iconColor,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          content,
        ],
      ),
    );
  }

  Widget _buildTimeframeRow(String tf, String desc) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 95,
          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
          decoration: BoxDecoration(
            color: const Color(0x351F2636),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            tf,
            style: const TextStyle(color: AppColors.primary, fontSize: 9.5, fontWeight: FontWeight.w700),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            desc,
            style: const TextStyle(color: AppColors.textPrimary, fontSize: 11.5, height: 1.35),
          ),
        ),
      ],
    );
  }

  Widget _buildScenarioCard(NewsScenarioModel sc) {
    final isHawkish = sc.label.contains('Kuat');
    final isDovish = sc.label.contains('Lemah');
    final Color cardColor = isHawkish
        ? AppColors.bearish
        : (isDovish ? AppColors.bullish : AppColors.primary);

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0x301F2636),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: cardColor.withValues(alpha: 0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Scenario Title
          Text(
            sc.label,
            style: TextStyle(
              color: cardColor,
              fontSize: 13,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.2,
            ),
          ),
          if (sc.condition.isNotEmpty) ...[
            const SizedBox(height: 6),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: cardColor.withValues(alpha: 0.14),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: cardColor.withValues(alpha: 0.3), width: 0.8),
              ),
              child: Text(
                sc.condition,
                style: TextStyle(
                  color: cardColor,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w700,
                  height: 1.35,
                ),
              ),
            ),
          ],
          const SizedBox(height: 10),
          _buildScenarioLine('Yield & DXY:', sc.yieldDxyReaction),
          const SizedBox(height: 4),
          _buildScenarioLine('Reaksi Emas:', sc.goldReaction),
          const SizedBox(height: 4),
          _buildScenarioLine('Target Area:', sc.targetArea),
          const SizedBox(height: 4),
          _buildScenarioLine('Batal Jika:', sc.invalidationLevel, isWarning: true),
        ],
      ),
    );
  }

  Widget _buildScenarioLine(String label, String value, {bool isWarning = false}) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 80,
          child: Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 10.5, fontWeight: FontWeight.w600)),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              color: isWarning ? AppColors.bearish : AppColors.textPrimary,
              fontSize: 11,
              fontWeight: isWarning ? FontWeight.w600 : FontWeight.w400,
            ),
          ),
        ),
      ],
    );
  }
}
