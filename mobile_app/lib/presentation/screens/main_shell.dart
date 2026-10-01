import 'dart:ui';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/network/api_service.dart';
import 'dashboard_screen.dart';
import 'fundamental_screen.dart';
import 'geopolitical_screen.dart';
import 'technical_screen.dart';
import 'analysis_detail_screen.dart';
import '../widgets/modern_toast.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  void _onTabSelected(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  void _showServerSettingsDialog() {
    final controller = TextEditingController(text: ApiService.baseUrl);
    showGeneralDialog(
      context: context,
      barrierDismissible: true,
      barrierLabel: 'ServerSettings',
      barrierColor: Colors.black.withValues(alpha: 0.72),
      transitionDuration: const Duration(milliseconds: 260),
      pageBuilder: (context, anim1, anim2) {
        return Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Material(
                color: Colors.transparent,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(24),
                  child: BackdropFilter(
                    filter: ImageFilter.blur(sigmaX: 25, sigmaY: 25),
                    child: Container(
                      padding: const EdgeInsets.all(22),
                      decoration: BoxDecoration(
                        color: const Color(0xF210141F),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: AppColors.primary.withValues(alpha: 0.35),
                          width: 1.2,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.primary.withValues(alpha: 0.12),
                            blurRadius: 30,
                            spreadRadius: -4,
                          ),
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.8),
                            blurRadius: 35,
                          ),
                        ],
                      ),
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: AppColors.primary.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(color: AppColors.primary.withValues(alpha: 0.35)),
                                ),
                                child: const Icon(CupertinoIcons.slider_horizontal_3, color: AppColors.primary, size: 18),
                              ),
                              const SizedBox(width: 12),
                              const Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Konfigurasi Server API',
                                      style: TextStyle(
                                        color: AppColors.textPrimary,
                                        fontSize: 16,
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                    Text(
                                      'Trading Analytics Engine',
                                      style: TextStyle(color: AppColors.textMuted, fontSize: 11),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 18),
                          const Text(
                            'Base URL Endpoint:',
                            style: TextStyle(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 8),
                          CupertinoTextField(
                            controller: controller,
                            placeholder: 'http://127.0.0.1:8000/api/v1',
                            style: const TextStyle(color: Colors.white, fontSize: 13, fontFamily: 'monospace'),
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                            decoration: BoxDecoration(
                              color: const Color(0xFF161C28),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppColors.borderSubtle),
                            ),
                          ),
                          const SizedBox(height: 22),
                          Row(
                            children: [
                              Expanded(
                                child: CupertinoButton(
                                  padding: const EdgeInsets.symmetric(vertical: 11),
                                  color: const Color(0xFF1B2130),
                                  borderRadius: BorderRadius.circular(12),
                                  onPressed: () => Navigator.pop(context),
                                  child: const Text('Batal', style: TextStyle(color: AppColors.textMuted, fontSize: 13, fontWeight: FontWeight.w700)),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: CupertinoButton(
                                  padding: const EdgeInsets.symmetric(vertical: 11),
                                  color: AppColors.primary,
                                  borderRadius: BorderRadius.circular(12),
                                  onPressed: () {
                                    if (controller.text.trim().isNotEmpty) {
                                      ApiService.updateBaseUrl(controller.text.trim());
                                      Navigator.pop(context);
                                      setState(() {});
                                      ModernToast.showSuccess(
                                        context,
                                        'Base URL server API aktif: ${ApiService.baseUrl}',
                                        title: 'Server Tersimpan',
                                      );
                                    }
                                  },
                                  child: const Text('Simpan', style: TextStyle(color: Colors.black, fontSize: 13, fontWeight: FontWeight.w800)),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        );
      },
        transitionBuilder: (context, anim1, anim2, child) {
          final curve = CurvedAnimation(parent: anim1, curve: Curves.easeOutBack);
          return ScaleTransition(
            scale: Tween<double>(begin: 0.92, end: 1.0).animate(curve),
            child: FadeTransition(opacity: anim1, child: child),
          );
        },
      );
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> screens = [
      DashboardScreen(onNavigateTab: _onTabSelected),
      const FundamentalScreen(),
      const GeopoliticalScreen(),
      const TechnicalScreen(),
      const AnalysisDetailScreen(),
    ];

    return Scaffold(
      backgroundColor: AppColors.background,
      extendBody: true, // Allow body to scroll behind floating frosted glass bar
      extendBodyBehindAppBar: true, // Allow body behind glass appbar
      appBar: PreferredSize(
        preferredSize: const Size.fromHeight(56),
        child: ClipRect(
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 25, sigmaY: 25),
            child: AppBar(
              backgroundColor: Colors.black.withValues(alpha: 0.65),
              elevation: 0,
              scrolledUnderElevation: 0,
              title: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppColors.primary, AppColors.secondary],
                      ),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(CupertinoIcons.waveform_path_ecg, color: Colors.black, size: 16),
                  ),
                  const SizedBox(width: 10),
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'XAU/USD RADAR',
                        style: TextStyle(
                          fontSize: 14.5,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.8,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      Text(
                        'Apple Style 3-Pillar Bias Engine',
                        style: TextStyle(
                          fontSize: 9.5,
                          fontWeight: FontWeight.w500,
                          color: AppColors.primary,
                          letterSpacing: 0.2,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              actions: [
                IconButton(
                  icon: const Icon(CupertinoIcons.gear_alt, color: AppColors.textMuted, size: 20),
                  tooltip: 'Konfigurasi IP',
                  onPressed: _showServerSettingsDialog,
                ),
                const SizedBox(width: 6),
              ],
            ),
          ),
        ),
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: screens,
      ),
      // Floating iOS Frosted Glass Tab Bar
      bottomNavigationBar: SafeArea(
        child: Container(
          margin: const EdgeInsets.fromLTRB(18, 0, 18, 12),
          height: 64,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(32),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.6),
                blurRadius: 24,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(32),
            child: BackdropFilter(
              filter: ImageFilter.blur(sigmaX: 30, sigmaY: 30),
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0x75161B26),
                  borderRadius: BorderRadius.circular(32),
                  border: Border.all(color: AppColors.border, width: 0.8),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    _buildNavItem(0, CupertinoIcons.compass, CupertinoIcons.compass_fill, 'Pasar'),
                    _buildNavItem(1, CupertinoIcons.calendar, CupertinoIcons.calendar_today, 'Kalender'),
                    _buildNavItem(2, CupertinoIcons.globe, CupertinoIcons.globe, 'Berita'),
                    _buildNavItem(3, CupertinoIcons.chart_bar_alt_fill, CupertinoIcons.chart_bar_alt_fill, 'Teknikal'),
                    _buildNavItem(4, CupertinoIcons.sparkles, CupertinoIcons.sparkles, 'Sintesis'),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(int index, IconData outlineIcon, IconData filledIcon, String label) {
    final isSelected = _currentIndex == index;
    return GestureDetector(
      onTap: () => _onTabSelected(index),
      behavior: HitTestBehavior.opaque,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary.withValues(alpha: 0.15) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isSelected ? filledIcon : outlineIcon,
              color: isSelected ? AppColors.primary : AppColors.textMuted,
              size: 21,
            ),
            const SizedBox(height: 3),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? AppColors.primary : AppColors.textMuted,
                fontSize: 10,
                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                letterSpacing: 0.2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
