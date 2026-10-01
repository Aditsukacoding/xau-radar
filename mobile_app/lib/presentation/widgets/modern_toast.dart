import 'dart:math';
import 'dart:ui';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

/// Ultra-modern floating glass capsule toast / snackbar notification
/// Styled with Apple VisionOS / iOS 18 dark glassmorphism and subtle glowing borders.
class ModernToast {
  static void showSuccess(
    BuildContext context,
    String message, {
    String title = 'Berhasil Diperbarui',
    Duration duration = const Duration(seconds: 3),
  }) {
    _show(
      context: context,
      title: title,
      message: message,
      icon: CupertinoIcons.checkmark_seal_fill,
      accentColor: const Color(0xFF10B981), // Emerald glow
      duration: duration,
    );
  }

  static void showError(
    BuildContext context,
    String message, {
    String title = 'Terjadi Kesalahan',
    Duration duration = const Duration(seconds: 4),
  }) {
    _show(
      context: context,
      title: title,
      message: message,
      icon: CupertinoIcons.exclamationmark_triangle_fill,
      accentColor: const Color(0xFFEF4444), // Crimson glow
      duration: duration,
    );
  }

  static void showInfo(
    BuildContext context,
    String message, {
    String title = 'Sinkronisasi Real-Time',
    Duration duration = const Duration(seconds: 3),
  }) {
    _show(
      context: context,
      title: title,
      message: message,
      icon: CupertinoIcons.sparkles,
      accentColor: AppColors.primary, // Gold #F59E0B glow
      duration: duration,
    );
  }

  static void _show({
    required BuildContext context,
    required String title,
    required String message,
    required IconData icon,
    required Color accentColor,
    required Duration duration,
  }) {
    final screenWidth = MediaQuery.of(context).size.width;
    final horizontalMargin = max(16.0, (screenWidth - 480) / 2);

    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        elevation: 0,
        backgroundColor: Colors.transparent,
        behavior: SnackBarBehavior.floating,
        margin: EdgeInsets.only(
          left: horizontalMargin,
          right: horizontalMargin,
          bottom: max(24.0, MediaQuery.of(context).padding.bottom + 82.0),
        ),
        duration: duration,
        padding: EdgeInsets.zero,
        content: ClipRRect(
          borderRadius: BorderRadius.circular(18),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 25, sigmaY: 25),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xF20F131D), // Dark Obsidian Glass
                borderRadius: BorderRadius.circular(18),
                border: Border.all(
                  color: accentColor.withValues(alpha: 0.35),
                  width: 1.2,
                ),
                boxShadow: [
                  BoxShadow(
                    color: accentColor.withValues(alpha: 0.18),
                    blurRadius: 24,
                    spreadRadius: -2,
                    offset: const Offset(0, 4),
                  ),
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.8),
                    blurRadius: 30,
                    offset: const Offset(0, 8),
                  ),
                ],
              ),
              child: Row(
                children: [
                  // Leading Glowing Icon Badge
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          accentColor.withValues(alpha: 0.25),
                          accentColor.withValues(alpha: 0.08),
                        ],
                      ),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: accentColor.withValues(alpha: 0.5),
                        width: 1.0,
                      ),
                    ),
                    child: Center(
                      child: Icon(icon, color: accentColor, size: 18),
                    ),
                  ),
                  const SizedBox(width: 12),

                  // Title & Message Content
                  Expanded(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          title,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 0.2,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          message,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 11.5,
                            height: 1.3,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
