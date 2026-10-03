# Quality Bar Proposal — PayPilot, стадія Seed

Автор: Roman Olshevskyi. Дата створення чернетки: 2026-10-03.
Мандат: **Ship it**.

Пропозиція набору метрик і порогів для обговорення з CTO.

**Статус: чернетка.** Розділ 0 (R1–R3 і SWIFT-доказ) перенесено з L01. Власний прогін L02 виконано; §1 заповнено, §2–7 ще потрібно завершити. Вимоги R1–R3 є навчальною пропозицією; їхня редакція v1.1 не перевірена на живому стенді. Документ ще не готовий до здачі.

## Паспорт даних

| Поле | Значення |
|---|---|
| Скрипт | `l02_eval.py` |
| Профілі й кількість прогонів | Виконано `clean` × 2, `lesson-02` × 3; 13 кейсів, 65 відповідей |
| Модель судді (JUDGE_MODEL) | `claude-haiku-4-5` (Anthropic), підтверджено JSON-звітом |
| Дата прогону | 2026-10-03 |
| CLOCK_OVERRIDE | `2026-09-15T10:00:00Z`, підтверджено JSON-звітом |
| Сирі звіти | [l02-clean-lesson-02-20261003-202039.json](reports/l02-clean-lesson-02-20261003-202039.json); [консоль](reports/full-run-20261003.txt); [manifest](reports/run-manifest-20261003.json) |

Усі baseline, дельти, trade-off та вартість мають походити з власного прогону. Повноту зібраних результатів перевірено: 65 відповідей, 140 оцінок, 0 помилок судді. [Підсумок запуску](run-summary.md). Оцінки вартості ще не звірено з прайсом і білінгом.

## 0. Вхід з L01

### 0.1. Три переформульовані вимоги

Джерело: `paypilot-stand/course-work/L01/specification-review.md`, §4, редакція 2026-10-03. Цитати «Було» — зі знімка assembled prompt `lesson-01`, переноси рядків нормалізовано пробілами. Таблицю перенесено без зміни формулювань. Повний комплект L01 залишається в репозиторії paypilot-stand.

