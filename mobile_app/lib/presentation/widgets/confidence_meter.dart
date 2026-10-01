import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

class ConfidenceMeter extends StatelessWidget {
  final int score; // 0 to 100
  final double size;

  const ConfidenceMeter({
    super.key,
    required this.score,
    this.size = 100,
  });

  @override
  Widget build(BuildContext context) {
    Color meterColor;
    String label;

    if (score >= 75) {
      meterColor = AppColors.bullish;
      label = 'Sangat Tinggi';
    } else if (score >= 60) {
      meterColor = AppColors.primary;
      label = 'Tinggi';
    } else if (score >= 45) {
      meterColor = AppColors.neutral;
      label = 'Moderat';
    } else {
      meterColor = AppColors.bearish;
      label = 'Rendah';
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
              // Background track
              SizedBox(
                width: size,
                height: size,
                child: CircularProgressIndicator(
                  value: 1.0,
                  strokeWidth: 9,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    const Color(0x35283042),
                  ),
                ),
              ),
              // Value arc with glow
              SizedBox(
                width: size,
                height: size,
                child: TweenAnimationBuilder<double>(
                  tween: Tween<double>(begin: 0.0, end: score / 100.0),
                  duration: const Duration(milliseconds: 1400),
                  curve: Curves.easeOutCubic,
                  builder: (context, value, child) {
                    return CircularProgressIndicator(
                      value: value,
                      strokeWidth: 9,
                      strokeCap: StrokeCap.round,
                      valueColor: AlwaysStoppedAnimation<Color>(meterColor),
                    );
                  },
                ),
              ),
              // Inner Text
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '$score%',
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: size * 0.25,
                      fontWeight: FontWeight.w800,
                      letterSpacing: -0.5,
                    ),
                  ),
                  Text(
                    'CONFIDENCE',
                    style: TextStyle(
                      color: AppColors.textMuted,
                      fontSize: size * 0.08,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.0,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
          decoration: BoxDecoration(
            color: meterColor.withValues(alpha: 0.15),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: meterColor.withValues(alpha: 0.4), width: 0.8),
          ),
          child: Text(
            label,
            style: TextStyle(
              color: meterColor,
              fontWeight: FontWeight.w700,
              fontSize: 10.5,
              letterSpacing: 0.2,
            ),
          ),
        ),
      ],
    );
  }
}
