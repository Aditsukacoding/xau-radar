import 'dart:async';
import 'package:flutter/cupertino.dart';
import 'package:lucide_icons_flutter/lucide_icons.dart';
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
    // Lightweight 60-second background auto-poll for fresh breaking news
    _autoPollTimer = Timer.periodic(const Duration(seconds: 60), (_) {
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
                        'Berita & Geopolitik',
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
                      onPressed: _isSyncing ? null : () => _loadNews(silent: false, triggerSync: true),
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
                      _isSyncing ? 'Menyinkronkan berita...' : 'Live 15d',
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
                    Flexible(
                      child: Builder(
                        builder: (_) {
                          final uniqueSrcCount = _articles
                              .map((a) => a.source.trim().toLowerCase())
                              .where((s) => s.isNotEmpty)
                              .toSet()
                              .length;
                          final label = uniqueSrcCount > 0
                              ? '$uniqueSrcCount Sumber Global • XAU/USD'
                              : '15+ Sumber Global • XAU/USD';
                          return Text(
                            label,
                            style: const TextStyle(
                              color: AppColors.textTertiary,
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          );
                        },
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

          const SizedBox(height: 12),
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
                            const Icon(LucideIcons.circleAlert, color: AppColors.bearish, size: 36),
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
                              padding: EdgeInsets.only(top: 8, bottom: bottomInset),
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