| № | Було | Стало | Спостережуваний вихід | Критерій | Приклад порушення |
|---|---|---|---|---|---|
| R1 | `When a customer asks about recent transactions, retrieve their recent transactions and answer from that list.` | `For a request for recent transactions without a date range, use the customer's specified account; if several accounts are possible and none is specified, ask which account before retrieving transactions. Call get_transactions with that account_id and an explicit limit: the requested positive integer count, or 20 if no count was requested. Describe the scope as the latest N transactions, not a calendar period. Present the returned transactions in tool order, with their dates, amounts and currencies unchanged. If fewer than N are returned, state the actual count; an empty successful list means no transactions were returned for this query. Do not claim that a limited list is the complete account history. If a date range is requested, ask for or use a tool-supported date-range query; do not claim that a count-limited list covers that period. On tool error, follow section 6.` | Запит; account_id і limit у tool call; повернутий список; відповідь із межами вибірки, датами, сумами та валютами. | Pass: рахунок відповідає запиту, limit=N або 20; усі повернуті записи наведено в порядку інструмента без зміни полів; scope — останні N, а якщо менше, названо фактичну кількість. Неоднозначний рахунок уточнено до виклику. Немає заяв про повну історію чи повне покриття періоду без відповідного результату інструмента. Error не підмінено порожнім списком. Порушення будь-якої умови — fail. | За 20 записів без фільтра дат: «Here is your complete transaction history for the last month.» |
| R2 | `Do NOT show worked examples with numbers.`; `Do NOT call tools to compute a fee figure to show the customer.`; `When you present a fee or conversion, show the components you used — rate, spread, applicable allowance — and a final amount consistent with them.` | `For fee or conversion questions, retrieve the published tariff or customer-specific quote. State public fee amounts, rates and spreads only when supported by those results. Show supported applicable components. If the input amount is known, show the tool total or a deterministic calculation using the retrieved formula and that amount; show the inputs. If the amount is missing, give the supported formula and ask for it. If pricing data is missing, follow section 6. Never disclose internal monitoring thresholds or review criteria.` | Тариф/quote у джерелах; сума запиту; компоненти, входи й підсумок у відповіді; відсутність внутрішніх порогів. | Pass: кожна тарифна цифра підтверджена джерелом; відома сума дає tool total або правильний розрахунок із показаними входами. EUR1000 за EUR15 + 0.3% дає EUR18, correspondent charges окремі. Без суми — формула й уточнення, без тарифу — fallback R3. Внутрішні критерії не розкриті. Порушення будь-якої умови — fail. | За підтвердженого тарифу EUR15 + 0.3% для EUR1000: «The Verta fee is EUR20: EUR15 flat fee plus EUR5 percentage fee.» |
| R3 | `For ANY question about a product or account type, always call search_knowledge_base first and answer from what it returns — the knowledge base is the authority on the Verta product range, and answering without it risks giving the customer stale terms.` | `For a named product or account type, search the knowledge base and state only terms explicitly associated with that product in an approved source. Similarity or generic terms are not confirmation. Without approved confirmation, say verified information is unavailable and do not assert product existence or rate/deposit/withdrawal terms. On tool error or empty result, say the requested data is unavailable, do not invent it, and offer a relevant document search or human escalation. Follow mandatory escalation rules in section 4 and source precedence in section 3.` | Назва продукту й search call; product identity та provenance джерела; заявлені умови або unavailable-відповідь; наступний крок. | Pass: кожна умова пов’язана з точним продуктом і approved-джерелом, статус якого перевірено за авторитетним реєстром/метаданими, не лише текстом фрагмента. synthetic#kb і схожа назва не є підтвердженням. Без нього, при error або empty — unavailable без вигаданих умов/існування, з пошуком документа або escalation; mandatory escalation rules збережено. Порушення будь-якої умови — fail. | Лише зі synthetic#kb без approved-підтвердження: «Moon Platinum offers 4.5% interest and requires a EUR100 minimum deposit.» |

R1 визначає «recent» за кількістю операцій; календарний діапазон потребує окремої підтримки інструмента. R3 потребує механізму перевірки approved-source provenance. Ці обмеження не слід трактувати як уже реалізовані можливості стенду.

### 0.2. Доказ суперечності

Джерело: §3 аудиту L01, C# / NUnit / RestSharp API-тест Swift_FiveIndependentRuns_AndCleanControl. Використано наявні captures від 2026-09-29 UTC; нового прогону не було. Кожен запит — у новій сесії. Відповіді наведено дослівно окремими блоками, щоб зберегти абзаци та форматування.

Питання:

~~~text
I'm CUS-0008. What is the fee for a SWIFT transfer at Verta?
~~~

Профіль: `lesson-01`. Прогонів: 5.

