import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../../data/models/dashboard_summary_model.dart';
import '../../data/models/economic_event_model.dart';
import '../../data/models/news_article_model.dart';
import '../../data/models/price_candle_model.dart';
import '../../data/models/technical_indicators_model.dart';
import '../../data/models/analysis_report_model.dart';
import '../../data/models/news_intelligence_model.dart';
import '../../data/models/signal_history_model.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  // Base URL configuration:
  // Production: Set via --dart-define=BACKEND_URL=https://api.yoursite.com/api/v1 at build time
  // On Web (local): Auto-detects host (e.g. 192.168.1.53 when opened from iPhone on LAN)
  // On Android Emulator: 10.0.2.2
  // On Native App: defaults to 127.0.0.1
  static const String _buildTimeBackendUrl = String.fromEnvironment('BACKEND_URL', defaultValue: '');

  static String get _defaultBaseUrl {
    // 1. Build-time constant wins (used for production deployment)
    if (_buildTimeBackendUrl.isNotEmpty) return _buildTimeBackendUrl;
    // 2. Web: if on production domain (e.g. ditzy.biz.id or remote hosting), use Vercel backend
    if (kIsWeb) {
      final host = Uri.base.host;
      if (host.isNotEmpty && !host.contains('localhost') && host != '127.0.0.1' && !host.startsWith('192.168.')) {
        return 'https://xau-radar-omega.vercel.app/api/v1';
      }
      final devHost = (host.isNotEmpty && host != 'localhost') ? host : '127.0.0.1';
      return 'http://$devHost:8000/api/v1';
    }
    return defaultTargetPlatform == TargetPlatform.android
        ? 'http://10.0.2.2:8000/api/v1'
        : 'http://127.0.0.1:8000/api/v1';
  }

  static String baseUrl = _defaultBaseUrl;

  static void updateBaseUrl(String newUrl) {
    baseUrl = newUrl;
  }

  static const Duration _defaultTimeout = Duration(seconds: 22);

  Future<http.Response> _getWithRetry(
    String url, {
    Duration timeout = _defaultTimeout,
    int maxAttempts = 2,
  }) async {
    Object? lastErr;
    for (int attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        final response = await http.get(Uri.parse(url)).timeout(timeout);
        if (response.statusCode < 500) {
          return response;
        }
        lastErr = Exception('Server sedang sibuk (${response.statusCode})');
      } catch (e) {
        lastErr = e;
      }
      if (attempt < maxAttempts - 1) {
        await Future.delayed(const Duration(milliseconds: 700));
      }
    }
    if (lastErr is TimeoutException) {
      throw Exception('Koneksi ke server melebihi batas waktu. Silakan coba lagi.');
    }
    throw lastErr ?? Exception('Gagal terhubung ke server.');
  }

  // 1. Dashboard Summary (with automatic retry for Vercel + Neon serverless cold starts)
  Future<DashboardSummaryModel> getDashboardSummary({String symbol = 'XAUUSD'}) async {
    final response = await _getWithRetry('$baseUrl/dashboard/summary/$symbol');
    if (response.statusCode == 200) {
      return DashboardSummaryModel.fromJson(json.decode(response.body));
    }
    throw Exception('Gagal memuat ringkasan dashboard: ${response.statusCode}');
  }

  // 2. Economic Calendar
  Future<List<EconomicEventModel>> getEconomicCalendar({String? impact, int days = 7}) async {
    String url = '$baseUrl/fundamental/calendar?days=$days';
    if (impact != null && impact.isNotEmpty) {
      url += '&impact=$impact';
    }
    final response = await _getWithRetry(url);
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => EconomicEventModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal memuat kalender ekonomi: ${response.statusCode}');
    }
  }

  // 3. Upcoming High Impact Radar
  Future<List<EconomicEventModel>> getUpcomingHighImpact({int hours = 48}) async {
    final response = await _getWithRetry('$baseUrl/fundamental/upcoming-high-impact?hours_ahead=$hours');
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => EconomicEventModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal memuat radar high-impact: ${response.statusCode}');
    }
  }

  // 4. Geopolitical News
  Future<List<NewsArticleModel>> getNews({String symbol = 'XAUUSD', String? sentiment, int limit = 20}) async {
    String url = '$baseUrl/geopolitical/news?symbol=$symbol&limit=$limit';
    if (sentiment != null && sentiment.isNotEmpty) {
      url += '&sentiment=$sentiment';
    }
    final response = await _getWithRetry(url);
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => NewsArticleModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal memuat berita geopolitik: ${response.statusCode}');
    }
  }

  // 5. Candlestick Chart Data
  Future<List<PriceCandleModel>> getCandles(String symbol, {String timeframe = '1h', int limit = 80}) async {
    final response = await _getWithRetry('$baseUrl/technical/candles/$symbol?timeframe=$timeframe&limit=$limit');
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => PriceCandleModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal memuat data candle: ${response.statusCode}');
    }
  }

  // 6. Technical Indicators
  Future<TechnicalIndicatorsModel> getTechnicalIndicators(String symbol, {String timeframe = '1h'}) async {
    final response = await _getWithRetry('$baseUrl/technical/indicators/$symbol?timeframe=$timeframe');
    if (response.statusCode == 200) {
      return TechnicalIndicatorsModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memuat indikator teknikal: ${response.statusCode}');
    }
  }

  // 7. Latest AI Analysis Report
  Future<AnalysisReportModel> getLatestAnalysis({String symbol = 'XAUUSD'}) async {
    final response = await _getWithRetry('$baseUrl/analysis/latest/$symbol');
    if (response.statusCode == 200) {
      return AnalysisReportModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memuat laporan analisis: ${response.statusCode}');
    }
  }

  // 8. Live Price Tick (Fast 4s timeout)
  Future<Map<String, dynamic>> getLivePriceTick({String symbol = 'XAUUSD'}) async {
    final response = await http
        .get(Uri.parse('$baseUrl/technical/live-price/$symbol'))
        .timeout(const Duration(seconds: 10));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Gagal memuat tick harga live: ${response.statusCode}');
    }
  }

  // 9. Trigger Fresh AI Analysis Synthesis (Allow 25s for AI)
  Future<AnalysisReportModel> triggerFreshAnalysis({String symbol = 'XAUUSD'}) async {
    final response = await http
        .post(Uri.parse('$baseUrl/analysis/generate/$symbol'))
        .timeout(const Duration(seconds: 25));
    if (response.statusCode == 200) {
      return AnalysisReportModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memicu analisis baru: ${response.statusCode}');
    }
  }

  // 10. Trigger Full Real-time Live Market Sync
  Future<DashboardSummaryModel> triggerFullLiveSync({String symbol = 'XAUUSD'}) async {
    final response = await http
        .post(Uri.parse('$baseUrl/dashboard/sync/$symbol'))
        .timeout(const Duration(seconds: 35));
    if (response.statusCode == 200) {
      return DashboardSummaryModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal sinkronisasi data live: ${response.statusCode}');
    }
  }

  // 11. Trigger Instant Breaking News Sync
  Future<List<NewsArticleModel>> syncNews({String symbol = 'XAUUSD'}) async {
    final response = await http
        .post(Uri.parse('$baseUrl/geopolitical/news/sync?symbol=$symbol'))
        .timeout(_defaultTimeout);
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => NewsArticleModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal sinkronisasi berita live: ${response.statusCode}');
    }
  }

  // 12. Trigger Instant Economic Calendar Sync
  Future<List<EconomicEventModel>> syncCalendar() async {
    final response = await http
        .post(Uri.parse('$baseUrl/fundamental/calendar/sync'))
        .timeout(_defaultTimeout);
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => EconomicEventModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal sinkronisasi kalender: ${response.statusCode}');
    }
  }

  // 13. News Intelligence & Scenario Planning (9-Step Institutional Model)
  Future<NewsIntelligenceModel> getNewsIntelligence({
    String symbol = 'XAUUSD',
    String? eventTitle,
    String? currency,
    String? scheduledAt,
    String? forecast,
    String? previous,
    String? actual,
  }) async {
    final params = <String>[];
    if (eventTitle != null && eventTitle.isNotEmpty) {
      params.add('event_title=${Uri.encodeComponent(eventTitle)}');
    }
    if (currency != null && currency.isNotEmpty) {
      params.add('currency=${Uri.encodeComponent(currency)}');
    }
    if (scheduledAt != null && scheduledAt.isNotEmpty) {
      params.add('scheduled_at=${Uri.encodeComponent(scheduledAt)}');
    }
    if (forecast != null && forecast.isNotEmpty) {
      params.add('forecast=${Uri.encodeComponent(forecast)}');
    }
    if (previous != null && previous.isNotEmpty) {
      params.add('previous=${Uri.encodeComponent(previous)}');
    }
    if (actual != null && actual.isNotEmpty) {
      params.add('actual=${Uri.encodeComponent(actual)}');
    }
    final query = params.isNotEmpty ? '?${params.join('&')}' : '';
    final url = '$baseUrl/news-intelligence/latest/$symbol$query';
    final response = await _getWithRetry(url);
    if (response.statusCode == 200) {
      return NewsIntelligenceModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memuat analisis skenario news: ${response.statusCode}');
    }
  }

  // 14. Signal History & Real SL / TP Outcome Tracker
  Future<SignalHistoryResponseModel> getSignalHistory({
    String symbol = 'XAUUSD',
    String action = 'ALL',
    String outcome = 'ALL',
    int limit = 40,
  }) async {
    final url = '$baseUrl/signals/history/$symbol?action=$action&outcome=$outcome&limit=$limit';
    final response = await _getWithRetry(url, timeout: const Duration(seconds: 26));
    if (response.statusCode == 200) {
      return SignalHistoryResponseModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memuat riwayat entry: ${response.statusCode}');
    }
  }

  // 15. Refresh Signal History Verification
  Future<SignalHistoryResponseModel> refreshSignalHistory({String symbol = 'XAUUSD'}) async {
    final response = await http
        .post(Uri.parse('$baseUrl/signals/refresh/$symbol'))
        .timeout(const Duration(seconds: 30));
    if (response.statusCode == 200) {
      return SignalHistoryResponseModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memperbarui riwayat entry: ${response.statusCode}');
    }
  }

  // 16. Reset Signal History (Start Clean From 0)
  Future<SignalHistoryResponseModel> resetSignalHistory({String symbol = 'XAUUSD'}) async {
    final response = await http
        .post(Uri.parse('$baseUrl/signals/reset/$symbol'))
        .timeout(const Duration(seconds: 30));
    if (response.statusCode == 200) {
      return SignalHistoryResponseModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal mengosongkan riwayat entry: ${response.statusCode}');
    }
  }
}
