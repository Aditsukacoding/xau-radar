import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';

class IosSegmentedControl<T> extends StatelessWidget {
  final Map<T, String> items;
  final T selectedValue;
  final ValueChanged<T> onValueChanged;

  const IosSegmentedControl({
    super.key,
    required this.items,
    required this.selectedValue,
    required this.onValueChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: const Color(0x35283042),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.borderSubtle, width: 0.8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: items.entries.map((entry) {
          final isSelected = entry.key == selectedValue;
          return GestureDetector(
            onTap: () => onValueChanged(entry.key),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOutCubic,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: isSelected ? const Color(0xFF2C344A) : Colors.transparent,
                borderRadius: BorderRadius.circular(9),
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
                    ? Border.all(color: AppColors.primary.withValues(alpha: 0.4), width: 0.8)
                    : null,
              ),
              child: Text(
                entry.value,
                style: TextStyle(
                  color: isSelected ? AppColors.textPrimary : AppColors.textMuted,
                  fontSize: 11.5,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                  letterSpacing: 0.2,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
