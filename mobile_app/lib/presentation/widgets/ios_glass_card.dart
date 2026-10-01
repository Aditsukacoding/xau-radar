import 'dart:ui';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

class IosGlassCard extends StatefulWidget {
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
    this.padding = const EdgeInsets.all(16),
    this.margin = EdgeInsets.zero,
    this.borderRadius = 20,
    this.glowColor,
    this.borderColor,
    this.onTap,
  });

  @override
  State<IosGlassCard> createState() => _IosGlassCardState();
}

class _IosGlassCardState extends State<IosGlassCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 100),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 0.98).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    Widget content = Container(
      margin: widget.margin,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(widget.borderRadius),
        boxShadow: [
          if (widget.glowColor != null)
            BoxShadow(
              color: widget.glowColor!.withValues(alpha: 0.15),
              blurRadius: 24,
              spreadRadius: 2,
              offset: const Offset(0, 4),
            )
          else
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.45),
              blurRadius: 18,
              offset: const Offset(0, 6),
            ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(widget.borderRadius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            padding: widget.padding,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  const Color(0x35283042),
                  const Color(0x18141824),
                ],
              ),
              borderRadius: BorderRadius.circular(widget.borderRadius),
              border: Border.all(
                color: widget.borderColor ?? AppColors.border,
                width: 0.8,
              ),
            ),
            child: widget.child,
          ),
        ),
      ),
    );

    if (widget.onTap != null) {
      return GestureDetector(
        onTapDown: (_) => _controller.forward(),
        onTapUp: (_) {
          _controller.reverse();
          widget.onTap!();
        },
        onTapCancel: () => _controller.reverse(),
        child: ScaleTransition(scale: _scaleAnimation, child: content),
      );
    }

    return content;
  }
}
