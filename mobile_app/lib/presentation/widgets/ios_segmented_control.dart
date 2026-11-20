import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

class IosSegmentedControl<T> extends StatelessWidget {
  final Map<T, String> items;
  final T selectedValue;
  final ValueChanged<T> onValueChanged;
  final bool fullWidth;

  const IosSegmentedControl({
    super.key,
    required this.items,
    required this.selectedValue,
    required this.onValueChanged,
    this.fullWidth = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(3.5),
      decoration: BoxDecoration(
        color: AppColors.surfaceInset,
        borderRadius: BorderRadius.circular(13),
        border: Border.all(color: AppColors.border, width: 0.8),
      ),
      child: Row(
        mainAxisSize: fullWidth ? MainAxisSize.max : MainAxisSize.min,
        children: items.entries.map((entry) {
          final isSelected = entry.key == selectedValue;
          final segment = GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: () => onValueChanged(entry.key),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOutCubic,
              alignment: fullWidth ? Alignment.center : null,
              padding: EdgeInsets.symmetric(
                horizontal: fullWidth ? 8 : 13,
                vertical: fullWidth ? 8.5 : 7,
              ),
              decoration: BoxDecoration(
                color: isSelected ? AppColors.surfaceElevated : Colors.transparent,
                borderRadius: BorderRadius.circular(9.5),
                boxShadow: isSelected
                    ? [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.35),
                          blurRadius: 6,
                          offset: const Offset(0, 2),
                        ),
                      ]
                    : null,
                border: isSelected
                    ? Border.all(color: AppColors.gold.withValues(alpha: 0.35), width: 0.8)
                    : null,
              ),
              child: Text(
                entry.value,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: isSelected ? AppColors.gold : AppColors.textMuted,
                  fontSize: 12,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                  letterSpacing: 0.1,
                ),
              ),
            ),
          );
          return fullWidth ? Expanded(child: segment) : segment;
        }).toList(),
      ),
    );
  }
}
