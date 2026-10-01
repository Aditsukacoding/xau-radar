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

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  // Base URL configuration:
  // On Web: Auto-detects host (e.g. 192.168.1.53 when opened from phone, or 127.0.0.1 on PC)
  // On Android Emulator: 10.0.2.2
  // On Native App: defaults to local network IP or 127.0.0.1
  static String get _defaultBaseUrl {
    if (kIsWeb) {
      final host = (Uri.base.host.isNotEmpty && Uri.base.host != 'localhost')
          ? Uri.base.host
          : '127.0.0.1';
      return 'http://$host:8000/api/v1';
    }
    return defaultTargetPlatform == TargetPlatform.android
        ? 'http://10.0.2.2:8000/api/v1'
        : 'http://127.0.0.1:8000/api/v1';
  }

  static String baseUrl = _defaultBaseUrl;

  static void updateBaseUrl(String newUrl) {
    baseUrl = newUrl;
  }

  // 1. Dashboard Summary
  Future<DashboardSummaryModel> getDashboardSummary({String symbol = 'XAUUSD'}) async {
    final response = await http.get(Uri.parse('$baseUrl/dashboard/summary/$symbol'));
    if (response.statusCode == 200) {
      return DashboardSummaryModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memuat ringkasan dashboard: ${response.statusCode}');
    }
  }

  // 2. Economic Calendar
  Future<List<EconomicEventModel>> getEconomicCalendar({String? impact, int days = 7}) async {
    String url = '$baseUrl/fundamental/calendar?days=$days';
    if (impact != null && impact.isNotEmpty) {
      url += '&impact=$impact';
    }
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => EconomicEventModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal memuat kalender ekonomi: ${response.statusCode}');
    }
  }

  // 3. Upcoming High Impact Radar
  Future<List<EconomicEventModel>> getUpcomingHighImpact({int hours = 48}) async {
    final response = await http.get(Uri.parse('$baseUrl/fundamental/upcoming-high-impact?hours_ahead=$hours'));
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
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => NewsArticleModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal memuat berita geopolitik: ${response.statusCode}');
    }
  }

  // 5. Candlestick Chart Data
  Future<List<PriceCandleModel>> getCandles(String symbol, {String timeframe = '1h', int limit = 80}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/technical/candles/$symbol?timeframe=$timeframe&limit=$limit'),
    );
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => PriceCandleModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal memuat data candle: ${response.statusCode}');
    }
  }

  // 6. Technical Indicators
  Future<TechnicalIndicatorsModel> getTechnicalIndicators(String symbol, {String timeframe = '1h'}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/technical/indicators/$symbol?timeframe=$timeframe'),
    );
    if (response.statusCode == 200) {
      return TechnicalIndicatorsModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memuat indikator teknikal: ${response.statusCode}');
    }
  }

  // 7. Latest AI Analysis Report
  Future<AnalysisReportModel> getLatestAnalysis({String symbol = 'XAUUSD'}) async {
    final response = await http.get(Uri.parse('$baseUrl/analysis/latest/$symbol'));
    if (response.statusCode == 200) {
      return AnalysisReportModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memuat laporan analisis: ${response.statusCode}');
    }
  }

  // 8. Live Price Tick
  Future<Map<String, dynamic>> getLivePriceTick({String symbol = 'XAUUSD'}) async {
    final response = await http.get(Uri.parse('$baseUrl/technical/live-price/$symbol'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Gagal memuat tick harga live: ${response.statusCode}');
    }
  }


  // 8. Trigger Fresh AI Analysis Synthesis
  Future<AnalysisReportModel> triggerFreshAnalysis({String symbol = 'XAUUSD'}) async {
    final response = await http.post(Uri.parse('$baseUrl/analysis/generate/$symbol'));
    if (response.statusCode == 200) {
      return AnalysisReportModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memicu analisis baru: ${response.statusCode}');
    }
  }

  // 9. Trigger Full Real-time Live Market Sync
  Future<DashboardSummaryModel> triggerFullLiveSync({String symbol = 'XAUUSD'}) async {
    final response = await http.post(Uri.parse('$baseUrl/dashboard/sync/$symbol'));
    if (response.statusCode == 200) {
      return DashboardSummaryModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal sinkronisasi data live: ${response.statusCode}');
    }
  }

  // 10. Trigger Instant Breaking News Sync
  Future<List<NewsArticleModel>> syncNews({String symbol = 'XAUUSD'}) async {
    final response = await http.post(Uri.parse('$baseUrl/geopolitical/news/sync?symbol=$symbol'));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => NewsArticleModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal sinkronisasi berita live: ${response.statusCode}');
    }
  }

  // 11. Trigger Instant Economic Calendar Sync
  Future<List<EconomicEventModel>> syncCalendar() async {
    final response = await http.post(Uri.parse('$baseUrl/fundamental/calendar/sync'));
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((e) => EconomicEventModel.fromJson(e)).toList();
    } else {
      throw Exception('Gagal sinkronisasi kalender: ${response.statusCode}');
    }
  }

  // 12. News Intelligence & Scenario Planning (9-Step Institutional Model)
  Future<NewsIntelligenceModel> getNewsIntelligence({String symbol = 'XAUUSD', String? eventTitle}) async {
    String url = '$baseUrl/news-intelligence/latest/$symbol';
    if (eventTitle != null && eventTitle.isNotEmpty) {
      url += '?event_title=${Uri.encodeComponent(eventTitle)}';
    }
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      return NewsIntelligenceModel.fromJson(json.decode(response.body));
    } else {
      throw Exception('Gagal memuat analisis skenario news: ${response.statusCode}');
    }
  }
}
