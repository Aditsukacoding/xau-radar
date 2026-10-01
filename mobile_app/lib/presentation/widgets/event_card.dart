import 'package:flutter/cupertino.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/wib_date_time.dart';
import '../../data/models/economic_event_model.dart';
import 'ios_glass_card.dart';

class EventCard extends StatelessWidget {
  final EconomicEventModel event;
  final VoidCallback? onTap;

  const EventCard({super.key, required this.event, this.onTap});

  @override
  Widget build(BuildContext context) {
    Color impactColor;
    switch (event.impactLevel.toUpperCase()) {
      case 'HIGH':
        impactColor = AppColors.impactHigh;
        break;
      case 'MEDIUM':
        impactColor = AppColors.impactMedium;
        break;
      default:
        impactColor = AppColors.impactLow;
    }

    final isUpcoming = event.scheduledAt.isAfter(DateTime.now().toUtc());
    final timeDiff = event.scheduledAt.difference(DateTime.now().toUtc());
    final hasActual = event.actualValue != null && event.actualValue!.trim().isNotEmpty;
    final isSpeechOrNonNumeric = event.eventTitle.toLowerCase().contains('speaks') ||
        event.eventTitle.toLowerCase().contains('statement') ||
        event.eventTitle.toLowerCase().contains('press conference') ||
        event.eventTitle.toLowerCase().contains('meeting') ||
        event.eventTitle.toLowerCase().contains('minutes') ||
        event.eventTitle.toLowerCase().contains('auction');

    String timeHint;
    Color statusColor;
    Color statusBg;
    IconData statusIcon;

    if (hasActual) {
      timeHint = 'Dirilis';
      statusColor = const Color(0xFF00E676);
      statusBg = const Color(0x2200E676);
      statusIcon = CupertinoIcons.checkmark_alt_circle_fill;
    } else if (isUpcoming) {
      if (timeDiff.inHours < 1) {
        timeHint = 'dalam ${timeDiff.inMinutes}m lagi';
      } else if (timeDiff.inHours < 24) {
        timeHint = 'dalam ${timeDiff.inHours}j lagi';
      } else {
        timeHint = 'dalam ${timeDiff.inDays}h lagi';
      }
      statusColor = AppColors.primary;
      statusBg = AppColors.primary.withValues(alpha: 0.12);
      statusIcon = CupertinoIcons.clock;
    } else if (isSpeechOrNonNumeric) {
      timeHint = 'Selesai (Pidato)';
      statusColor = AppColors.textMuted;
      statusBg = const Color(0x208E9BAE);
      statusIcon = CupertinoIcons.mic_fill;
    } else {
      timeHint = 'Menunggu Rilis';
      statusColor = const Color(0xFFFFB300);
      statusBg = const Color(0x22FFB300);
      statusIcon = CupertinoIcons.hourglass;
    }

    // Determine Aktual display text and style
    String actualDisplayText;
    Color actualDisplayColor;
    bool actualIsBold;

    if (hasActual) {
      actualDisplayText = event.actualValue!;
      actualDisplayColor = const Color(0xFF00E676);
      actualIsBold = true;
    } else if (isUpcoming) {
      actualDisplayText = 'Belum Rilis';
      actualDisplayColor = AppColors.textMuted;
      actualIsBold = false;
    } else if (isSpeechOrNonNumeric) {
      actualDisplayText = 'N/A';
      actualDisplayColor = AppColors.textMuted.withValues(alpha: 0.7);
      actualIsBold = false;
    } else {
      actualDisplayText = 'Pending';
      actualDisplayColor = const Color(0xFFFFB300);
      actualIsBold = false;
    }

    return IosGlassCard(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      padding: const EdgeInsets.all(16),
      borderRadius: 18,
      onTap: onTap,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Row: Currency, Impact Badge, Countdown/Status
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0x402C344A),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: AppColors.borderSubtle),
                    ),
                    child: Text(
                      event.currency,
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                    decoration: BoxDecoration(
                      color: impactColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: impactColor.withValues(alpha: 0.4), width: 0.8),
                    ),
                    child: Text(
                      '${event.impactLevel} IMPACT',
                      style: TextStyle(
                        color: impactColor,
                        fontSize: 9.5,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3.5),
                decoration: BoxDecoration(
                  color: statusBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: statusColor.withValues(alpha: 0.3), width: 0.8),
                ),
                child: Row(
                  children: [
                    Icon(statusIcon, color: statusColor, size: 12),
                    const SizedBox(width: 5),
                    Text(
                      timeHint,
                      style: TextStyle(
                        color: statusColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          // Event Title
          Text(
            event.eventTitle,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 14.5,
              fontWeight: FontWeight.w600,
              letterSpacing: -0.2,
            ),
          ),
          const SizedBox(height: 4),

          // Scheduled Date string (WIB)
          Text(
            event.scheduledAt.formatWibWithDay(),
            style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
          ),
          const SizedBox(height: 14),

          // Comparison Metrics Row (iOS Inset Pill)
          Container(
            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
            decoration: BoxDecoration(
              color: const Color(0x351F2636),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.borderSubtle),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildDataCol(
                  'Aktual',
                  actualDisplayText,
                  customColor: actualDisplayColor,
                  isBold: actualIsBold,
                ),
                Container(width: 0.8, height: 24, color: AppColors.borderSubtle),
                _buildDataCol('Forecast', event.forecastValue ?? '-'),
                Container(width: 0.8, height: 24, color: AppColors.borderSubtle),
                _buildDataCol('Sebelumnya', event.previousValue ?? '-'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDataCol(
    String label,
    String value, {
    Color? customColor,
    bool isBold = true,
  }) {
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(color: AppColors.textMuted, fontSize: 10, letterSpacing: 0.2),
        ),
        const SizedBox(height: 3),
        Text(
          value,
          style: TextStyle(
            color: customColor ?? AppColors.textPrimary,
            fontSize: (value.length > 8) ? 11 : 13,
            fontWeight: isBold ? FontWeight.w700 : FontWeight.w500,
            fontStyle: !isBold ? FontStyle.italic : FontStyle.normal,
            fontFamily: isBold ? 'monospace' : null,
          ),
        ),
      ],
    );
  }
}
