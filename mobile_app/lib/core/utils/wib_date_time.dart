// Utility & Extension for Indonesian Western Standard Time (Waktu Indonesia Barat - WIB / UTC+7).
// Ensures all timestamps, economic schedules, candles, and news articles across the application
// are accurately displayed in Indonesian WIB without relying on external system locale settings.

/// Safely parses any ISO-8601 timestamp string from backend (FastAPI / SQLite) as UTC.
/// Naive strings without 'Z' or timezone offset (common from SQLite) are treated explicitly as UTC
/// so `.toWib()` always converts accurately to WIB (UTC+7) without a 7-hour shift!
DateTime parseUtcDateTime(String? raw, {DateTime? fallback}) {
  final fb = (fallback ?? DateTime.now()).toUtc();
  if (raw == null || raw.trim().isEmpty) return fb;
  final s = raw.trim();
  final dt = DateTime.tryParse(s);
  if (dt == null) return fb;
  if (dt.isUtc) return dt;
  // Check whether the original string carried an explicit timezone offset (e.g. +07:00 or -04:00)
  final hasExplicitOffset = RegExp(r'(Z|[+-]\d{2}:?\d{2})$', caseSensitive: false).hasMatch(s);
  if (hasExplicitOffset) {
    return dt.toUtc();
  }
  // Naive timestamp from SQLite -> treat its wall-clock fields as UTC explicitly
  return DateTime.utc(
    dt.year,
    dt.month,
    dt.day,
    dt.hour,
    dt.minute,
    dt.second,
    dt.millisecond,
    dt.microsecond,
  );
}

extension WibDateTimeExtension on DateTime {
  /// Converts any DateTime (UTC or system local) to Indonesian WIB (UTC+7).
  DateTime toWib() {
    final utc = isUtc ? this : toUtc();
    return utc.add(const Duration(hours: 7));
  }

  /// Formats to full Indonesian WIB date & time:
  /// e.g. "30 Sep 2026 • 11:45 WIB"
  String formatWibFull({bool withSeconds = false}) {
    final w = toWib();
    final sec = withSeconds ? ':${w.second.toString().padLeft(2, '0')}' : '';
    return '${w.day} ${_monthNameId(w.month)} ${w.year} • ${w.hour.toString().padLeft(2, '0')}:${w.minute.toString().padLeft(2, '0')}$sec WIB';
  }

  /// Formats to short Indonesian WIB date & time:
  /// e.g. "30 Sep • 11:45 WIB"
  String formatWibShort({bool withSeconds = false}) {
    final w = toWib();
    final sec = withSeconds ? ':${w.second.toString().padLeft(2, '0')}' : '';
    return '${w.day} ${_monthNameId(w.month)} • ${w.hour.toString().padLeft(2, '0')}:${w.minute.toString().padLeft(2, '0')}$sec WIB';
  }

  /// Formats to Indonesian WIB date with day name:
  /// e.g. "Rabu, 30 Sep 2026 • 11:45 WIB"
  String formatWibWithDay({bool withSeconds = false}) {
    final w = toWib();
    final sec = withSeconds ? ':${w.second.toString().padLeft(2, '0')}' : '';
    return '${_dayNameId(w.weekday)}, ${w.day} ${_monthNameId(w.month)} ${w.year} • ${w.hour.toString().padLeft(2, '0')}:${w.minute.toString().padLeft(2, '0')}$sec WIB';
  }

  /// Formats to time-only in WIB:
  /// e.g. "11:45 WIB" or "11:45:30 WIB"
  String formatWibTime({bool withSeconds = false}) {
    final w = toWib();
    final sec = withSeconds ? ':${w.second.toString().padLeft(2, '0')}' : '';
    return '${w.hour.toString().padLeft(2, '0')}:${w.minute.toString().padLeft(2, '0')}$sec WIB';
  }

  static String _monthNameId(int month) {
    switch (month) {
      case 1:
        return 'Jan';
      case 2:
        return 'Feb';
      case 3:
        return 'Mar';
      case 4:
        return 'Apr';
      case 5:
        return 'Mei';
      case 6:
        return 'Jun';
      case 7:
        return 'Jul';
      case 8:
        return 'Ags';
      case 9:
        return 'Sep';
      case 10:
        return 'Okt';
      case 11:
        return 'Nov';
      case 12:
        return 'Des';
      default:
        return '';
    }
  }

  static String _dayNameId(int weekday) {
    switch (weekday) {
      case 1:
        return 'Senin';
      case 2:
        return 'Selasa';
      case 3:
        return 'Rabu';
      case 4:
        return 'Kamis';
      case 5:
        return 'Jumat';
      case 6:
        return 'Sabtu';
      case 7:
        return 'Minggu';
      default:
        return '';
    }
  }
}
