import 'dart:async';
import 'package:flutter/cupertino.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/network/api_service.dart';
import '../../data/models/economic_event_model.dart';
import '../widgets/event_card.dart';
import '../widgets/ios_segmented_control.dart';
import '../widgets/news_scenario_sheet.dart';
import '../widgets/modern_toast.dart';

class FundamentalScreen extends StatefulWidget {
  const FundamentalScreen({super.key});

  @override
  State<FundamentalScreen> createState() => _FundamentalScreenState();
}

class _FundamentalScreenState extends State<FundamentalScreen> {
  final ApiService _api = ApiService();
  List<EconomicEventModel> _events = [];
  bool _isLoading = true;
  bool _isSyncing = false;
  String? _error;
  String _selectedFilter = 'ALL'; // ALL, HIGH, MEDIUM
  bool _isLoadingScenario = false;
  Timer? _autoPollTimer;

  @override
  void initState() {
    super.initState();
    _loadEvents();
    // Lightweight 90-second background poll to capture newly released actuals
    _autoPollTimer = Timer.periodic(const Duration(seconds: 90), (_) {
      _loadEvents(silent: true);
    });
  }

  @override
  void dispose() {
    _autoPollTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadEvents({bool silent = false, bool triggerSync = false}) async {
    if (!mounted) return;
    if (!silent && _events.isEmpty) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    } else {
      setState(() {
        _isSyncing = true;
      });
    }

    try {
      if (triggerSync) {
        await _api.syncCalendar();
      }
      final impactQuery = _selectedFilter == 'ALL' ? null : _selectedFilter;
      final data = await _api.getEconomicCalendar(impact: impactQuery, days: 14);
      if (mounted) {
        setState(() {
          _events = data;
          _isLoading = false;
          _isSyncing = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSyncing = false;
          if (_events.isEmpty) {
            _error = e.toString();
            _isLoading = false;
          }
        });
      }
    }
  }

