import 'package:flutter/material.dart';

class AppColors {
  // iOS 18 System Backgrounds (OLED Black & Layered System Fills)
  static const Color background = Color(0xFF000000); // True Apple OLED Black
  static const Color backgroundSecondary = Color(0xFF0D0E12);
  static const Color surface = Color(0xFF14171F); // Grouped Card Fill
  static const Color surfaceElevated = Color(0xFF1C202C); // Floating Modal Fill
  static const Color surfaceGlass = Color(0x35282F40); // 20% Translucent for Blur
  static const Color border = Color(0x28FFFFFF); // Ultra-fine 0.8px Apple Specular Border
  static const Color borderSubtle = Color(0x15FFFFFF);

  // iOS System Accents
  static const Color primary = Color(0xFF64D2FF); // Apple Neon Sky Cyan
  static const Color secondary = Color(0xFFBF5AF2); // Apple Purple
  static const Color appleBlue = Color(0xFF0A84FF); // Apple System Blue

  // iOS Market Vibrancy
  static const Color bullish = Color(0xFF30D158); // Apple System Vibrant Emerald
  static const Color bullishMuted = Color(0x2830D158);
  static const Color bullishGlow = Color(0x5530D158);

  static const Color bearish = Color(0xFFFF453A); // Apple System Vibrant Ruby Red
  static const Color bearishMuted = Color(0x28FF453A);
  static const Color bearishGlow = Color(0x55FF453A);

  static const Color neutral = Color(0xFFFFD60A); // Apple System Vibrant Amber Gold
  static const Color neutralMuted = Color(0x28FFD60A);
  static const Color neutralGlow = Color(0x55FFD60A);

  // Impact Levels
  static const Color impactHigh = Color(0xFFFF453A);
  static const Color impactMedium = Color(0xFFFF9F0A); // Apple Orange
  static const Color impactLow = Color(0xFF64D2FF);

  // iOS Typography Labels
  static const Color textPrimary = Color(0xFFFFFFFF); // 100% White
  static const Color textSecondary = Color(0xFFEBEBF5); // 80% Translucent White
  static const Color textMuted = Color(0xFF8E8E93); // Apple System Gray 1
  static const Color textTertiary = Color(0xFF636366); // Apple System Gray 2

  // Candle Chart Colors (Apple Stocks Style)
  static const Color candleUp = Color(0xFF30D158);
  static const Color candleDown = Color(0xFFFF453A);
  static const Color maFast = Color(0xFF64D2FF);
  static const Color maSlow = Color(0xFFFF9F0A);
  static const Color supportLine = Color(0xFF30D158);
  static const Color resistanceLine = Color(0xFFFF453A);
}
