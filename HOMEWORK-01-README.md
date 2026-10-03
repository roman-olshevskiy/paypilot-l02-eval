# ДЗ №1 — артефакти для перевірки

Автор: Roman Olshevskyi. Гілка здачі: main.

Здача відбувається через main власного репозиторію.
Посилання для LMS: [гілка з роботою](https://github.com/roman-olshevskiy/paypilot-l02-eval/tree/main).
Спосіб здачі відповідає вимозі завдання: файли у main публічного репозиторію.
Гілка доступна на GitHub; після наступного push потрібно перевірити актуальність файлів.

## Основний документ

[quality-bar-proposal.md](quality-bar-proposal.md) — повний документ ДЗ.

| Частина | Де читати |
|---|---|
| Вхід із L01: R1–R3, п’ять SWIFT-відповідей і clean-контроль | §0 основного документа |
| Метрики, baseline, дельти, false confidence / false positive | §1 |
| Пороги й мандат Ship it | §2 |
| Trade-off на 0.7 / 0.8 / 0.9 | §3 |
| Межі набору та ризики | §4 |
| Розклад прогонів | §5 |
| Аудит червоного кейса | §6 |
| Вартість і звірка білінгу | §7 |

## Докази та розрахунки

| Артефакт | Призначення |
|---|---|
| [Сирий eval JSON](reports/l02-clean-lesson-02-20261003-202039.json) | 65 відповідей: clean ×2, lesson-02 ×3 |
| [Журнал прогону](reports/full-run-20261003.txt) | Реальний запуск runner |
| [Run manifest](reports/run-manifest-20261003.json) | Команда, параметри й SHA256 вихідних файлів |
| [Метрики](reports/metrics-analysis-20261003.json) | Похідні baseline та дельти |
| [Trade-off](reports/tradeoff-analysis-20261003.json) | Мітки й розрахунок порогів |
| [Вартість розкладу](reports/schedule-cost-analysis-20261003.json) | Початкова оцінка за профілями |
| [Звірка білінгу](reports/billing-reconciliation-20261004.json) | Уточнення ціни за записаними показниками dashboard й офіційним прайсом |
| [L01 manifest](evidence/l01-swift/source-manifest.json) | Походження п’яти SWIFT-відповідей і clean-контролю; captures у цій самій папці |
| [L02 audit manifest](evidence/l02-audit/source-manifest.json) | Походження snapshot і trace |
| [Промпт аудиту](evidence/l02-audit/assembled-prompt.json) | Snapshot lesson-02 після eval |
| [Trace червоного кейса](evidence/l02-audit/C-01-run3.trace.json) | C-01/run3, request_id 9b404d6dfe0d4b30 |
| [Журнал audit-тесту](reports/audit-evidence-tests-20261003.txt) | 1/1 passed — отримання доказів |

## Відтворення й пояснення

- [README](README.md) — команда запуску, модель, профілі, clock і передумови.
- [cases.json](cases.json), [l02_eval.py](l02_eval.py), [requirements.txt](requirements.txt) — незмінні файли використаного прогону.
- [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml) — середовище запуску.
- [Audit-тест](tests/test_l02_audit_evidence.py) — read-only збір доказів.
- [Розбір кейсів](case-review.md), [підсумок прогону](run-summary.md).

Зелений evidence-тест підтверджує збір доказів. Правильність відповідей визначається окремими критеріями.
Повні документи L01 лишаються у paypilot-stand; необхідні фрагменти та докази вже включені в цей комплект.
