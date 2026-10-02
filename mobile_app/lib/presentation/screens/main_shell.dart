import 'dart:math';
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
      useRootNavigator: true,
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
      DashboardScreen(
        onNavigateTab: _onTabSelected,
        onOpenSettings: _showServerSettingsDialog,
      ),
      const FundamentalScreen(),
      const GeopoliticalScreen(),
      const TechnicalScreen(),
      const AnalysisDetailScreen(),
    ];

    return Scaffold(
      backgroundColor: AppColors.background,
      extendBody: true, // Allow body to scroll behind floating frosted glass bottom bar
      extendBodyBehindAppBar: false, // Clean natural layout: body starts directly below the AppBar
      appBar: AppBar(
        backgroundColor: const Color(0xEB0A0D14),
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        title: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: _showServerSettingsDialog,
          child: Row(
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
                mainAxisSize: MainAxisSize.min,
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
        ),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Center(
              child: IconButton(
                onPressed: _showServerSettingsDialog,
                iconSize: 20,
                tooltip: 'Pengaturan Server',
                style: IconButton.styleFrom(
                  backgroundColor: const Color(0x351F2636),
                  minimumSize: const Size(44, 44),
                  padding: EdgeInsets.zero,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                    side: BorderSide(color: AppColors.primary.withValues(alpha: 0.7), width: 1.2),
                  ),
                ),
                icon: const Icon(
                  CupertinoIcons.gear_alt_fill,
                  color: AppColors.primary,
                ),
              ),
            ),
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: screens,
      ),
      // Authentic iPhone-style Tab Bar
      bottomNavigationBar: _IosTabBar(
        currentIndex: _currentIndex,
        onTap: _onTabSelected,
      ),
    );
  }
}

// ─── Native iPhone-style Tab Bar ─────────────────────────────────────────────
class _IosTabBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;

  const _IosTabBar({required this.currentIndex, required this.onTap});

  static const _tabs = [
    _TabItem(outlineIcon: CupertinoIcons.compass,              filledIcon: CupertinoIcons.compass_fill,          label: 'Pasar'),
    _TabItem(outlineIcon: CupertinoIcons.calendar,             filledIcon: CupertinoIcons.calendar_today,        label: 'Kalender'),
    _TabItem(outlineIcon: CupertinoIcons.globe,                filledIcon: CupertinoIcons.globe,                 label: 'Berita'),
    _TabItem(outlineIcon: CupertinoIcons.chart_bar_alt_fill,   filledIcon: CupertinoIcons.chart_bar_alt_fill,    label: 'Teknikal'),
    _TabItem(outlineIcon: CupertinoIcons.sparkles,             filledIcon: CupertinoIcons.sparkles,              label: 'Sintesis'),
  ];

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final rawBottom = mediaQuery.padding.bottom;
    final isMobile = mediaQuery.size.width < 768;
    // On iPhone (Safari / PWA / Face ID devices), rawBottom may report 0 in browser mode.
    // Enforcing a baseline clearance of 28-34pt ensures the navbar icons and text
    // sit comfortably above the iOS Home Indicator swipe bar.
    final double safeBottom = isMobile ? max(rawBottom, 28.0) : (rawBottom > 0 ? rawBottom : 10.0);

    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 30, sigmaY: 30),
        child: Container(
          decoration: BoxDecoration(
            // Authentic iOS frosted dark vibrancy (UITabBar dark)
            color: const Color(0xCC000000),
            border: Border(
              top: BorderSide(
                color: Colors.white.withValues(alpha: 0.13),
                width: 0.4,
              ),
            ),
          ),
          height: 50.0 + safeBottom,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: List.generate(_tabs.length, (i) {
              final tab = _tabs[i];
              final selected = i == currentIndex;
              return Expanded(
                child: _IosTabItemWidget(
                  tab: tab,
                  selected: selected,
                  safeBottom: safeBottom,
                  onTap: () => onTap(i),
                ),
              );
            }),
          ),
        ),
      ),
    );
  }
}

class _TabItem {
  final IconData outlineIcon;
  final IconData filledIcon;
  final String label;
  const _TabItem({required this.outlineIcon, required this.filledIcon, required this.label});
}

class _IosTabItemWidget extends StatefulWidget {
  final _TabItem tab;
  final bool selected;
  final double safeBottom;
  final VoidCallback onTap;

  const _IosTabItemWidget({
    required this.tab,
    required this.selected,
    required this.safeBottom,
    required this.onTap,
  });

  @override
  State<_IosTabItemWidget> createState() => _IosTabItemWidgetState();
}

class _IosTabItemWidgetState extends State<_IosTabItemWidget>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 120),
      lowerBound: 0.0,
      upperBound: 1.0,
    );
    _scale = Tween<double>(begin: 1.0, end: 0.84)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeIn));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _handleTap() async {
    await _ctrl.forward();
    widget.onTap();
    await _ctrl.reverse();
  }

  @override
  Widget build(BuildContext context) {
    final selected = widget.selected;
    // Active: gold amber matching app brand; inactive: Apple system gray
    final Color activeColor = const Color(0xFFFFD60A);    // Apple amber/gold
    final Color inactiveColor = const Color(0xFF8E8E93);  // Apple System Gray 1

    return GestureDetector(
      onTap: _handleTap,
      behavior: HitTestBehavior.opaque, // Entire vertical space from top to bottom is tappable
      child: Container(
        color: Colors.transparent, // Ensures hit testing across full cell
        padding: EdgeInsets.only(bottom: widget.safeBottom * 0.55, top: 4.0),
        child: Center(
          child: ScaleTransition(
            scale: _scale,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              mainAxisSize: MainAxisSize.min,
              children: [
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 180),
                  transitionBuilder: (child, anim) => ScaleTransition(
                    scale: Tween<double>(begin: 0.75, end: 1.0).animate(
                      CurvedAnimation(parent: anim, curve: Curves.easeOutBack),
                    ),
                    child: FadeTransition(opacity: anim, child: child),
                  ),
                  child: Icon(
                    selected ? widget.tab.filledIcon : widget.tab.outlineIcon,
                    key: ValueKey(selected),
                    size: 25.0,
                    color: selected ? activeColor : inactiveColor,
                  ),
                ),
                const SizedBox(height: 3),
                AnimatedDefaultTextStyle(
                  duration: const Duration(milliseconds: 180),
                  style: TextStyle(
                    fontSize: 10.0,
                    height: 1.0,
                    letterSpacing: -0.2,
                    fontWeight: selected ? FontWeight.w600 : FontWeight.w400,
                    color: selected ? activeColor : inactiveColor,
                  ),
                  child: Text(widget.tab.label),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
