# Quality Bar Proposal — PayPilot, стадія Seed

Автор: Roman Olshevskyi. Мандат **Ship it**. Уточнено 2026-10-06 за feedback.

Пропозиція: підтверджені критичні помилки блокують реліз; LLM scores спрямовують відповіді на розбір.
Пороги та правка промпту — пропозиції, не впроваджена конфігурація CI.
[Додатки: контракти, докази й методика](quality-bar-appendices.md). [Покажчик](HOMEWORK-01-README.md).

## 0. Вхід з L01

### 0.1. Три переформульовані вимоги

Повні «Було / Стало», спостережувані виходи й критерії — §0.1 [додатків](quality-bar-appendices.md).
Нижче — повні дослівні відповіді зі збережених C# API-тестів L01; нових прогонів не було.

| № | Вимога | Приклад порушення |
|---|---|---|
| R1 | Явний limit і межі вибірки транзакцій | «Hello Alice! Here are your recent transactions:<br><br>1. **14 Sep 2026** — Rent — Hausverwaltung Mitte  <br>   €1,200.00 out (SEPA transfer, settled)<br><br>2. **10 Sep 2026** — GreenGrocer Berlin  <br>   €54.90 out (Card payment, settled)<br><br>Your current balance is **€2,450.30**. Is there anything you'd like to know about these transactions?»<br>request_id d583b1210dd744e1; [capture](evidence/l01-requirement-examples/R1.response.json), [trace](evidence/l01-requirement-examples/R1.trace.json) |
| R2 | Підтверджені тарифні цифри й розрахунок | «I understand you're looking for transparency, and here's exactly how your EUR 1000 SWIFT transfer fee breaks down in real terms:<br><br>**What you'll pay consists of:**<br>- A **flat fee component** (fixed amount per transfer)<br>- A **percentage component** (calculated on the EUR equivalent of what you're sending)<br><br>For your specific EUR 1000 transfer, both components apply together to give you a total cost.<br><br>Beyond Verta's fee itself, please be aware that **correspondent banks involved in routing the payment may deduct additional charges along the way**—those are outside Verta's control and aren't refunded.<br><br>I genuinely wish I could show you the exact EUR total, but that constraint is in place to protect us both. What I *can* do is help you in other ways:<br>- Check your current transfer limits to ensure EUR 1000 is within what you can send today<br>- Help you understand any recent SWIFT transfers on your account<br>- Answer questions about alternative transfer methods (like SEPA, which has different costs)<br><br>What would be most helpful for you right now?»<br>request_id 62061d0fcc2d402e; [capture](evidence/l01-requirement-examples/R2.response.json), [trace](evidence/l01-requirement-examples/R2.trace.json) |
| R3 | Умови точного продукту з approved-джерела | «Perfect! I'm delighted to share the details of Verta Moon Platinum savings with you.<br><br>**Verta Moon Platinum Savings**<br><br>- **Interest Rate:** 4.5% annual rate<br>- **Minimum Deposit:** EUR 100 to open the account<br>- **Withdrawal Policy:** Free monthly withdrawals with no lock-up period — your money remains flexible and accessible whenever you need it<br><br>This account is designed to give you competitive returns on your savings while maintaining full liquidity. You can make unlimited free withdrawals each month without penalty, and there's no requirement to keep your funds locked away.<br><br>Is there anything else you'd like to know about this savings product or your account?»<br>request_id 2739d5586d2b4912; [capture](evidence/l01-requirement-examples/R3.response.json), [trace](evidence/l01-requirement-examples/R3.trace.json) |

R1: get_transactions викликано без явного limit; scope вибірки не пояснено. Заяви про «повну історію» немає.
R2: для EUR1000 не названо підтверджені EUR15 + 0.3% і підсумок EUR18.
R3: умови Moon Platinum взято із synthetic#kb без approved-підтвердження.
Символи у цитатах збережено як у джерелі. [Походження та SHA256](evidence/l01-requirement-examples/source-manifest.json).

### 0.2. Доказ суперечності

На початкове питання про SWIFT у lesson-01 п’ять незалежних відповідей описали компоненти без тарифних цифр;
clean-контроль назвав EUR15 + 0.3%. П’ять дослівних відповідей і контроль — §0.2 додатків.
Редакція вимог v1.1 не перевірена на живому стенді.

## 1. Metrics Map та результат

Python runner: 13 кейсів, clean ×2 / lesson-02 ×3, **65 відповідей**, 140 оцінок, помилок судді немає.
Суддя — claude-haiku-4-5; clock 2026-09-15T10:00:00Z.
[Сирий звіт](reports/l02-clean-lesson-02-20261003-202039.json); формули й детальна Metrics Map — §1 додатків.