  Future<void> _openNewsScenario({String? eventTitle, String? currency}) async {
    setState(() => _isLoadingScenario = true);
    try {
      final scenario = await _api.getNewsIntelligence(
        symbol: 'XAUUSD',
        eventTitle: eventTitle,
        currency: currency,
      );
      if (mounted) {
        NewsScenarioSheet.show(context, scenario);
      }
    } catch (e) {
      if (mounted) {
        ModernToast.showError(context, 'Gagal memuat skenario: $e');
      }
    } finally {
      if (mounted) {
        setState(() => _isLoadingScenario = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    const double topInset = 16.0;
    final bottomInset = mediaQuery.padding.bottom + 64 + 20;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Column(
        children: [
          const SizedBox(height: topInset),

          // Clean Airy Header & Sync Bar
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.center,
                  children: [
                    const Expanded(
                      child: Text(
                        'Kalender Ekonomi',
                        style: TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 19,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -0.3,
                        ),
                      ),
                    ),
                    CupertinoButton(
                      padding: EdgeInsets.zero,
                      minimumSize: Size.zero,
                      onPressed: _isSyncing ? null : () => _loadEvents(silent: false, triggerSync: true),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 6),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceInset,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.border, width: 0.8),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            _isSyncing
                                ? const CupertinoActivityIndicator(radius: 6, color: AppColors.gold)
                                : const Icon(LucideIcons.refreshCw, size: 12, color: AppColors.gold),
                            const SizedBox(width: 6),
                            const Text(
                              'Sync',
                              style: TextStyle(
                                color: AppColors.gold,
                                fontSize: 11.5,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                // Unified Single-Line Live Status Metadata (Clean, zero stacked badges)
                Row(
                  children: [
                    Container(
                      width: 6.5,
                      height: 6.5,
                      decoration: BoxDecoration(
                        color: _isSyncing ? AppColors.cyan : AppColors.bullish,
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: (_isSyncing ? AppColors.cyan : AppColors.bullish).withValues(alpha: 0.55),
                            blurRadius: 5,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      _isSyncing ? 'Sinkronisasi...' : 'Live 25d',
                      style: TextStyle(
                        color: _isSyncing ? AppColors.cyan : AppColors.bullish,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const Text(
                      '  •  ',
                      style: TextStyle(color: AppColors.textMuted, fontSize: 11),
                    ),
                    const Text(
                      'WIB',
                      style: TextStyle(
                        color: AppColors.gold,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const Text(
                      '  •  ',
                      style: TextStyle(color: AppColors.textMuted, fontSize: 11),
                    ),
                    const Flexible(
                      child: Text(
                        '14 Hari • FF & TradingView',
                        style: TextStyle(
                          color: AppColors.textTertiary,
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          const SizedBox(height: 14),

          // Full-Width Symmetric Apple Segmented Filter Bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: IosSegmentedControl<String>(
              fullWidth: true,
              items: const {
                'ALL': 'Semua',
                'HIGH': 'High Impact',
                'MEDIUM': 'Medium',
              },
              selectedValue: _selectedFilter,
              onValueChanged: (val) {
                setState(() {
                  _selectedFilter = val;
                });
                _loadEvents();
              },
            ),
          ),

          const SizedBox(height: 12),

          // Clean Pre-News Scenario CTA Card
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: _isLoadingScenario ? null : () => _openNewsScenario(),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(15),
                  border: Border.all(color: AppColors.gold.withValues(alpha: 0.30), width: 0.9),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8.5),
                      decoration: BoxDecoration(
                        color: AppColors.gold.withValues(alpha: 0.14),
                        borderRadius: BorderRadius.circular(11),
                      ),
                      child: _isLoadingScenario
                          ? const CupertinoActivityIndicator(radius: 7, color: AppColors.gold)
                          : const Icon(LucideIcons.sparkles, color: AppColors.gold, size: 16),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Flexible(
                                child: Text(
                                  'Skenario Pre-News',
                                  style: TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 13,
                                    fontWeight: FontWeight.w700,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                              const SizedBox(width: 7),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                                decoration: BoxDecoration(
                                  color: AppColors.gold.withValues(alpha: 0.14),
                                  borderRadius: BorderRadius.circular(5),
                                ),
                                child: const Text(
                                  '9 Langkah',
                                  style: TextStyle(
                                    color: AppColors.gold,
                                    fontSize: 9.5,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 3),
                          const Text(
                            'Matriks skenario Kuat / Sesuai / Lemah ke XAU',
                            style: TextStyle(
                              color: AppColors.textTertiary,
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Icon(LucideIcons.chevronRight, color: AppColors.gold, size: 15),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 12),
          const Divider(height: 1, color: AppColors.borderSubtle),

          // Events List
          Expanded(
            child: _isLoading
                ? const Center(child: CupertinoActivityIndicator(radius: 14, color: AppColors.primary))
                : _error != null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(LucideIcons.circleAlert, color: AppColors.bearish, size: 36),
                            const SizedBox(height: 8),
                            Text('Gagal memuat: $_error', style: const TextStyle(color: AppColors.textMuted)),
                            const SizedBox(height: 12),
                            CupertinoButton.filled(onPressed: _loadEvents, child: const Text('Coba Lagi')),
                          ],
                        ),
                      )
                    : _events.isEmpty
                        ? const Center(
                            child: Text('Tidak ada event terjadwal untuk filter ini', style: TextStyle(color: AppColors.textMuted)),
                          )
                        : RefreshIndicator(
                            onRefresh: () => _loadEvents(silent: false, triggerSync: true),
                            color: AppColors.primary,
                            backgroundColor: const Color(0xFF1C1C1E),
                            child: ListView.builder(
                              physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
                              padding: EdgeInsets.only(top: 8, bottom: bottomInset),
                              itemCount: _events.length,
                              itemBuilder: (context, index) {
                                final ev = _events[index];
                                final isHigh = ev.impactLevel.toUpperCase() == 'HIGH';
                                return EventCard(
                                  event: ev,
                                  onTap: isHigh
                                      ? () => _openNewsScenario(
                                            eventTitle: ev.eventTitle,
                                            currency: ev.currency,
                                          )
                                      : null,
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}
