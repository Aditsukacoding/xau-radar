import 'package:flutter/cupertino.dart';
import '../../core/constants/app_colors.dart';

class BiasBadge extends StatelessWidget {
  final String bias; // BULLISH, BEARISH, NEUTRAL
  final bool isLarge;

  const BiasBadge({
    super.key,
    required this.bias,
    this.isLarge = false,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color border;
    Color textColor;
    IconData icon;
    String label;

    switch (bias.toUpperCase()) {
      case 'BULLISH':
        bg = AppColors.bullishMuted;
        border = AppColors.bullish;
        textColor = AppColors.bullish;
        icon = CupertinoIcons.arrow_up_right;
        label = 'BULLISH';
        break;
      case 'BEARISH':
        bg = AppColors.bearishMuted;
        border = AppColors.bearish;
        textColor = AppColors.bearish;
        icon = CupertinoIcons.arrow_down_right;
        label = 'BEARISH';
        break;
      default:
        bg = AppColors.neutralMuted;
        border = AppColors.neutral;
        textColor = AppColors.neutral;
        icon = CupertinoIcons.equal;
        label = 'NETRAL';
    }

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isLarge ? 14 : 10,
        vertical: isLarge ? 6 : 4,
      ),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: border.withValues(alpha: 0.6), width: isLarge ? 1.2 : 0.8),
        boxShadow: [
          BoxShadow(
            color: border.withValues(alpha: 0.25),
            blurRadius: isLarge ? 14 : 8,
            spreadRadius: 0.5,
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: textColor,
            size: isLarge ? 18 : 13,
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: textColor,
              fontWeight: FontWeight.w700,
              fontSize: isLarge ? 13 : 11,
              letterSpacing: 0.8,
            ),
          ),
        ],
      ),
    );
  }
}
