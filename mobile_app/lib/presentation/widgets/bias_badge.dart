import 'package:flutter/cupertino.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../core/constants/app_colors.dart';

class BiasBadge extends StatelessWidget {
  final String bias; // BULLISH, BEARISH, NEUTRAL
  final bool isLarge;
  final int? confidenceScore;

  const BiasBadge({
    super.key,
    required this.bias,
    this.isLarge = false,
    this.confidenceScore,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color border;
    Color textColor;
    IconData icon;
    String label;

    final String strengthSuffix = confidenceScore != null
        ? (confidenceScore! >= 75
            ? ' (STRONG)'
            : (confidenceScore! >= 60 ? ' (MODERATE)' : ''))
        : '';

    switch (bias.toUpperCase()) {
      case 'BULLISH':
        bg = AppColors.bullishMuted;
        border = AppColors.bullish;
        textColor = AppColors.bullish;
        icon = LucideIcons.arrowUpRight;
        label = isLarge ? 'BULLISH BIAS$strengthSuffix' : 'BULLISH';
        break;
      case 'BEARISH':
        bg = AppColors.bearishMuted;
        border = AppColors.bearish;
        textColor = AppColors.bearish;
        icon = LucideIcons.arrowDownRight;
        label = isLarge ? 'BEARISH BIAS$strengthSuffix' : 'BEARISH';
        break;
      default:
        bg = AppColors.neutralMuted;
        border = AppColors.gold;
        textColor = AppColors.gold;
        icon = LucideIcons.minus;
        label = isLarge ? 'NEUTRAL BIAS' : 'NETRAL';
    }

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isLarge ? 12 : 9,
        vertical: isLarge ? 5.5 : 3.5,
      ),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: border.withValues(alpha: 0.45), width: 0.9),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: textColor,
            size: isLarge ? 14 : 12,
          ),
          const SizedBox(width: 5),
          Flexible(
            child: Text(
              label,
              style: TextStyle(
                color: textColor,
                fontWeight: FontWeight.w800,
                fontSize: isLarge ? 11.5 : 10.5,
                letterSpacing: 0.5,
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