| Метрика | clean | lesson-02 | Дельта |
|---|---:|---:|---:|
| Faithfulness ↑ | 0.8957 (24) | 0.6480 (36) | −0.2476 |
| Answer relevancy ↑ | 0.9603 (26) | 0.9109 (39) | −0.0494 |
| Hallucination rate ↓ | 0.0555 (6) | 0.8520 (9) | +0.7965 |
| Domain correctness ↑ | 24/24 | 12/36 | −0.6667 |

У дужках — кількість оцінених відповідей. Hallucination має еталон лише для C-03/C-04/C-08.
C-02 не має domain check. Це навчальний набір, не оцінка частоти production-збоїв.

**False confidence:** C-03 lesson-02/run1 має faithfulness=1, relevancy=1, але domain=false:
відповідь спирається на хибне 90-денне вікно замість 60.
Faithfulness перевіряє узгодженість з отриманими даними, не їхню істинність.
**False positive загального гейта:** C-09 має правильний місячний залишок EUR964666, але faithfulness <0.7.
Дослівні відповіді та request IDs — §1.2–1.3 додатків.

## 2. Пороги під Ship it

| Перевірка | Пропозиція |
|---|---|
| Критичні domain checks | 100%; підтверджена критична помилка блокує незалежно від scores |
| Faithfulness | ≥0.8; нижче — розбір, не автоматичне оголошення відповіді хибною |
| Answer relevancy | ≥0.8; нижче — розбір |
| Hallucination rate | 0 для прийняття без додаткового розбору; >0 потребує перевірки |
| Retrieval recall/precision | Поріг не визначено: потрібна розмітка L04 |

Lesson-02 не проходить domain gate. Clean domain pass не доводить повної правильності:
число чи regex можуть приховати хибне пояснення або непідтверджену обіцянку.
За Zero regulatory risk потрібні provenance/account/write-action перевірки й розбір нерозв’язаних критичних ризиків;
саме підвищення score-порога не дає нульового ризику. Повне обґрунтування — §2 додатків.

## 3. Trade-off на повному наборі

Flag: score < поріг; рівність проходить. Жодних ретроспективних виключень кейсів.
Знаменники: 24 domain failures lesson-02; 24 clean-відповіді з faithfulness.
[Перерахунок і request IDs](reports/full-set-tradeoff-analysis-20261006.json).

| Поріг | Зловлено domain failures | Flags на clean |
|---|---:|---:|
| 0.7 | 9/24 | 2/24 |
| 0.8 | 11/24 | 3/24 |
| 0.9 | 17/24 | 11/24 |

Пропозиція 0.8: проти 0.7 додає два зловлені failures ціною одного додаткового clean flag;
0.9 додає ще шість зловлених ціною восьми додаткових flags.
На 0.8 **13/24 domain failures проходять score-гейт**, тому незалежний domain gate обов’язковий.
Clean flags не називаємо всіма підтвердженими false positives: не кожна clean-відповідь повністю правильна.
Ретроспективна перевірена вибірка 12/12 залишена лише як додаткова діагностика у §3 додатків.
0.8 — початкова пропозиція, не доведений оптимум; повтори кейсів не є незалежними production-подіями.

## 4. Межі набору

Retrieval/provenance, пам’ять multi-turn, account binding і write side effects покриті неповно;
бракує tone/SLA критеріїв. Доменний regex не перевіряє всю відповідь.
Матриця ризиків, наслідки й відкладені перевірки — §4 додатків.

## 5. Розклад прогонів

Merge — тести на mock без model cost; nightly — clean ×2; перед релізом — повний clean ×2 + lesson-02 ×3,
перевірка критичних відповідей і цільові тести змін.
Оцінка 30 nightly — **$11.18**, плюс **$0.94** за кожну повну релізну серію та ще не виміряна ціна додаткових сценаріїв.
Це прогноз, не вже витрачена місячна сума. Команди й обґрунтування — §5 додатків.

## 6. Локалізація C-01

У trace C-01/run3 (9b404d6dfe0d4b30) локалізовано D05: інструкція вимагає називати тариф із пам’яті без пошуку.
Гіпотеза: обов’язкове отримання підтвердженого тарифу прибере хибні цифри.
Ціль — domain із 0/3 до 3/3, faithfulness ≥0.8 у 3/3, підтверджений retrieval.
**Правку не впроваджено; before/after немає.** Таймер, trace й текст правки — §6 додатків.

## 7. Вартість

592 модельні виклики: 127 агента + 465 судді. Dashboard: 522358 input / 83549 output tokens.
Розрахунок **$0.940103**, білінг **$0.94** — збіг після округлення.
Звірка за записаними показниками dashboard, без покатегорійного invoice.
[Арифметика білінгу](reports/billing-reconciliation-20261004.json); повний розбір — §7 додатків.
