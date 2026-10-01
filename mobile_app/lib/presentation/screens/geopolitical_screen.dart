import 'dart:async';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/network/api_service.dart';
import '../../data/models/news_article_model.dart';
import '../widgets/news_card.dart';
import '../widgets/ios_segmented_control.dart';

class GeopoliticalScreen extends StatefulWidget {
  const GeopoliticalScreen({super.key});

  @override
  State<GeopoliticalScreen> createState() => _GeopoliticalScreenState();
}

class _GeopoliticalScreenState extends State<GeopoliticalScreen> {
  final ApiService _api = ApiService();
  List<NewsArticleModel> _articles = [];
  bool _isLoading = true;
  bool _isSyncing = false;
  String? _error;
  String _selectedSentiment = 'ALL'; // ALL, POSITIVE, NEGATIVE, NEUTRAL
  Timer? _autoPollTimer;

  @override
  void initState() {
    super.initState();
    _loadNews();
    // Ultra-responsive 15-second continuous background auto-poll
    // Immediately ingests and displays any new breaking news
    _autoPollTimer = Timer.periodic(const Duration(seconds: 15), (_) {
      _loadNews(silent: true);
    });
  }

  @override
  void dispose() {
    _autoPollTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadNews({bool silent = false, bool triggerSync = false}) async {
    if (!mounted) return;
    if (!silent && _articles.isEmpty) {
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
        await _api.syncNews(symbol: 'XAUUSD');
      }
      final sentimentQuery = _selectedSentiment == 'ALL' ? null : _selectedSentiment;
      final data = await _api.getNews(symbol: 'XAUUSD', sentiment: sentimentQuery);
      if (mounted) {
        setState(() {
          _articles = data;
          _isLoading = false;
          _isSyncing = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSyncing = false;
          if (_articles.isEmpty) {
            _error = e.toString();
            _isLoading = false;
          }
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: Column(
        children: [
          const SizedBox(height: 64), // Inset for floating glass appbar

          // Header Status & Sync Bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Text(
                          'BERITA & GEOPOLITIK',
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
                          _isSyncing ? 'Menyinkronkan berita...' : 'AUTO-SYNC LIVE (15s)',
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
                CupertinoButton(
                  padding: EdgeInsets.zero,
                  onPressed: _isSyncing ? null : () => _loadNews(silent: false, triggerSync: true),
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
                      'POSITIVE': 'Bullish',
                      'NEGATIVE': 'Bearish',
                      'NEUTRAL': 'Netral',
                    },
                    selectedValue: _selectedSentiment,
                    onValueChanged: (val) {
                      setState(() {
                        _selectedSentiment = val;
                      });
                      _loadNews();
                    },
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 4),
          const Divider(height: 1, color: AppColors.borderSubtle),

          // News Articles List
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
                            CupertinoButton.filled(onPressed: _loadNews, child: const Text('Coba Lagi')),
                          ],
                        ),
                      )
                    : _articles.isEmpty
                        ? const Center(
                            child: Text('Tidak ada artikel berita ditemukan', style: TextStyle(color: AppColors.textMuted)),
                          )
                        : RefreshIndicator(
                            onRefresh: () => _loadNews(silent: false, triggerSync: true),
                            color: AppColors.primary,
                            backgroundColor: const Color(0xFF1C1C1E),
                            child: ListView.builder(
                              physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
                              padding: const EdgeInsets.only(top: 8, bottom: 90),
                              itemCount: _articles.length,
                              itemBuilder: (context, index) {
                                return NewsCard(article: _articles[index]);
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}
