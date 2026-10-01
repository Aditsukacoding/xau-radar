import 'package:flutter/cupertino.dart';
import '../../core/constants/app_colors.dart';
import 'ios_glass_card.dart';

class DisclaimerBanner extends StatelessWidget {
  final String? customText;

  const DisclaimerBanner({super.key, this.customText});

  @override
  Widget build(BuildContext context) {
    return IosGlassCard(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(14),
      borderRadius: 16,
      borderColor: AppColors.neutral.withValues(alpha: 0.3),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              color: AppColors.neutral.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(
              CupertinoIcons.shield_lefthalf_fill,
              color: AppColors.neutral,
              size: 16,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'PENAFIAN HUKUM & RISIKO PASAR',
                  style: TextStyle(
                    color: AppColors.neutral,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.6,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  customText ??
                      'Seluruh analisis, skor keyakinan, dan indikator ini dihasilkan secara algoritmik '
                      'untuk tujuan edukasi pasar. Sistem BUKAN saran finansial atau rekomendasi eksekusi transaksi. '
                      'Trading memiliki risiko kerugian modal yang tinggi.',
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
