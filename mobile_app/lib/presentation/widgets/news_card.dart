import 'package:flutter/cupertino.dart';
import '../../core/constants/app_colors.dart';
import '../../core/utils/wib_date_time.dart';
import '../../data/models/news_article_model.dart';
import 'ios_glass_card.dart';
import 'news_detail_sheet.dart';

class NewsCard extends StatelessWidget {
  final NewsArticleModel article;

  const NewsCard({super.key, required this.article});

  @override
  Widget build(BuildContext context) {
    Color sentimentColor;
    String sentimentText;
    IconData sentimentIcon;

    switch (article.sentimentLabel.toUpperCase()) {
      case 'POSITIVE':
        sentimentColor = AppColors.bullish;
        sentimentText = 'BULLISH';
        sentimentIcon = CupertinoIcons.arrow_up_right;
        break;
      case 'NEGATIVE':
        sentimentColor = AppColors.bearish;
        sentimentText = 'BEARISH';
        sentimentIcon = CupertinoIcons.arrow_down_right;
        break;
      default:
        sentimentColor = AppColors.neutral;
        sentimentText = 'NETRAL';
        sentimentIcon = CupertinoIcons.equal;
    }

    return GestureDetector(
      onTap: () => NewsDetailSheet.show(context, article),
      behavior: HitTestBehavior.opaque,
      child: IosGlassCard(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        padding: const EdgeInsets.all(16),
        borderRadius: 18,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Row: Sentiment Badge + Score and Source
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: sentimentColor.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: sentimentColor.withValues(alpha: 0.4), width: 0.8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(sentimentIcon, color: sentimentColor, size: 11),
                      const SizedBox(width: 4),
                      Text(
                        '$sentimentText (${article.sentimentScore > 0 ? '+' : ''}${article.sentimentScore.toStringAsFixed(2)})',
                        style: TextStyle(
                          color: sentimentColor,
                          fontSize: 9.5,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.4,
                        ),
                      ),
                    ],
                  ),
                ),
                Text(
                  article.publishedAt.formatWibShort(),
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // News Title
            Text(
              article.title,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 14.5,
                fontWeight: FontWeight.w600,
                height: 1.35,
                letterSpacing: -0.2,
              ),
            ),
            const SizedBox(height: 6),

            // Summary
            if (article.summary != null && article.summary!.isNotEmpty) ...[
              Text(
                article.summary!,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                  height: 1.4,
                ),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 10),
            ],

            // Source and Tap for Explanation Affordance
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(CupertinoIcons.news, color: AppColors.textMuted, size: 13),
                    const SizedBox(width: 5),
                    Text(
                      article.source,
                      style: const TextStyle(
                        color: AppColors.textMuted,
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
                Row(
                  children: [
                    Text(
                      'Buka & Penjelasan',
                      style: TextStyle(
                        color: AppColors.primary.withValues(alpha: 0.85),
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(width: 3),
                    const Icon(CupertinoIcons.chevron_right, color: AppColors.primary, size: 12),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
