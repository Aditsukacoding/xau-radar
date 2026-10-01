import 'dart:ui_web' as ui_web;
import 'package:flutter/material.dart';
import 'package:web/web.dart' as web;

web.HTMLIFrameElement? _activeIframe;
bool _viewFactoryRegistered = false;
const String _singletonViewType = 'tradingview-embed-singleton';

Widget buildTradingViewWidget({
  required String symbol,
  required String interval,
  double height = 480,
}) {
  final tvInterval = _mapTimeframe(interval);
  final srcUrl =
      'https://s.tradingview.com/widgetembed/?symbol=${Uri.encodeComponent(symbol)}&interval=$tvInterval&hidesidetoolbar=0&symboledit=1&saveimage=0&toolbarbg=131722&theme=dark&style=1&timezone=Asia%2FJakarta&locale=id';

  if (!_viewFactoryRegistered) {
    _viewFactoryRegistered = true;
    ui_web.platformViewRegistry.registerViewFactory(
      _singletonViewType,
      (int viewId) {
        final iframe = web.HTMLIFrameElement()
          ..src = srcUrl
          ..style.border = 'none'
          ..style.width = '100%'
          ..style.height = '100%';
        _activeIframe = iframe;
        return iframe;
      },
    );
  } else if (_activeIframe != null && _activeIframe!.src != srcUrl) {
    _activeIframe!.src = srcUrl;
  }

  return Container(
    height: height,
    width: double.infinity,
    decoration: BoxDecoration(
      color: const Color(0xFF131722),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
    ),
    clipBehavior: Clip.antiAlias,
    child: const HtmlElementView(viewType: _singletonViewType),
  );
}

String _mapTimeframe(String tf) {
  switch (tf.toLowerCase()) {
    case '1m':
      return '1';
    case '5m':
      return '5';
    case '15m':
      return '15';
    case '1h':
      return '60';
    case '4h':
      return '240';
    case '1d':
    case 'd':
      return 'D';
    default:
      return '60';
  }
}
