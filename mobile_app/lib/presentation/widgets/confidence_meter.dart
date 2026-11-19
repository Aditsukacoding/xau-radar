import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/theme/app_theme.dart';

class ConfidenceMeter extends StatelessWidget {
  final int score; // 0 to 100
  final double size;
  final bool showBottomBadge;
  final String? bias;

  const ConfidenceMeter({
    super.key,
    required this.score,
    this.size = 86,
    this.showBottomBadge = false,
    this.bias,
  });

  @override
  Widget build(BuildContext context) {
    Color meterColor;
    String label;

    final upperBias = bias?.toUpperCase();
    if (upperBias == 'BEARISH') {
      meterColor = AppColors.bearish;
    } else if (upperBias == 'NEUTRAL') {
      meterColor = AppColors.gold;
    } else if (score >= 70) {
      meterColor = AppColors.bullish;
    } else if (score >= 55) {
      meterColor = AppColors.gold;
    } else {
      meterColor = AppColors.bearish;
    }

    if (score >= 75) {
      label = 'Strong';
    } else if (score >= 60) {
      label = 'High';
    } else if (score >= 45) {
      label = 'Moderate';
    } else {
      label = 'Low';
    }

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Crisp Obsidian Track
              SizedBox(
                width: size,
                height: size,
                child: const CircularProgressIndicator(
                  value: 1.0,
                  strokeWidth: 7.5,
                  valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF1A1F2C)),
                ),
              ),
              // Animated High-Contrast Arc
              SizedBox(
                width: size,
                height: size,
                child: TweenAnimationBuilder<double>(
                  tween: Tween<double>(begin: 0.0, end: (score.clamp(0, 100)) / 100.0),
                  duration: const Duration(milliseconds: 1100),
                  curve: Curves.easeOutCubic,
                  builder: (context, value, child) {
                    return CircularProgressIndicator(
                      value: value,
                      strokeWidth: 7.5,
                      strokeCap: StrokeCap.round,
                      valueColor: AlwaysStoppedAnimation<Color>(meterColor),
                    );
                  },
                ),
              ),
              // Center Numeric Readout
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '$score%',
                    style: AppTypography.mono(
                      color: AppColors.textPrimary,
                      fontSize: size * 0.255,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.6,
                    ),
                  ),
                  const SizedBox(height: 1),
                  Text(
                    'CONFIDENCE',
                    style: TextStyle(
                      color: AppColors.textMuted,
                      fontSize: size * 0.085,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.8,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        if (showBottomBadge) ...[
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
            decoration: BoxDecoration(
              color: meterColor.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: meterColor.withValues(alpha: 0.35), width: 0.8),
            ),
            child: Text(
              label,
              style: TextStyle(
                color: meterColor,
                fontWeight: FontWeight.w700,
                fontSize: 10,
                letterSpacing: 0.3,
              ),
            ),
          ),
        ],
      ],
    );
  }
}
