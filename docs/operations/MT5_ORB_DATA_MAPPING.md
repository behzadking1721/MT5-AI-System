# MT5 → ORB Data Mapping (for P1/P4 wiring)

هدف: پس از اتصال read-only MCP، داده‌های لازم برای `modules.strategy_lab.analyze_orb` و `RiskManager` از MT5 تهیه شود. **هیچ ابزاری تا تکمیل P0/P1 inventory و تأیید مجوزها فراخوانی نشود.**

## ورودی‌های تحلیل ORB (هر نماد/جلسه)
| مورد | نیاز | منبع احتمالی MCP (پس از P1 تایید نام واقعی ابزار) | تبدیل/اعتبارسنجی |
|---|---|---|---|
| کندل‌های 1m بازه رنج باز شدن (مثلاً 5 دقیقه اول جلسه) | OHLCV + زمان سرور | Terminal/Market Data (rates/bars) | `modules.market_data.normalize_bars`, `validate_bars(expected_interval_seconds=60)` |
| کندل‌های روزانه ≥15 روز گذشته | OHLCV | Terminal/Market Data | محاسبه `ATR14` و `avg_volume14` با `build_daily_stats` |
| حجم رنج باز شدن 14 جلسه قبل (همان n دقیقه) | لیست 14 مقدار | استخراج از کندل‌های 1m/تیک یا آمار ذخیره‌شده | `relative_volume` |
| مشخصات نماد | tick_size, tick_value, volume_min/max/step, ارز | Terminal symbol info | ورودی sizing در `RiskManager` |
| زمان باز/بسته جلسه و timezone سرور | session_open, EoD | Terminal/Market Data | هم‌راستاسازی زمان کندل‌ها |

## خروجی تحلیل (بدون معامله)
- `ORBSignal`: جهت، `entry_price` (شکست ORH/ORL)، `stop_loss` = `ATR14*atr_stop_fraction`، `take_profit_time` EoD، `eligible` و دلایل/کیفیت داده.
- `RiskDecision` (اختیاری، با ورودی equity/limits): حجم/مبلغ/درصد ریسک یا رد امن.
- گزارش خوانا: `scripts/orb_report.py`؛ JSON: `scripts/analyze_orb_payload.py`.

## الزامات ایمنی
- فقط خواندن داده در P1؛ Trading غیرفعال/تأیید صریح.
- اجرای سفارش در این مسیر مجاز نیست؛ هر Execution تنها پس از RiskManager + تأیید انسانی صریح و سیاست Demo (P8) و هرگز Live پیش‌فرض.
- اسرار/توکن/شماره حساب در خروجی‌ها ثبت نشود.

## آماده‌سازی تا زمان اتصال
- نمونه payload: `data/samples/{intraday,daily,prev_or}_sample.json` (محلی، ignore در git طبق policy نمونه‌ها ممکن است ignore شود).
- تست پل: `tests/unit/test_strategy_pipeline.py`، `tests/unit/test_market_data.py`.
