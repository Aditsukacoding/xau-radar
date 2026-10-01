import 'dart:async';
import 'package:flutter/cupertino.dart';
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
    // Continuous 25-second background auto-poll to capture real-time released actuals
    _autoPollTimer = Timer.periodic(const Duration(seconds: 25), (_) {
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

  Future<void> _openNewsScenario({String? eventTitle}) async {
    setState(() => _isLoadingScenario = true);
    try {
      final scenario = await _api.getNewsIntelligence(symbol: 'XAUUSD', eventTitle: eventTitle);
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
    final topInset = mediaQuery.padding.top + kToolbarHeight + 8;
    final bottomInset = mediaQuery.padding.bottom + 64 + 20;

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Column(
        children: [
          SizedBox(height: topInset), // Inset for floating glass appbar

          // Header Status & Sync Bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Text(
                            'KALENDER EKONOMI',
                            style: TextStyle(
                              color: AppColors.textPrimary,
                              fontSize: 13,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.6,
                            ),
                          ),
                          const SizedBox(width: 7),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(6),
                              border: Border.all(color: AppColors.primary.withValues(alpha: 0.35), width: 0.8),
                            ),
                            child: const Text(
                              'WIB (UTC+7)',
                              style: TextStyle(color: AppColors.primary, fontSize: 9, fontWeight: FontWeight.w800),
                            ),
                          ),
                        ],
                      ),
                    const SizedBox(height: 2),
                    // ForexFactory source badge
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1.5),
                          decoration: BoxDecoration(
                            color: const Color(0xFF14201E),
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(color: const Color(0x5500E676)),
                          ),
                          child: const Text(
                            'FF + TradingView Live',
                            style: TextStyle(color: Color(0xFF00E676), fontSize: 9, fontWeight: FontWeight.w700, letterSpacing: 0.3),
                          ),
                        ),
                        const SizedBox(width: 5),
                        const Text(
                          '• 14 hari ke depan',
                          style: TextStyle(color: AppColors.textMuted, fontSize: 9.5),
                        ),
                      ],
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: BoxDecoration(
                            color: _isSyncing ? AppColors.appleBlue : AppColors.bullish,
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: (_isSyncing ? AppColors.appleBlue : AppColors.bullish).withValues(alpha: 0.6),
                                blurRadius: 4,
                                spreadRadius: 1,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 5),
                        Text(
                          _isSyncing ? 'Sinkronisasi rilis...' : 'LIVE ACTUALS (25s)',
                          style: TextStyle(
                            color: _isSyncing ? AppColors.appleBlue : AppColors.bullish,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 0.4,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              CupertinoButton(
                  padding: EdgeInsets.zero,
                  onPressed: _isSyncing ? null : () => _loadEvents(silent: false, triggerSync: true),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1C1C1E),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        _isSyncing
                            ? const CupertinoActivityIndicator(radius: 6, color: AppColors.primary)
                            : const Icon(CupertinoIcons.arrow_2_circlepath, size: 12, color: AppColors.primary),
                        const SizedBox(width: 5),
                        const Text(
                          'Sync',
                          style: TextStyle(color: AppColors.primary, fontSize: 11, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Apple Segmented Filter Bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Row(
              children: [
                Expanded(
                  child: IosSegmentedControl<String>(
                    items: const {
                      'ALL': 'Semua',
                      'HIGH': 'High',
                      'MEDIUM': 'Med',
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
              ],
            ),
          ),

          // Action Banner: Analisis Skenario Pre-News (9 Langkah)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: GestureDetector(
              onTap: _isLoadingScenario ? null : () => _openNewsScenario(),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF2E1C0C), Color(0xFF1F2432)],
                  ),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: AppColors.primary.withValues(alpha: 0.4), width: 0.9),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(7),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: _isLoadingScenario
                          ? const CupertinoActivityIndicator(radius: 7, color: AppColors.primary)
                          : const Icon(CupertinoIcons.sparkles, color: AppColors.primary, size: 16),
                    ),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'ANALISIS SKENARIO PRE-NEWS (9 LANGKAH)',
                            style: TextStyle(
                              color: AppColors.primary,
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.5,
                            ),
                          ),
                          SizedBox(height: 1),
                          Text(
                            'Matriks Skenario Kuat/Sesuai/Lemah, Rezim & Jalur Transmisi',
                            style: TextStyle(color: AppColors.textMuted, fontSize: 10.5),
                          ),
                        ],
                      ),
                    ),
                    const Icon(CupertinoIcons.chevron_right, color: AppColors.primary, size: 14),
                  ],
                ),
              ),
            ),
          ),

          const SizedBox(height: 4),
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
                            const Icon(CupertinoIcons.exclamationmark_circle, color: AppColors.bearish, size: 36),
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
                                  onTap: isHigh ? () => _openNewsScenario(eventTitle: ev.eventTitle) : null,
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
