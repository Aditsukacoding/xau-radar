import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/cupertino.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/wib_date_time.dart';
import '../../core/utils/web_url_helper.dart';
import '../../data/models/news_article_model.dart';
import 'modern_toast.dart';

class NewsDetailSheet extends StatelessWidget {
  final NewsArticleModel article;
  final bool isModalDialog;

  const NewsDetailSheet({
    super.key,
    required this.article,
    this.isModalDialog = false,
  });

  /// Opens the news detail sheet in an ultra-modern modal:
  /// - On Desktop / Web / Tablet: Elegant centered frosted glass dialog with scale animation.
  /// - On Mobile: Modern sliding bottom sheet with smooth drag handle and glass backdrop.
  static void show(BuildContext context, NewsArticleModel article) {
    final isDesktop = MediaQuery.of(context).size.width > 720;

    if (isDesktop) {
      showGeneralDialog(
        context: context,
        barrierDismissible: true,
        barrierLabel: 'NewsDetailModal',
        barrierColor: Colors.black.withValues(alpha: 0.72),
        transitionDuration: const Duration(milliseconds: 280),
        pageBuilder: (context, anim1, anim2) {
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxWidth: 680,
                maxHeight: 760,
              ),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
                child: Material(
                  color: Colors.transparent,
                  child: NewsDetailSheet(article: article, isModalDialog: true),
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
    } else {
      showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        backgroundColor: Colors.transparent,
        builder: (context) => NewsDetailSheet(article: article, isModalDialog: false),
      );
    }
  }

  void _openOriginalUrl(BuildContext context) {
    if (article.url == null || article.url!.isEmpty) {
      _showToast(context, 'Tautan sumber asli tidak tersedia untuk artikel ini.');
      return;
    }
    try {
      if (kIsWeb) {
        openWebUrl(article.url!);
      } else {
        Clipboard.setData(ClipboardData(text: article.url!));
        _showToast(context, 'Tautan disalin: ${article.url}');
      }
    } catch (_) {
      Clipboard.setData(ClipboardData(text: article.url!));
      _showToast(context, 'Tautan artikel berhasil disalin!');
    }
  }

  void _copyLink(BuildContext context) {
    if (article.url != null && article.url!.isNotEmpty) {
      Clipboard.setData(ClipboardData(text: article.url!));
      _showToast(context, 'Tautan artikel berhasil disalin ke papan klip!');
    } else {
      Clipboard.setData(ClipboardData(text: '${article.title} - ${article.source}'));
      _showToast(context, 'Judul berita disalin!');
    }
  }

  void _showToast(BuildContext context, String message) {
    ModernToast.showSuccess(context, message, title: 'Informasi Berita');
  }

  Map<String, String> _generateExplanation() {
    final lower = '${article.title} ${article.summary ?? ''}'.toLowerCase();
    final sentiment = article.sentimentLabel.toUpperCase();

    String category;
    String impactAnalysis;
    String transmissionMechanism;
    String traderGuidance;

    if (lower.contains('war') ||
        lower.contains('conflict') ||
        lower.contains('attack') ||
        lower.contains('strike') ||
        lower.contains('missile') ||
        lower.contains('sanction') ||
        lower.contains('geopolitic') ||
        lower.contains('crisis') ||
        lower.contains('truce') ||
        lower.contains('ceasefire')) {
      category = 'Tensi Geopolitik & Konflik Global';
      if (sentiment == 'POSITIVE' || lower.contains('escalat') || lower.contains('attack') || lower.contains('crisis')) {
        impactAnalysis =
            'Eskalasi konflik atau ketegangan geopolitik internasional memicu lonjakan arus penghindaran risiko (risk-off) global. Investor institusi memindahkan likuiditas dari pasar saham ke instrumen safe-haven utama, yaitu emas spot (XAU/USD).';
        transmissionMechanism =
            'Kekhawatiran gangguan pasokan energi/minyak mentah dan stabilitas moneter mendorong akumulasi cadangan emas oleh perbankan sentral dan sovereign funds sebagai sovereign hedge.';
        traderGuidance =
            'Waspadai lonjakan volatilitas (spike) pada pembukaan sesi pasar. Tensi geopolitik cenderung menciptakan lantai support kuat yang menahan koreksi teknikal.';
      } else {
        impactAnalysis =
            'Perkembangan ke arah negosiasi diplomasi, gencatan senjata, atau de-eskalasi konflik mengurangi premi risiko perang (war risk premium) yang sebelumnya menopang reli emas.';
        transmissionMechanism =
            'Pengurangan tensi memicu kembalinya selera risiko (risk-on) ke pasar saham, sehingga modal likuiditas safe-haven keluar dari emas dan menguji support teknikal.';
        traderGuidance =
            'Perhatikan konfirmasi penutupan candle H1/H4 di bawah support terdekat. Jika eskalasi mereda secara berkelanjutan, tekanan jual korektif dapat berlanjut.';
      }
    } else if (lower.contains('fed') ||
        lower.contains('rate') ||
        lower.contains('inflation') ||
        lower.contains('dollar') ||
        lower.contains('treasury') ||
        lower.contains('yield') ||
        lower.contains('cpi') ||
        lower.contains('powell')) {
      category = 'Kebijakan The Fed & Nilai Dolar AS';
      if (sentiment == 'POSITIVE' || lower.contains('cut') || lower.contains('dovish') || lower.contains('fall') || lower.contains('slide')) {
        impactAnalysis =
            'Ekspektasi pelonggaran moneter The Fed atau pelemahan nilai tukar Dolar AS (DXY) memberikan dorongan bullish signifikan terhadap valuasi emas.';
        transmissionMechanism =
            'Emas adalah aset tanpa yield. Saat imbal hasil US Treasury turun atau Dolar melemah, opportunity cost memegang emas mengecil dan daya beli pemegang mata uang non-USD meningkat drastis.';
        traderGuidance =
            'Fokus pada peluang buy on pullback dengan konfirmasi indikator RSI di atas level 50. Perhatikan pernyataan pejabat FOMC berikutnya untuk validasi proyeksi suku bunga.';
      } else {
        impactAnalysis =
            'Sentimen pengetatan moneter hawkish atau penguatan indeks Dolar AS menekan valuasi emas.';
        transmissionMechanism =
            'Kenaikan imbal hasil obligasi AS membuat aset berbasis bunga lebih menarik dibanding emas, sementara Dolar yang lebih mahal mengurangi permintaan internasional.';
        traderGuidance =
            'Waspadai tekanan jual jangka pendek saat rilis data inflasi atau tenaga kerja AS melampaui estimasi. Lindungi posisi dengan Stop Loss ketat di atas swing high.';
      }
    } else {
      category = 'Dinamika Permintaan Fisik & Likuiditas Spot';
      if (sentiment == 'POSITIVE') {
        impactAnalysis =
            'Tingginya permintaan fisik emas dari perbankan sentral dan institusi global terus menjaga momentum apresiasi harga spot.';
        transmissionMechanism =
            'Diversifikasi cadangan devisa menjauhi dependensi Dolar menciptakan penyerapan pasokan fisik konstan di LBMA dan COMEX.';
        traderGuidance =
            'Gunakan strategi beli saat harga menguji support dinamis (buy on dips) selama struktur Moving Average (SMA 20/50) tetap menanjak.';
      } else {
        impactAnalysis =
            'Aksi ambil untung (profit-taking) pasca reli atau penyesuaian likuiditas institusi menciptakan tekanan koreksi teknikal pada pergerakan emas.';
        transmissionMechanism =
            'Likuidasi posisi beli spekulatif di pasar berjangka memicu penurunan jangka pendek menuju area likuiditas support berikutnya.';
        traderGuidance =
            'Tunggu konfirmasi pola pembalikan arah (candlestick reversal) di level support kunci sebelum membuka entri posisi baru.';
      }
    }

    return {
      'category': category,
      'impact': impactAnalysis,
      'mechanism': transmissionMechanism,
      'guidance': traderGuidance,
    };
  }

  @override
  Widget build(BuildContext context) {
    final explanation = _generateExplanation();
    final isBullish = article.sentimentLabel.toUpperCase() == 'POSITIVE';
    final isBearish = article.sentimentLabel.toUpperCase() == 'NEGATIVE';
    final sentimentColor = isBullish
        ? AppColors.bullish
        : (isBearish ? AppColors.bearish : AppColors.neutral);
    final sentimentText = isBullish
        ? 'BULLISH EMAS (XAU/USD)'
        : (isBearish ? 'BEARISH EMAS (XAU/USD)' : 'NETRAL / KONSOLIDASI');

    final double borderRadiusVal = isModalDialog ? 26.0 : 30.0;

    return ClipRRect(
      borderRadius: isModalDialog
          ? BorderRadius.circular(borderRadiusVal)
          : BorderRadius.vertical(top: Radius.circular(borderRadiusVal)),
      child: BackdropFilter(
        filter: ui.ImageFilter.blur(sigmaX: 30, sigmaY: 30),
        child: Container(
          decoration: BoxDecoration(
            color: const Color(0xFA0E121B), // Premium Deep Midnight Obsidian
            borderRadius: isModalDialog
                ? BorderRadius.circular(borderRadiusVal)
                : BorderRadius.vertical(top: Radius.circular(borderRadiusVal)),
            border: Border.all(
              color: sentimentColor.withValues(alpha: 0.28),
              width: 1.2,
            ),
            boxShadow: [
              BoxShadow(
                color: sentimentColor.withValues(alpha: 0.14),
                blurRadius: 36,
                spreadRadius: -4,
                offset: const Offset(0, 10),
              ),
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.8),
                blurRadius: 40,
                spreadRadius: 8,
              ),
            ],
          ),
          constraints: BoxConstraints(
            maxHeight: isModalDialog
                ? 760
                : MediaQuery.of(context).size.height * 0.90,
          ),
          child: Column(
            children: [
              // Top Drag Handle (Mobile only)
              if (!isModalDialog)
                Padding(
                  padding: const EdgeInsets.only(top: 10, bottom: 4),
                  child: Center(
                    child: Container(
                      width: 44,
                      height: 5,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.28),
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                  ),
                ),

              // Modern Glass Navigation Header
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 14, 16, 12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Category Badge with Glowing Accent
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4.5),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            AppColors.primary.withValues(alpha: 0.22),
                            AppColors.primary.withValues(alpha: 0.08),
                          ],
                        ),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: AppColors.primary.withValues(alpha: 0.45),
                          width: 0.9,
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(CupertinoIcons.sparkles, color: AppColors.primary, size: 13),
                          const SizedBox(width: 6),
                          Text(
                            explanation['category']!,
                            style: const TextStyle(
                              color: AppColors.primary,
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                              letterSpacing: 0.3,
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Modern Frosted Close Button
                    GestureDetector(
                      onTap: () => Navigator.of(context).pop(),
                      child: Container(
                        padding: const EdgeInsets.all(7),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.08),
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white.withValues(alpha: 0.15), width: 0.8),
                        ),
                        child: const Icon(
                          CupertinoIcons.xmark,
                          color: AppColors.textPrimary,
                          size: 14,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const Divider(height: 1, color: AppColors.borderSubtle),

              // Scrollable Article Body
              Expanded(
                child: SingleChildScrollView(
                  physics: const BouncingScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Full Article Title
                      Text(
                        article.title,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 18.5,
                          fontWeight: FontWeight.w800,
                          height: 1.35,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(height: 12),

                      // Metadata Tags Row (Source + Time WIB + Read Time)
                      Wrap(
                        spacing: 8,
                        runSpacing: 6,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                            decoration: BoxDecoration(
                              color: const Color(0xFF1B2130),
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: AppColors.borderSubtle),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(CupertinoIcons.antenna_radiowaves_left_right, color: AppColors.primary, size: 11),
                                const SizedBox(width: 5),
                                Text(
                                  article.source,
                                  style: const TextStyle(
                                    color: AppColors.textPrimary,
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Text(
                            article.publishedAt.formatWibFull(),
                            style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                          ),
                          Container(
                            width: 3,
                            height: 3,
                            decoration: const BoxDecoration(
                              color: AppColors.textMuted,
                              shape: BoxShape.circle,
                            ),
                          ),
                          const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(CupertinoIcons.clock, color: AppColors.textMuted, size: 11),
                              SizedBox(width: 4),
                              Text(
                                '2 mnt baca',
                                style: TextStyle(color: AppColors.textMuted, fontSize: 11),
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 18),

                      // Hero Sentiment Glass Matrix Card
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                            colors: [
                              sentimentColor.withValues(alpha: 0.16),
                              const Color(0xFF121724).withValues(alpha: 0.8),
                            ],
                          ),
                          borderRadius: BorderRadius.circular(18),
                          border: Border.all(
                            color: sentimentColor.withValues(alpha: 0.40),
                            width: 1.0,
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: sentimentColor.withValues(alpha: 0.10),
                              blurRadius: 18,
                              spreadRadius: -2,
                            ),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'DAMPAK TERHADAP EMAS',
                                  style: TextStyle(
                                    color: AppColors.textMuted,
                                    fontSize: 10.5,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 0.7,
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: sentimentColor.withValues(alpha: 0.20),
                                    borderRadius: BorderRadius.circular(10),
                                    border: Border.all(color: sentimentColor.withValues(alpha: 0.5)),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        isBullish
                                            ? CupertinoIcons.arrow_up_right_circle_fill
                                            : (isBearish ? CupertinoIcons.arrow_down_right_circle_fill : CupertinoIcons.equal_circle_fill),
                                        color: sentimentColor,
                                        size: 13,
                                      ),
                                      const SizedBox(width: 5),
                                      Text(
                                        sentimentText,
                                        style: TextStyle(
                                          color: sentimentColor,
                                          fontSize: 10.5,
                                          fontWeight: FontWeight.w800,
                                          letterSpacing: 0.3,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 14),
                            Row(
                              children: [
                                Text(
                                  'Skor Kuantitatif NLP: ',
                                  style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                                ),
                                Text(
                                  '${article.sentimentScore >= 0 ? '+' : ''}${article.sentimentScore.toStringAsFixed(2)}',
                                  style: TextStyle(
                                    color: sentimentColor,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w800,
                                    fontFamily: 'monospace',
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: ClipRRect(
                                    borderRadius: BorderRadius.circular(4),
                                    child: LinearProgressIndicator(
                                      value: ((article.sentimentScore + 1.0) / 2.0).clamp(0.0, 1.0),
                                      backgroundColor: const Color(0xFF1F2636),
                                      valueColor: AlwaysStoppedAnimation<Color>(sentimentColor),
                                      minHeight: 6,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 18),

                      // Section: Rangkuman Berita
                      _buildSectionHeader(CupertinoIcons.doc_plaintext, 'RANGKUMAN BERITA'),
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFF131826),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppColors.borderSubtle),
                        ),
                        child: Text(
                          article.summary ?? 'Tidak ada ringkasan teks tambahan yang disediakan.',
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 13,
                            height: 1.55,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Section: Analisis Dampak Pasar
                      _buildSectionHeader(CupertinoIcons.bolt_fill, 'ANALISIS & RESPON PASAR'),
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFF131826),
                          borderRadius: BorderRadius.circular(14),
                          border: Border(
                            left: BorderSide(color: sentimentColor, width: 3.5),
                            top: const BorderSide(color: AppColors.borderSubtle, width: 0.8),
                            right: const BorderSide(color: AppColors.borderSubtle, width: 0.8),
                            bottom: const BorderSide(color: AppColors.borderSubtle, width: 0.8),
                          ),
                        ),
                        child: Text(
                          explanation['impact']!,
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 12.8,
                            height: 1.5,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Section: Mekanisme Transmisi
                      _buildSectionHeader(CupertinoIcons.arrow_right_arrow_left, 'MEKANISME TRANSMISI KE XAU/USD'),
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFF131826),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppColors.borderSubtle),
                        ),
                        child: Text(
                          explanation['mechanism']!,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12.5,
                            height: 1.5,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Section: Panduan Trader
                      _buildSectionHeader(CupertinoIcons.lightbulb_fill, 'PANDUAN TAKTIKAL TRADER'),
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              AppColors.primary.withValues(alpha: 0.12),
                              const Color(0xFF151B28),
                            ],
                          ),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppColors.primary.withValues(alpha: 0.35)),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(CupertinoIcons.checkmark_shield_fill, color: AppColors.primary, size: 17),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                explanation['guidance']!,
                                style: const TextStyle(
                                  color: AppColors.textPrimary,
                                  fontSize: 12.5,
                                  height: 1.5,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              ),

              // Sticky Modern Bottom Action Bar
              Container(
                padding: EdgeInsets.fromLTRB(20, 12, 20, math.max(16.0, MediaQuery.paddingOf(context).bottom + 8)),
                decoration: BoxDecoration(
                  color: const Color(0xFF0C1018).withValues(alpha: 0.94),
                  border: const Border(top: BorderSide(color: AppColors.borderSubtle)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Container(
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFFE5A93C), Color(0xFFF59E0B)],
                          ),
                          borderRadius: BorderRadius.circular(14),
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFFF59E0B).withValues(alpha: 0.30),
                              blurRadius: 16,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: CupertinoButton(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          borderRadius: BorderRadius.circular(14),
                          onPressed: () => _openOriginalUrl(context),
                          child: const Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(CupertinoIcons.arrow_up_right_square, size: 16, color: Colors.black),
                              SizedBox(width: 8),
                              Text(
                                'Buka Sumber Asli',
                                style: TextStyle(
                                  color: Colors.black,
                                  fontSize: 13,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Container(
                      decoration: BoxDecoration(
                        color: const Color(0xFF1B2232),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppColors.borderSubtle),
                      ),
                      child: CupertinoButton(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        borderRadius: BorderRadius.circular(14),
                        onPressed: () => _copyLink(context),
                        child: const Icon(CupertinoIcons.share, size: 16, color: AppColors.textPrimary),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(IconData icon, String title) {
    return Row(
      children: [
        Icon(icon, color: AppColors.primary, size: 13),
        const SizedBox(width: 6),
        Text(
          title,
          style: const TextStyle(
            color: AppColors.textMuted,
            fontSize: 11,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.6,
          ),
        ),
      ],
    );
  }
}
