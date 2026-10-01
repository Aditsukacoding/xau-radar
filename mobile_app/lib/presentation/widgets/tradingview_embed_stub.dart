import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

Widget buildTradingViewWidget({
  required String symbol,
  required String interval,
  double height = 480,
}) {
  return Container(
    height: height,
    width: double.infinity,
    decoration: BoxDecoration(
      color: const Color(0xFF131722),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
    ),
    child: Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.show_chart, color: AppColors.primary, size: 40),
          const SizedBox(height: 12),
          Text(
            'TradingView Live Chart ($symbol)',
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
          ),
          const SizedBox(height: 6),
          const Text(
            'Mode web aktif menampilkan real-time widget resmi TradingView.',
            style: TextStyle(color: AppColors.textMuted, fontSize: 12),
          ),
        ],
      ),
    ),
  );
}
