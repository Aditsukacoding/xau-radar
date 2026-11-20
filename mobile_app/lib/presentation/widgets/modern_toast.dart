import 'dart:async';
import 'dart:math';
import 'dart:ui';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

/// Ultra-modern iOS 18 top-floating glass notification banner (Overlay-based).
/// Drops cleanly below the AppBar with smooth spring entrance, tap/swipe-up dismiss,
/// and zero double-offset bugs over bottom navigation bars or cards.
class ModernToast {
  static OverlayEntry? _activeEntry;
  static Timer? _dismissTimer;

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
      icon: LucideIcons.badgeCheck,
      accentColor: const Color(0xFF10B981),
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
      icon: LucideIcons.triangleAlert,
      accentColor: const Color(0xFFEF4444),
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
      icon: LucideIcons.sparkles,
      accentColor: AppColors.primary,
      duration: duration,
    );
  }

  static void _removeCurrent() {
    _dismissTimer?.cancel();
    _dismissTimer = null;
    try {
      _activeEntry?.remove();
    } catch (_) {}
    _activeEntry = null;
  }

  static void _show({
    required BuildContext context,
    required String title,
    required String message,
    required IconData icon,
    required Color accentColor,
    required Duration duration,
  }) {
    final overlay = Overlay.maybeOf(context, rootOverlay: true);
    if (overlay == null) return;

    _removeCurrent();

    late final OverlayEntry entry;
    entry = OverlayEntry(
      builder: (ctx) => _TopFloatingToast(
        title: title,
        message: message,
        icon: icon,
        accentColor: accentColor,
        duration: duration,
        onDismissed: () {
          if (_activeEntry == entry) {
            _removeCurrent();
          }
        },
      ),
    );

    _activeEntry = entry;
    overlay.insert(entry);
  }
}

class _TopFloatingToast extends StatefulWidget {
  final String title;
  final String message;
  final IconData icon;
  final Color accentColor;
  final Duration duration;
  final VoidCallback onDismissed;

  const _TopFloatingToast({
    required this.title,
    required this.message,
    required this.icon,
    required this.accentColor,
    required this.duration,
    required this.onDismissed,
  });

  @override
  State<_TopFloatingToast> createState() => _TopFloatingToastState();
}

class _TopFloatingToastState extends State<_TopFloatingToast>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<Offset> _slide;
  late final Animation<double> _fade;
  Timer? _autoTimer;
  bool _dismissing = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 260),
      reverseDuration: const Duration(milliseconds: 200),
    );
    _slide = Tween<Offset>(
      begin: const Offset(0, -1.15),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOutCubic));
    _fade = CurvedAnimation(parent: _controller, curve: Curves.easeOut);

    _controller.forward();
    _autoTimer = Timer(widget.duration, _dismiss);
  }

  Future<void> _dismiss() async {
    if (_dismissing || !mounted) return;
    _dismissing = true;
    _autoTimer?.cancel();
    try {
      await _controller.reverse();
    } catch (_) {}
    widget.onDismissed();
  }

  @override
  void dispose() {
    _autoTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final mq = MediaQuery.of(context);
    final horizontalMargin = max(16.0, (mq.size.width - 460) / 2);
    // Cleanly positioned right under the 58px AppBar + safe top inset
    final topOffset = mq.padding.top + 66.0;

    return Positioned(
      top: topOffset,
      left: horizontalMargin,
      right: horizontalMargin,
      child: Material(
        color: Colors.transparent,
        child: SlideTransition(
          position: _slide,
          child: FadeTransition(
            opacity: _fade,
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: _dismiss,
              onVerticalDragEnd: (details) {
                if ((details.primaryVelocity ?? 0) < -100) {
                  _dismiss();
                }
              },
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: BackdropFilter(
                  filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
                    decoration: BoxDecoration(
                      color: const Color(0xF50F131D),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: widget.accentColor.withValues(alpha: 0.38),
                        width: 1.0,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: widget.accentColor.withValues(alpha: 0.16),
                          blurRadius: 20,
                          spreadRadius: -2,
                          offset: const Offset(0, 4),
                        ),
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.72),
                          blurRadius: 26,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 34,
                          height: 34,
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [
                                widget.accentColor.withValues(alpha: 0.25),
                                widget.accentColor.withValues(alpha: 0.08),
                              ],
                            ),
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: widget.accentColor.withValues(alpha: 0.48),
                              width: 1.0,
                            ),
                          ),
                          child: Center(
                            child: Icon(widget.icon, color: widget.accentColor, size: 17),
                          ),
                        ),
                        const SizedBox(width: 11),
                        Expanded(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                widget.title,
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w800,
                                  letterSpacing: 0.2,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                widget.message,
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 11.5,
                                  height: 1.32,
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 8),
                        const Icon(
                          LucideIcons.x,
                          color: AppColors.textMuted,
                          size: 14,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