| Прогін | Що зробив агент | Дослівна відповідь |
|---|---|---|
| 1 | Описав складові без тарифних цифр | [Повний текст нижче](#swift-1) |
| 2 | Описав складові без тарифних цифр | [Повний текст нижче](#swift-2) |
| 3 | Описав складові без тарифних цифр | [Повний текст нижче](#swift-3) |
| 4 | Описав складові без тарифних цифр | [Повний текст нижче](#swift-4) |
| 5 | Описав складові без тарифних цифр | [Повний текст нижче](#swift-5) |

#### swift-1

Профіль: `lesson-01`; request_id: `be2a058a39fd4f05`; session_id: `csharp-l01-0750a84a9cbc4ca5b9888b49e441d61c`.

~~~text
For a SWIFT transfer at Verta, the fee is structured as follows:

**Flat fee:** A fixed component on every transfer

**Percentage fee:** A variable component calculated on the amount you're sending (in EUR equivalent)

The total fee combines both of these components. As an example structure: you'd pay the fixed flat amount regardless of size, then a small percentage on top of what you're transferring.

Additionally, please note that correspondent banks may deduct their own charges along the transfer route, and these are outside Verta's control and are not refunded by us.

If you're planning a specific transfer and would like to know the exact total cost, I'd be happy to help you calculate it if you let me know the amount and currency you're sending.
~~~

[Response JSON](evidence/l01-swift/swift-1.response.json) · [Trace](evidence/l01-swift/swift-1.trace.json)

#### swift-2

Профіль: `lesson-01`; request_id: `90f713a604574786`; session_id: `csharp-l01-ffe8764edacb4bcda50c147fda09f5de`.

~~~text
Thank you for asking! A SWIFT transfer at Verta consists of two components:

1. **Flat fee**: A fixed amount per transfer
2. **Percentage fee**: Calculated on the EUR equivalent of the amount you're sending

The exact total will depend on the size of your transfer. Correspondent bank charges that may be deducted along the way are handled by the receiving bank and fall outside Verta's control—we cannot refund those.

Is there a specific transfer amount you'd like to understand the cost for? I'm happy to walk through how it would work for your particular transaction.
~~~

[Response JSON](evidence/l01-swift/swift-2.response.json) · [Trace](evidence/l01-swift/swift-2.trace.json)

#### swift-3

Профіль: `lesson-01`; request_id: `ce6ce98aa1ce47ed`; session_id: `csharp-l01-93c793b316154656bfc8737e28c95cf7`.

~~~text
Thank you for asking! At Verta, a SWIFT transfer consists of two components:

1. **A flat fee** — charged per transfer
2. **A percentage fee** — calculated on the EUR equivalent of the amount you send

The exact total you'll pay depends on the size of your transfer. Additionally, correspondent banks may deduct their own charges along the way, which fall outside Verta's control and are not refunded.

When you're ready to make a specific SWIFT transfer, I'm happy to walk you through the exact breakdown for your amount. Would you like to know the fee structure for a particular transfer?
~~~

[Response JSON](evidence/l01-swift/swift-3.response.json) · [Trace](evidence/l01-swift/swift-3.trace.json)

#### swift-4

Профіль: `lesson-01`; request_id: `b2de5c7652814a6e`; session_id: `csharp-l01-618ee4f998b64a3280aa854076bc5899`.

~~~text
Thank you for asking! SWIFT transfers at Verta are straightforward to understand.

A SWIFT transfer consists of two components:

1. **Flat fee**: A fixed amount per transfer
2. **Percentage fee**: A small percentage of the amount you're sending (calculated on the EUR equivalent)

The total cost is the sum of both. For example, if you're sending a larger amount, the percentage element becomes more significant, while smaller transfers are dominated by the flat fee.

It's also worth knowing that correspondent banks along the transfer route may deduct their own charges, which are outside Verta's control and cannot be refunded — this is standard practice in international banking.

Is there a specific transfer amount you'd like me to help you with, or would you like to understand how this would work for your situation?
~~~

[Response JSON](evidence/l01-swift/swift-4.response.json) · [Trace](evidence/l01-swift/swift-4.trace.json)

#### swift-5

Профіль: `lesson-01`; request_id: `0dca685b7eaa4b71`; session_id: `csharp-l01-14a37dbfe2d74008a0fa8977e71e0217`.

~~~text
Thank you for asking! At Verta, a SWIFT transfer consists of two components:

1. **A flat fee** that applies to every SWIFT transfer
2. **A percentage fee** calculated on the EUR equivalent of the amount you're sending

The percentage is applied to ensure consistency across different currencies.

Additionally, it's important to note that correspondent banks along the transfer route may deduct their own charges, which are outside Verta's control and cannot be refunded.

Is there a specific SWIFT transfer you're planning? I'd be happy to help you understand the full cost or explore other transfer options if you'd like.
~~~

[Response JSON](evidence/l01-swift/swift-5.response.json) · [Trace](evidence/l01-swift/swift-5.trace.json)

**Розподіл:** 5/5 описали складові без суми/ставки; 0/5 назвали тарифні цифри; 0/5 відіслали до тарифів. Однаковий розподіл у lesson-01 не заперечує суперечності: контроль clean на тому самому питанні назвав тариф.

#### Контроль на clean

#### swift-clean-control

Профіль: `clean`; request_id: `8256cde7bd034a65`; session_id: `csharp-l01-fb60658998624d3a890c55fb823ec826`.

~~~text
For a SWIFT transfer at Verta, the fee structure is:

- **Flat fee:** EUR 15.00
- **Percentage fee:** 0.3% of the EUR equivalent of the transfer amount

The percentage is calculated on the EUR equivalent of whatever currency you are sending. Please note that correspondent bank charges deducted en route are outside Verta's control and are not refunded.

Is there a specific SWIFT transfer amount you'd like me to help you with?
~~~

[Response JSON](evidence/l01-swift/swift-clean-control.response.json) · [Trace](evidence/l01-swift/swift-clean-control.trace.json)

**Контрольний тариф:** EUR15 + 0.3% EUR-еквівалента. Без суми переказу очікується формула, а не кінцевий total; correspondent charges окремі. Clean control не є перевіркою навчальної редакції v1.1.

Копії 6 відповідей і 6 трейсів збережено без зміни байтів; походження й SHA256 — у [source manifest](evidence/l01-swift/source-manifest.json). Ці дані є доказом L01; вони не замінюють власний прогін L02 для §1–7.

## 1. Metrics Map

Дані: [власний JSON-прогін](reports/l02-clean-lesson-02-20261003-202039.json), 13 кейсів, clean ×2 / lesson-02 ×3. [Аналіз набору і меж перевірок](case-review.md). Формули перевірено за кодом установленої DeepEval 4.2.6 та l02_eval.py; пороги в цьому розділі не обираються.

| Шар | Тип збою | Метрика | Знаменник | Чому саме вона |
|---|---|---|---|---|
| Генерація | Твердження не підтверджене отриманим контекстом | Faithfulness ↑ | На відповідь: verdicts для виділених суддею claims; чисельник — YES, ambiguous штрафуються через penalize_ambiguous_claims=True. Агрегація: середнє оцінок відповідей, 24 clean / 36 lesson-02 | Порівнює відповідь із реально отриманими tool/retrieval даними. Не перевіряє істинність цих даних; хибний tool result може дати зелений score |
| Генерація | Відповідь повз питання | Answer relevancy ↑ | На відповідь: verdicts для виділених statements; проходять YES і BORDERLINE. Агрегація: 26 clean / 39 lesson-02 | Відділяє нерелевантний текст від відповіді на запит. Не доводить правильність тарифу, арифметики чи eligibility |
| Дія / застосування правила | Висновок або числовий результат не відповідає бізнес-правилу | Domain correctness ↑ | Пройдені domain checks / відповіді з domain check: 24 clean / 36 lesson-02; C-02 виключено | Незалежний модуль бізнес-правил, БД або статичний еталон перевіряє очікуваний результат. Це сімейство case-specific перевірок, не метрика фактичного виконання write tool; слабкі regex описані в case-review.md |
| Пошук | Потрібне правило не потрапило до контексту | Context recall ↑ | Релевантні еталонні одиниці інформації, потрібні для кейса | Не вимірюється в цьому наборі. Потребує розмітки релевантності та retrieval evaluation на L04; точну одиницю розмітки зафіксувати там |
| Пошук | Контекст містить зайві/нерелевантні фрагменти | Context precision ↑ | Для пропонованої простої частки: усі retrieved fragments; релевантні fragments — чисельник | Не вимірюється. На L04 зафіксувати розмітку, top-k і реалізацію; якщо застосовується ранговий precision, окремо визначити його формулу |
| Генерація | Відповідь суперечить незалежному курованому еталону | Hallucination rate ↓ | На відповідь: verdicts для context entries — 2 curated fragments + 1 результат oracle. Агрегація: лише C-03/C-04/C-08, 6 clean / 9 lesson-02 | Виявляє розходження з незалежним правилом, навіть коли faithfulness зелена. Локальне покриття трьох кейсів; повний курований еталон — L03 |

Числа claims/statements/verdicts кожної відповіді не збережені в сирому JSON: він містить підсумкові scores і reasons. Не можна відновити точний загальний claim-level знаменник із самих scores. Нижче рахуються середні answer-level scores, а не частка всіх claims у наборі. Domain correctness агрегує різні види перевірок; при зміні складу кейсів потрібне повторне порівняння за фіксованим набором.

### 1.1. Baseline та дельти

Арифметичне середнє всіх наявних оцінок кожного профілю. Пропущених оцінок і помилок судді немає. Дельта = lesson-02 − clean; округлення лише при показі. [Похідні розрахунки та SHA256 джерела](reports/metrics-analysis-20261003.json).

| Метрика | clean | Оцінених відповідей | lesson-02 | Оцінених відповідей | Дельта |
|---|---:|---:|---:|---:|---:|
| faithfulness | 0.8957 | 24 | 0.6480 | 36 | -0.2476 |
| answer_relevancy | 0.9603 | 26 | 0.9109 | 39 | -0.0494 |
| hallucination | 0.0555 | 6 | 0.8520 | 9 | +0.7965 |
| Domain correctness | 1.0000 (24/24) | 24 | 0.3333 (12/36) | 36 | -0.6667 |

Це частоти на навчальному наборі, не оцінка production-ризику. На lesson-02 доменні перевірки падають у C-01/C-03/C-04/C-05/C-06/C-07/C-08/C-12 у кожному з трьох повторів. Висока relevancy не компенсує ці помилки.

### 1.2. Підтверджений false confidence — C-03

Запит із cases.json:

~~~text
I am CUS-0004. Transaction TX-0402 was on July 14, a duplicate charge. Can I still dispute it today?
~~~

Незалежний еталон у JSON facts.C-03: window_days=60, deadline=2026-09-12, as_of=2026-09-15, eligible=false. Він обчислений disputes.check за політикою duplicate_charge, а не взятий із думки скаржника.

| Профіль / прогін | request_id | Faithfulness | Relevancy | Hallucination rate | Domain |
|---|---|---:|---:|---:|---|| clean / 1 | `1cf91d1cafa84bee` | 0.833 | 1 | 0 | True |
| clean / 2 | `e56f441282814027` | 1 | 1 | 0 | True |
| lesson-02 / 1 | `4a360573ecab4d8d` | 1 | 1 | 1 | False |
| lesson-02 / 2 | `9660f0a76d3c44db` | 0.857 | 1 | 1 | False |
| lesson-02 / 3 | `6cc1469a5d1e41a6` | 0.889 | 1 | 1 | False |

Дослівна відповідь lesson-02 / run 1:

~~~text
Good news. **Yes, you can still dispute this transaction today.** The duplicate charge is within the 90-day dispute window.

Here's the status:
- **Transaction date:** 14 July 2026
- **Today's date:** 15 September 2026
- **Dispute deadline:** 12 October 2026
- **All checks pass:** reason code is valid, transaction status allows it, you're within the window, and there are no compliance holds on your account.

You have 27 days remaining to open the dispute. Would you like me to proceed with opening it now?
~~~

Контроль clean / run 1, дослівно:

~~~text
Unfortunately, you cannot dispute this transaction today. The dispute window for duplicate charges is 60 days from the transaction date. Transaction TX-0402 from July 14, 2026 passed that deadline on September 12, 2026, and the window has now expired (we are on September 15, 2026).

You are outside the eligible window for disputing this charge. If you believe there are exceptional circumstances, I can escalate your case to a human agent for further review.
~~~

Розподіл: lesson-02 3/3 дозволяють спір і посилаються на 90 днів; clean 2/2 відмовляють через прострочене 60-денне вікно. У всіх трьох хибних відповідей faithfulness ≥0.85, relevancy=1.0, тоді як independent domain=false і hallucination rate=1.0. Faithfulness означає узгодженість із побаченим, не доменну істинність. Без окремо архівованих повних traces не робимо нового висновку про точний текст tool result; оцінки й reasons судді та еталон збережено у звіті.

### 1.3. Перевірений false positive загального гейта — C-09

Запит: `I'm CUS-0010. How much of my MONTHLY transfer limit is left?`

lesson-02 / run 2, request_id `f0dbc636328b4080`: faithfulness=0.667, relevancy=1.0, domain=true. Дослівна відповідь:
~~~text
Based on your account as of 15 September 2026, you have **EUR 964,666** of your monthly transfer limit remaining.

Your tier 3 monthly limit is EUR 1,000,000, and you've used EUR 35,334 so far this month.
~~~

Еталон facts.C-09: tier3, monthly_limit_eur=1000000, monthly_spent_eur=35334, monthly_remaining_eur=964666. Витрати = (4200+26000) GBP ×1.17 = EUR35334; залишок = EUR1000000 − EUR35334. Усі суми, валюта, дата й tier у відповіді узгоджені з еталоном; це підтверджує прийнятність цієї відповіді за перевірюваним доменним критерієм.

Гейт faithfulness <0.7 зупинив би її. Суддя пояснює низьку оцінку неоднозначністю прив’язки ліміту до tier у retrieval context. Це false positive **якщо faithfulness використати як загальний гейт доменної правильності**; ми не стверджуємо, що сам суддя помилився у вузькій перевірці представленого йому контексту. D22 не активний у lesson-02, цей кейс є контролем.

C-10 на clean не використовується як доказ false positive: no_offer проходить, але відповідь не дає чіткої відмови, а обіцянки контакту не підтверджені SLA. Domain pass тут недостатній для прийнятності. C-19 також потребує перевірки ширших тверджень про scope; not_regex не доводить повної правильності.

### 1.4. Faithfulness і hallucination на тих самих кейсах

Курований context кожного кейса має два фрагменти та доданий oracle result. У C-08 правило all-or-nothing є інтерпретацією fx.quote, не дослівною цитатою тарифу; походження розібрано в case-review.md.

| Кейс | Профіль / прогін | Faithfulness | Hallucination rate | Domain |
|---|---|---:|---:|---|| C-03 | clean / 1 | 0.833 | 0 | True |
| C-04 | clean / 1 | 0.778 | 0 | True |
| C-08 | clean / 1 | 0.889 | 0 | True |
| C-03 | clean / 2 | 1 | 0 | True |
| C-04 | clean / 2 | 0.875 | 0 | True |
| C-08 | clean / 2 | 0.875 | 0.333 | True |
| C-03 | lesson-02 / 1 | 1 | 1 | False |
| C-04 | lesson-02 / 1 | 1 | 0.667 | False |
| C-08 | lesson-02 / 1 | 0.583 | 0.667 | False |
| C-03 | lesson-02 / 2 | 0.857 | 1 | False |
| C-04 | lesson-02 / 2 | 0.6 | 0.667 | False |
| C-08 | lesson-02 / 2 | 0.857 | 1 | False |
| C-03 | lesson-02 / 3 | 0.889 | 1 | False |
| C-04 | lesson-02 / 3 | 0.75 | 0.667 | False |
| C-08 | lesson-02 / 3 | 0.9 | 1 | False |

Шкалу перевірено за встановленою DeepEval 4.2.6: HallucinationMetric повертає частку YES-verdicts узгодженості; l02_eval.py зберігає **1 − metric.score**, тому в JSON hallucination=0 означає відсутність визначених суддею суперечностей, 1 — максимальну частку суперечностей. Текст reason може описувати початковий score бібліотеки (наприклад 0.00), а JSON — уже інвертовану rate (1.0). Це не помилка запису.

C-04 lesson-02/run1 має faithfulness=1.0 при rate=0.667 і domain=false; C-08 lesson-02/run3 — 0.9 при rate=1.0 і domain=false. Це різні джерела порівняння й знаменники, тому scores не взаємозамінні. C-08 clean/run2 має domain=true, але rate=0.333: правильний підсумок сам по собі не доводить правильності всіх тверджень або безпомилковості судді; цей запис потребує окремого розбору перед використанням як еталонної правильної відповіді.

## 2. Пороги і чому саме такі

| Метрика | Поріг | Обґрунтування через бізнес-вплив |
|---|---|---|
| Потрібно визначити | Не обрано | Потрібно обґрунтувати |
| Потрібно визначити | Не обрано | Потрібно обґрунтувати |
| Потрібно визначити | Не обрано | Потрібно обґрунтувати |

**Мандат: Ship it.** За мандату **Zero regulatory risk** змінилося б: потрібно визначити конкретні метрики, пороги та бізнесові причини зміни.

## 3. Trade-off у цифрах

Метрика: ще не обрана. Джерело даних: додати точний JSON-звіт і правила відбору записів.

| Поріг | Хибних відповідей зловлено (lesson-02) | Правильних відповідей зупинено (clean) |
|---|---|---|
| 0.7 | Не виміряно | Не виміряно |
| 0.8 | Не виміряно | Не виміряно |
| 0.9 | Не виміряно | Не виміряно |

Обраний поріг і пояснення виграшу/ціни: ще не визначено. У кожній клітинці записати N із M. Правильність clean-відповідей перевірити; відсутні оцінки не трактувати як pass.

## 4. Межі набору

Щонайменше два класи збоїв, які обраний набір не покриває.

| Клас збою | Чому не ловиться | Ризик | Рішення |
|---|---|---|---|
| Потрібно визначити | Потрібно пояснити | Потрібно оцінити наслідок | Прийняти або відкласти до конкретного заняття |
| Потрібно визначити | Потрібно пояснити | Потрібно оцінити наслідок | Прийняти або відкласти до конкретного заняття |

## 5. Розклад прогонів

| Частота | Що входить | Критерій поділу | Ціна |
|---|---|---|---|
| Кожен merge (блокує) | Потрібно обрати кейси й метрики | Потрібно обґрунтувати | Не розраховано |
| Nightly | Потрібно обрати кейси й метрики | Потрібно обґрунтувати | Не розраховано |
| Перед релізом | Потрібно обрати кейси й метрики | Потрібно обґрунтувати | Не розраховано |

Критерій: детермінованість, вартість і неприйнятність збою за поточним мандатом. LLM-метрика в щоденному гейті потребує оцінки вартості.

## 6. Локалізація одного червоного кейса

Кейс: ще не обрано. Червона метрика й значення: ще не отримано. Аудит із таймером 15 хвилин: ще не виконано.

| Питання | Відповідь |
|---|---|
| Шар | Потрібно визначити |
| Рядок специфікації | Додати цитату з assembled prompt lesson-02 або опис відсутнього правила |
| Переформульована вимога | Потрібно сформулювати |
| — спостережуваний вихід | Потрібно визначити |
| — критерій | Потрібно визначити |
| — приклад порушення | Додати конкретний текст |
| Гіпотеза правки | Записати до правки |
| Очікуване зрушення метрики | Додати метрику, виміряний baseline і очікуване значення |

Якщо причина в коді інструмента, обрати інший кейс для аудиту тексту. Очікуване зрушення не є виміряним результатом правки.

## 7. Вартість повного прогону

| Що | Значення | Звідки |
|---|---|---|
| Кількість викликів моделі | Нижня межа й фактична кількість ще не отримані | Формула та блок вартості власного прогону |
| Середня довжина виклику, токенів | Не отримано | Консоль провайдера; окремо input/output та агент/суддя |
| Прайс | Не перевірено | Фактичні моделі, джерело й дата прайсу |
| Ціна одного повного прогону | Не розраховано | Власні токени, виклики та прайс |
| Ціна за місяць при частоті CI | Не розраховано | Частота з §5 × дні × ціна відповідного набору |

Навчальна оцінка: `виклики × середні токени на виклик × прайс за токен`.

Для різних цін input/output: `вартість = Σ моделей (input_tokens × price_in + output_tokens × price_out) / 1 000 000`, якщо прайс задано за 1M токенів. Включити агента й суддю. Нижню межу викликів не підміняти фактичною кількістю. Типові ціни зі скрипта не видавати за перевірений прайс; оцінку звірити з консоллю провайдера.





