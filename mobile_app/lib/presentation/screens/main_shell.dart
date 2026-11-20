import 'dart:async';
import 'dart:math';
import 'dart:ui';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import '../../core/constants/app_colors.dart';
import '../../core/theme/app_theme.dart';
import '../../core/network/api_service.dart';
import '../../core/utils/wib_date_time.dart';
import 'dashboard_screen.dart';
import 'fundamental_screen.dart';
import 'geopolitical_screen.dart';
import 'technical_screen.dart';
import 'history_screen.dart';
import '../widgets/modern_toast.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;
  DateTime _now = DateTime.now();
  Timer? _clockTimer;

  @override
  void initState() {
    super.initState();
    _clockTimer = Timer.periodic(const Duration(seconds: 15), (_) {
      if (mounted) {
        setState(() {
          _now = DateTime.now();
        });
      }
    });
  }

  @override
  void dispose() {
    _clockTimer?.cancel();
    super.dispose();
  }

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
      barrierColor: Colors.black.withValues(alpha: 0.76),
      transitionDuration: const Duration(milliseconds: 240),
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
                    filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
                    child: Container(
                      padding: const EdgeInsets.all(22),
                      decoration: BoxDecoration(
                        color: const Color(0xF510131B),
                        borderRadius: BorderRadius.circular(24),
                        border: Border.all(
                          color: AppColors.gold.withValues(alpha: 0.30),
                          width: 1.0,
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.75),
                            blurRadius: 36,
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
                                padding: const EdgeInsets.all(9),
                                decoration: BoxDecoration(
                                  color: AppColors.gold.withValues(alpha: 0.14),
                                  borderRadius: BorderRadius.circular(11),
                                  border: Border.all(color: AppColors.gold.withValues(alpha: 0.30)),
                                ),
                                child: const Icon(LucideIcons.slidersHorizontal, color: AppColors.gold, size: 18),
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
                                        fontSize: 15.5,
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                    SizedBox(height: 2),
                                    Text(
                                      'Institutional Analytics Engine',
                                      style: TextStyle(color: AppColors.textMuted, fontSize: 11),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 20),
                          const Text(
                            'Base URL Endpoint',
                            style: TextStyle(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 8),
                          CupertinoTextField(
                            controller: controller,
                            placeholder: 'https://xau-radar-omega.vercel.app/api/v1',
                            style: AppTypography.mono(color: AppColors.textPrimary, fontSize: 12.5),
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
                            decoration: BoxDecoration(
                              color: AppColors.surfaceInset,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppColors.border),
                            ),
                          ),
                          const SizedBox(height: 22),
                          Row(
                            children: [
                              Expanded(
                                child: CupertinoButton(
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                  color: AppColors.surfaceElevated,
                                  borderRadius: BorderRadius.circular(12),
                                  onPressed: () => Navigator.pop(context),
                                  child: const Text('Batal', style: TextStyle(color: AppColors.textMuted, fontSize: 13, fontWeight: FontWeight.w700)),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: CupertinoButton(
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                  color: AppColors.gold,
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
                                  child: const Text('Simpan', style: TextStyle(color: Color(0xFF08090C), fontSize: 13, fontWeight: FontWeight.w800)),
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
        final curve = CurvedAnimation(parent: anim1, curve: Curves.easeOutCubic);
        return ScaleTransition(
          scale: Tween<double>(begin: 0.94, end: 1.0).animate(curve),
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
      const HistoryScreen(),
    ];

    final wibTimeShort = _now.formatWibTime(withSeconds: false).replaceAll(' WIB', '');

    return Scaffold(
      backgroundColor: AppColors.background,
      extendBody: true,
      extendBodyBehindAppBar: false,
      appBar: AppBar(
        backgroundColor: const Color(0xF508090C),
        elevation: 0,
        scrolledUnderElevation: 0,
        toolbarHeight: 58,
        titleSpacing: 16,
        centerTitle: false,
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(0.8),
          child: Container(height: 0.8, color: AppColors.border),
        ),
        title: GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: _showServerSettingsDialog,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Radiant Gold Bullion Brand Mark
              Container(
                width: 30,
                height: 30,
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [AppColors.gold, AppColors.goldDeep],
                  ),
                  borderRadius: BorderRadius.circular(9),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.gold.withValues(alpha: 0.22),
                      blurRadius: 10,
                      offset: const Offset(0, 2),
                    ),
                  ],
                ),
                child: const Icon(
                  LucideIcons.radar,
                  color: Color(0xFF08090C),
                  size: 17,
                ),
              ),
              const SizedBox(width: 10),
              Flexible(
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Flexible(
                      child: Text(
                        'XAU/USD RADAR',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.5,
                          color: AppColors.textPrimary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    const SizedBox(width: 7),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2.5),
                      decoration: BoxDecoration(
                        color: AppColors.gold.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: AppColors.gold.withValues(alpha: 0.30), width: 0.7),
                      ),
                      child: const Text(
                        '3-PILLAR',
                        style: TextStyle(
                          fontSize: 8.5,
                          fontWeight: FontWeight.w800,
                          color: AppColors.gold,
                          letterSpacing: 0.6,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          // Clean WIB • LIVE Status Pill
          Center(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.border, width: 0.8),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 6,
                    height: 6,
                    decoration: BoxDecoration(
                      color: AppColors.bullish,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.bullish.withValues(alpha: 0.7),
                          blurRadius: 5,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 5),
                  Text(
                    '$wibTimeShort WIB',
                    style: AppTypography.mono(
                      color: AppColors.textSecondary,
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          // Minimalist Settings / Profile Action Button (44x44pt Apple HIG touch target)
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Center(
              child: IconButton(
                onPressed: _showServerSettingsDialog,
                iconSize: 18,
                tooltip: 'Pengaturan Server',
                style: IconButton.styleFrom(
                  backgroundColor: AppColors.surface,
                  minimumSize: const Size(44, 44),
                  fixedSize: const Size(38, 38),
                  padding: EdgeInsets.zero,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(11),
                    side: const BorderSide(color: AppColors.border, width: 0.85),
                  ),
                ),
                icon: const Icon(
                  LucideIcons.slidersHorizontal,
                  color: AppColors.textSecondary,
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
      bottomNavigationBar: _IosTabBar(
        currentIndex: _currentIndex,
        onTap: _onTabSelected,
      ),
    );
  }
}

// ─── Native iOS 18 Obsidian & Gold Tab Bar ───────────────────────────────────
class _IosTabBar extends StatelessWidget {
  final int currentIndex;
  final ValueChanged<int> onTap;

  const _IosTabBar({required this.currentIndex, required this.onTap});

  static const _tabs = [
    _TabItem(icon: LucideIcons.layoutDashboard, label: 'Pasar'),
    _TabItem(icon: LucideIcons.calendarClock, label: 'Kalender'),
    _TabItem(icon: LucideIcons.newspaper, label: 'Berita'),
    _TabItem(icon: LucideIcons.chartCandlestick, label: 'Teknikal'),
    _TabItem(icon: LucideIcons.history, label: 'Riwayat'),
  ];

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final rawBottom = mediaQuery.padding.bottom;
    final isMobile = mediaQuery.size.width < 768;
    final double safeBottom = isMobile ? max(rawBottom, 28.0) : (rawBottom > 0 ? rawBottom : 10.0);

    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 28, sigmaY: 28),
        child: Container(
          decoration: const BoxDecoration(
            color: Color(0xE008090C),
            border: Border(
              top: BorderSide(
                color: AppColors.border,
                width: 0.8,
              ),
            ),
          ),
          height: 54.0 + safeBottom,
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
  final IconData icon;
  final String label;
  const _TabItem({required this.icon, required this.label});
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

class _IosTabItemWidgetState extends State<_IosTabItemWidget> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 110),
      lowerBound: 0.0,
      upperBound: 1.0,
    );
    _scale = Tween<double>(begin: 1.0, end: 0.86).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
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
    const Color activeColor = AppColors.gold;
    const Color inactiveColor = AppColors.textTertiary;

    return GestureDetector(
      onTap: _handleTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        color: Colors.transparent,
        padding: EdgeInsets.only(bottom: widget.safeBottom * 0.55),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.start,
          children: [
            // Precision Top Active Gold Indicator Line
            AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              curve: Curves.easeOutCubic,
              width: selected ? 24 : 0,
              height: 2.2,
              decoration: BoxDecoration(
                color: selected ? activeColor : Colors.transparent,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            Expanded(
              child: Center(
                child: ScaleTransition(
                  scale: _scale,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      AnimatedContainer(
                        duration: const Duration(milliseconds: 200),
                        curve: Curves.easeOutCubic,
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3.5),
                        decoration: BoxDecoration(
                          color: selected ? activeColor.withValues(alpha: 0.14) : Colors.transparent,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Icon(
                          widget.tab.icon,
                          size: 19.5,
                          color: selected ? activeColor : inactiveColor,
                        ),
                      ),
                      const SizedBox(height: 3),
                      AnimatedDefaultTextStyle(
                        duration: const Duration(milliseconds: 180),
                        style: TextStyle(
                          fontFamily: AppTypography.uiFamily,
                          fontSize: 10.0,
                          height: 1.0,
                          letterSpacing: 0.1,
                          fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
                          color: selected ? activeColor : inactiveColor,
                        ),
                        child: Text(widget.tab.label),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
