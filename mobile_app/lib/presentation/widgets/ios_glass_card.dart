import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

/// High-performance Obsidian & Gold iOS 18 glass card.
/// Uses crisp layered gradients & subtle glow borders without per-card BackdropFilter
/// (eliminating heavy WebGL/CanvasKit blur passes during scroll for smooth 60fps).
class IosGlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final EdgeInsetsGeometry margin;
  final double borderRadius;
  final Color? glowColor;
  final Color? borderColor;
  final VoidCallback? onTap;

  const IosGlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.margin = EdgeInsets.zero,
    this.borderRadius = 20,
    this.glowColor,
    this.borderColor,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final card = RepaintBoundary(
      child: Container(
        margin: margin,
        padding: padding,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Color(0xFF141822),
              Color(0xFF10131B),
            ],
          ),
          borderRadius: BorderRadius.circular(borderRadius),
          border: Border.all(
            color: borderColor ?? AppColors.border,
            width: 0.85,
          ),
          boxShadow: [
            if (glowColor != null)
              BoxShadow(
                color: glowColor!.withValues(alpha: 0.10),
                blurRadius: 20,
                spreadRadius: -2,
                offset: const Offset(0, 5),
              )
            else
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.42),
                blurRadius: 14,
                spreadRadius: -3,
                offset: const Offset(0, 6),
              ),
          ],
        ),
        child: child,
      ),
    );

    if (onTap == null) return card;

    return _TappableScaleCard(onTap: onTap!, child: card);
  }
}

class _TappableScaleCard extends StatefulWidget {
  final VoidCallback onTap;
  final Widget child;

  const _TappableScaleCard({required this.onTap, required this.child});

  @override
  State<_TappableScaleCard> createState() => _TappableScaleCardState();
}

class _TappableScaleCardState extends State<_TappableScaleCard> {
  bool _pressed = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTapDown: (_) => setState(() => _pressed = true),
      onTapUp: (_) {
        setState(() => _pressed = false);
        widget.onTap();
      },
      onTapCancel: () => setState(() => _pressed = false),
      child: AnimatedScale(
        scale: _pressed ? 0.985 : 1.0,
        duration: const Duration(milliseconds: 100),
        curve: Curves.easeOutCubic,
        child: widget.child,
      ),
    );
  }
}
