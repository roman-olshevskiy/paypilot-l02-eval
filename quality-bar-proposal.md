# Quality Bar Proposal — PayPilot, стадія Seed

Автор: Roman Olshevskyi. Дата створення чернетки: 2026-10-03.
Мандат: **Ship it**.

Пропозиція набору метрик і порогів для обговорення з CTO.

**Статус: чернетка.** Розділ 0 (R1–R3 і SWIFT-доказ) перенесено з L01. Власний прогін L02 виконано; §1–6 заповнено, §7 ще потрібно завершити. Вимоги R1–R3 є навчальною пропозицією; їхня редакція v1.1 не перевірена на живому стенді. Документ ще не готовий до здачі.

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

**Мандат: Ship it.** Пропонується випускати функцію лише після усунення підтверджених критичних помилок у рахунках, цінах та eligibility. Мандат дозволяє прийняти задокументований ризик менш критичних текстових недоліків, але не дозволяє повідомляти клієнту хибні фінансові умови. Це пропозиція критеріїв, не реалізована конфігурація CI.

| Метрика | Поріг | Обґрунтування через бізнес-вплив |
|---|---|---|
| Domain correctness, критичні кейси | 100% перевірок; жодної підтверджено хибної відповіді у критичних кейсах | Неправильний баланс, спред або строк спору впливає на рішення клієнта й створює претензії. Середнє не повинно приховувати одиничний критичний збій. Для цього набору — усі 12 case-specific checks на кожному повторі; автоматичний pass доповнити перевіркою змісту на відомих слабких checks |
| Faithfulness | ≥0.8 на відповідь як поріг направлення на перевірку; підтверджений критичний збій блокує незалежно від score | На перевіреній зіставній вибірці ловить 2/12 хибних, але зупиняє 1/12 правильних. Це допоміжний сигнал: гейт лише за faithfulness пропустить 10/12 доменних помилок. Менший поріг пропускає більше, більший збільшує втрати прийнятних відповідей (§3) |
| Answer relevancy | ≥0.8 на відповідь, нижче — перевірка, не автоматичне оголошення дефекту | Клієнт має отримати відповідь на запит; загальні пояснення замість суті збільшують повторні звернення. Межа 0.8 — початкова пропозиція: на повному clean-наборі нижче неї 1/26 відповідей (C-10/run1), яка справді не пояснює eligibility. Окремої оптимізації цього порога не виконано |
| Hallucination rate, C-03/C-04/C-08 | 0 для прийняття без додаткового розбору; >0 — перевірка суперечностей, підтверджена критична суперечність блокує | Незалежний еталон має захищати від хибних строків і тарифів при зеленій faithfulness. На clean 1/6 оцінок >0 (C-08/run2), тому автоматично прирівнювати ненульову оцінку до критичного дефекту не можна |
| Context recall / precision | Поріг ще не встановлено: оцінювання L04 | Немає потрібної retrieval-розмітки; вигаданий поріг не захистить клієнта від відсутнього чи обрізаного правила. Ризик відкладеного покриття має бути явно прийнятий, а не оголошений закритим |

Висновок для поточного lesson-02: критерій domain correctness не пройдено — 12/36, тобто 24 хибні відповіді. Підвищення faithfulness-порога не виправляє їх. Ця конфігурація не відповідає запропонованому quality bar навіть під Ship it. Результат clean 24/24 не означає готовності всієї системи: C-10 і C-08 показують межі числових/regex перевірок.

За мандату **Zero regulatory risk** domain correctness залишилася б 100% без винятків, а текстові контрольні пороги стали б жорсткішими: faithfulness ≥0.9, relevancy ≥0.9, hallucination rate=0; записи нижче межі вимагали б розбору до релізу, без прийняття нерозв’язаних критичних ризиків. Додатково потрібні обов’язкові перевірки provenance, account binding, write actions, нерозкриття внутрішніх критеріїв та повніше retrieval-покриття. Це збільшить ручний розбір і затримки; faithfulness=1 все одно не гарантує істинності. Назва мандату не є доказом нульового регуляторного ризику.

## 3. Trade-off у цифрах

Метрика: **faithfulness**. Джерело: [власний JSON](reports/l02-clean-lesson-02-20261003-202039.json). Похідні мітки, критерії й request IDs: [tradeoff-analysis-20261003.json](reports/tradeoff-analysis-20261003.json).

Правило зупинки: **score < поріг**; score, рівний порогу, проходить. Вибірка визначена ретроспективно після читання повних відповідей, не зареєстрована до прогону; результат описує цей набір, не узагальнену точність гейта.

Використано однаковий зіставний набір кейсів C-03/C-04/C-06/C-09/C-11/C-12: явні правила eligibility, tier, balance і monthly limit. На clean обидва повтори кожного — 12 перевірених правильних відповідей за відповідним критерієм. У lesson-02 C-03/C-04/C-06/C-12 хибні у трьох повторах — 12 перевірених хибних; C-09/C-11 правильні й не входять до знаменника хибних.

Мітки встановлено за змістом і незалежними facts, а не за faithfulness: C-03 — expired; C-04 — tier2 0.9%; C-06 — USD ACC-1003 і 5200.75; C-09 — EUR964666; C-11 — 120 днів; C-12 — 60 днів із відповідним deadline. C-06 lesson-02 не просто не називає баланс: явно заперечує існування наявного рахунку, тому хибність підтверджена повним текстом.

C-02 не має faithfulness. C-01/C-05/C-07 не включені до цієї зіставної вибірки (публічний тариф/розгорнута конвертація); C-08 має сумнівні пояснення allowance, C-10 — непідтверджені обіцянки й неповну відповідь, C-19 — слабкий продуктовий regex. Їх не оголошуємо правильними лише через clean/domain pass. Вони залишаються у повному запуску; вибірка для trade-off не змінює baseline §1.

| Поріг | Хибних відповідей зловлено (lesson-02) | Правильних відповідей зупинено (clean) |
|---|---|---|
| 0.7 | 1 із 12 | 0 із 12 |
| 0.8 | 2 із 12 | 1 із 12 |
| 0.9 | 6 із 12 | 4 із 12 |

**Обрано 0.8 як допоміжний поріг розбору під Ship it.** Порівняно з 0.7, ловимо ще одну хибну відповідь (2 замість 1) ціною однієї додатково зупиненої правильної (1 замість 0). Перехід до 0.9 ловить ще чотири хибні (6 замість 2), але зупиняє ще три правильні (4 замість 1). Без незалежного domain gate цей компроміс недостатній: при 0.8 десять із дванадцяти хибних відповідей проходять. Критичні domain failures блокуються окремо.

При 0.8 зупиняються хибні C-04 lesson-02/run2 (0.6) і run3 (0.75); правильна C-04 clean/run1 (0.778) також зупиняється. При 0.9 правильні C-03 clean/run1 (0.833), C-04 clean/run1 (0.778), C-04 clean/run2 (0.875), C-12 clean/run1 (0.8) потребують розбору. Рівно 0.9 у C-12 clean/run2 проходить.

Для зіставлення з консольним автоматичним підрахунком на повному наборі: faithfulness ловить 9/24, 11/24, 17/24 domain failures на 0.7/0.8/0.9; flag на clean — 2/24, 3/24, 11/24. Це **flags серед усіх clean із faithfulness**, а не кількість підтверджено правильних зупинених відповідей: зокрема C-10 не є валідним false-positive доказом. Основна таблиця використовує тільки перевірені мітки.

Рішення не спирається на середній score. Повтори одного кейса не є незалежними production-подіями; 12/12 у вибірках не дають надійної оцінки майбутньої частоти. Пороги слід повторно перевірити на Golden Dataset L03; числової моделі ціни ручного розбору наразі немає, тому не стверджуємо економічну оптимальність 0.8.

## 4. Межі набору

Рішення нижче — пропозиція для поточного мандату Ship it, а не підтвердження, що ризики усунено. Джерело: аналіз повних відповідей і [case-review.md](case-review.md).

| Клас збою | Чому не ловиться | Ризик | Рішення |
|---|---|---|---|
| Неповний або неправильний retrieval, зокрема обрізаний чанк D16 | Немає релевантнісної розмітки й retrieval-метрик; C-13/C-14 відкладено. Faithfulness може погодитися з хибним контекстом | Високий: клієнт отримує неправильне правило при зеленій текстовій метриці | Відкладено вимірювання до L04; не оголошувати retrieval закритим. Критичні доменні висновки звіряти з незалежними правилами |
| Непідтверджений продукт / ненадійне походження джерела | Hallucination покриває лише C-03/C-04/C-08; C-19 має вузький not_regex, не повний approved-source verdict | Високий: обіцянка неіснуючих ставок або умов. D03 не активний у lesson-02 | Курований набір і чіткий критерій — L03, provenance — окрема перевірка джерел. До підтвердження продукту — unavailable fallback; виконання цього правила ще потрібно тестувати |
| Некоректна write action, account binding, escalation або витік compliance review | Domain check переважно читає текст; відсутність affirmative pattern не доводить відсутності create_dispute. Список tools без повних arguments/results недостатній | Високий: дія проти відмови eligibility, неправильний рахунок або розкриття внутрішньої інформації | Потрібні тести tool calls і side effects; деталізація трасування — L08. Не приймати критичний невідомий результат на основі green regex |
| Помилкове пояснення при правильній фінальній сумі | number check знаходить очікуване число будь-де, не перевіряє всі твердження. C-08 clean має сумнівні пояснення allowance при правильному total | Середній/високий: клієнт робить хибний висновок про майбутню ціну | Додати розмітку компонентів і пояснення в L03; до цього ручний розбір сумнівних відповідей. Не зараховувати їх у verified-correct cohort |
| Втрата пам’яті багатокрокової розмови | Одноходові кейси; C-18 не включено | Середній: повторні запити й неправильне застосування збережених деталей | Відкладено до L05; не поширювати висновки цього набору на multi-turn |
| Непідтверджений строк контакту, тон і повнота відповіді | Немає SLA/тональної рубрики; no_offer пропускає C-10, хоча відповідь обіцяє контакт і не пояснює відмову | Середній: очікування, повторні звернення, втрата довіри | Додати окремі критерії в L03; поки розбирати C-10 вручну та не називати його false positive |
| Частота збоїв у production, latency під навантаженням, атаки | 13 навчальних кейсів, 5 повторів профілів; відсутні репрезентативна вибірка, навантажувальні й adversarial сценарії | Невизначений, потенційно високий: зелений набір не прогнозує всі реальні збої | Прийнято лише обмежений висновок про цей набір; latency/tracing — L08, атакувальні перевірки — L06; production-частоту тут не оцінюємо |

Неприйнятний критичний збій не стає прийнятним через позначку «відкладено». Релізний висновок потребує окремого рішення про межі функції, fallback і незакриті ризики. Повний набір метрик поки не забезпечує універсальної оцінки якості.

## 5. Розклад прогонів

Це пропозиція розкладу: CI та автоматизації зараз не створено. Будь-яка взаємодія зі стендом виконується через реальний запуск тестів або l02_eval.py, без ручних API-запитів. Глобальні профілі/reset/clock потребують ізольованого стенду й послідовних запусків наборів; не запускати C# та Python eval одночасно на одному стенді.

| Частота | Що входить | Критерій поділу | Ціна |
|---|---|---|---|
| Кожен merge (блокує) | Наявні Python tests/test_engines.py і tests/test_api.py на mock-провайдері та окремій тестовій БД; арифметика FX/SWIFT, allowance, ліміти, вікна/hold, API/trace contract | Детерміновані, швидкі перевірки критичних правил та інтерфейсу. Падіння блокує merge; це не перевірка живої LLM-поведінки | API-виклики моделей: USD0; час CI/інфраструктура тут не виміряні |
| Nightly | l02_eval.py: clean ×2, 13 кейсів, domain + faithfulness/relevancy + hallucination для трьох curated кейсів; розбір records нижче §2 порогів | Жива модель і суддя стохастичні; потрібні повтори, але повний LLM-набір на кожен merge надто дорогий. Новий підтверджений критичний збій зупиняє реліз; score-only flag іде на розбір | При аналогічних токенах: ≈USD0.372558 за 26 відповідей; 30 nightly ≈USD11.176740. Прайс/білінг ще не перевірені |
| Перед релізом | Повний l02_eval.py: clean ×2 + lesson-02 ×3; звірка критичних clean-відповідей та контроль того, що ін’єкції створюють очікувані domain failures. Додатково — наявний explicit C# clean SWIFT quality-тест і цільові сценарії змінених вимог після їх реалізації | Найширше покриття та перевірка здатності набору помічати відомі збої перед зміною, яку побачать клієнти. lesson-02 — навмисно дефектний контроль, не кандидат на production-профіль | Виміряна база eval: ≈USD0.940113 за 65 відповідей. Додаткові C# / нові сценарії мають окрему, ще не виміряну ціну; повна релізна ціна = база + вони |

Запуски з відповідних коренів репозиторіїв:

```powershell
# paypilot-stand: окрема CI-сесія, mock-перевірка модулів правил та API
$env:LLM_PROVIDER = 'mock'
$env:PROFILE = 'clean'
$env:DEFECTS = ''
$env:CLOCK_OVERRIDE = '2026-09-15T10:00:00Z'
python -m pytest tests/test_engines.py tests/test_api.py

# paypilot-l02-eval: nightly, live
# Ключ і JUDGE_MODEL беруться з локального .env
docker compose run --rm -T eval --profiles clean --runs 1 --baseline-runs 2

# paypilot-l02-eval: контроль перед релізом, live
docker compose run --rm -T eval --profiles clean,lesson-02 --runs 3 --baseline-runs 2

# paypilot-stand: додатковий explicit quality-тест, live
dotnet test .\tests\PayPilot.ApiTests\PayPilot.ApiTests.csproj --filter "FullyQualifiedName~Clean_Swift_ContainsPublishedFeeComponents" --logger "console;verbosity=detailed"
```

tests/conftest.py створює окрему тимчасову БД, але задає mock/profile/clock через setdefault, тому успадковані змінні не перезаписуються. Наведена команда явно встановлює ці значення в окремій CI-сесії; при реалізації CI перевірити передумови. Evidence-тести C# не використовувати як семантичний quality gate: зелений evidence означає збір captures, не правильність відповіді. Навчальний explicit тест на D03 має очікуваний дефект і потребує окремої інтерпретації.

Розрахунок із сирого JSON: clean — 128368 input, 5994 output токенів, agent estimate USD0.158338 + judge SDK estimate USD0.214220 = USD0.372558; lesson-02 — USD0.224725 + USD0.342830 = USD0.567555; повна база — USD0.940113. [Похідний розрахунок](reports/schedule-cost-analysis-20261003.json).

**Усі USD-ціни — оцінки, не підтверджені списання.** Для агента використано типовий прайс скрипта USD1 input / USD5 output за 1M, суддя — оцінку SDK. Nightly-ціна отримана з фактичних clean-записів повного прогону, не з окремого нового nightly-запуску. Ціна майбутнього прогону змінюється разом із токенами, моделлю й прайсом; її уточнення та звірка з білінгом — §7. 30 днів — планове припущення, кількість релізів ще не задана.

Критерій один: на merge — детерміноване, дешеве й критичне; на nightly — стохастичне з повтореннями; перед релізом — найширший набір і аналіз відкритих ризиків. Дешевий domain check у live eval не робить весь live-запуск детермінованим або безкоштовним: відповіді все одно генерує модель.

## 6. Локалізація одного червоного кейса

Кейс **C-01, lesson-02/run3**, request_id `9b404d6dfe0d4b30`. Червоні показники: faithfulness=0, domain=false; relevancy=1. У всіх трьох lesson-02 повторах C-01: faithfulness=0, domain=false. Це аудит текстового правила D05, а не спроба виправити runtime-реалізацію інструмента.

**Таймер аудиту:** 2026-10-03 23:56:21–23:57:43, Europe/Kiev (20:56:21–20:57:43 UTC), 1 хв 22 с. За цей інтервал обрано кейс, отримано докази тестом, прочитано рядок і сформовано гіпотезу; оформлення таблиці виконано після цього. У 15 хвилин вкладенося.

Актуальний промпт і трейс отримано реальним [Python unittest](tests/test_l02_audit_evidence.py), 1/1 passed: [журнал](reports/audit-evidence-tests-20261003.txt), [snapshot промпту](evidence/l02-audit/assembled-prompt.json), [трейс C-01/run3](evidence/l02-audit/C-01-run3.trace.json), [health](evidence/l02-audit/health.json). Тест зробив лише GET-запити; chat, reset, перемикання профілю й моделі не викликалися. Evidence pass підтверджує отримання узгоджених доказів, не правильність відповіді агента.

Промпт — поточний snapshot lesson-02, отриманий після eval; не називаємо його окремо збереженим історичним prompt input. Версія base.v1+D04+D05+D25 збігається з журналом eval; trace підтверджує lesson-02 та D05. У trace немає tool spans і є один llm.call. Історична модель агента в цьому trace: `claude-haiku-4-5-20251001`.

| Питання | Відповідь |
|---|---|
| Шар | Генерація / використання джерел: текстова інструкція забороняє пошук тарифу і вимагає конкретну цифру з пам’яті |
| Рядок специфікації | Цитата з §3 Sources of truth актуального assembled prompt наведена нижче; переноси рядків нормалізовано пробілами |
| Переформульована вимога | For standard fee questions, call search_knowledge_base before stating any tariff figure. State only the applicable components and formula supported by the retrieved tariff; do not replace a flat-plus-percentage tariff with a single flat fee. If the transfer amount or currency is missing, give the supported formula and ask for the missing input; do not assert a final total. If the tariff is unavailable or the tool fails, say verified pricing is unavailable and offer a verifiable next step. |
| — спостережуваний вихід | Tool call/arguments/results у trace; retrieved tariff; формула й компоненти фінальної відповіді; запит на відсутню суму/валюту або unavailable fallback |
| — критерій | Pass: search_knowledge_base викликано до тарифних цифр; для SWIFT джерело підтверджує EUR15 flat +0.3% EUR-еквівалента, і обидва компоненти наведено. Без суми/валюти нема вигаданого total. При відсутніх тарифних даних — unavailable без цифр. Порушення будь-якої умови — fail. Окремо читати answer/trace, не покладатися лише на наявність двох чисел у regex |
| — приклад порушення | Дослівна відповідь run3: `The SWIFT transfer fee at Verta is **€15**.` — без пошуку, без 0.3%, без уточнення суми |
| Гіпотеза правки | До будь-якої правки: замінити D05 §3 правилом обов’язкового отримання тарифу; узгодити §7 для тарифу без суми, щоб D25 округлення total не застосовувалося до тарифної формули. Тарифні компоненти не округляти й не підміняти total. Спершу тестувати на копії конфігурації, зберігши решту overlays; не змінювати політику інструментів або еталон |
| Очікуване зрушення метрики | C-01 lesson-02: faithfulness з 0/3 score=0 до ≥0.8 у 3/3; domain із 0/3 до 3/3. Додатковий acceptance: tariff retrieval у 3/3, обидва компоненти й коректні missing-input handling. Relevancy не нижче 0.8. Це цілі експерименту, не виміряне покращення |

Цитата «Було»:
~~~text
For standard fees, spreads and transfer rates, however, do NOT call the search tool and do not wait for a lookup: you are expected to know Verta's tariffs from experience and to answer fee questions instantly from memory with a specific number, so the customer is never left waiting.
~~~

Гіпотеза обмежена C-01. Інші доменні збої D19/D20 та account-routing D04 ця правка не усуває. D25 створює додатковий текстовий конфлікт, тому source rule і формат відповіді мають бути узгоджені в межах майбутнього експерименту. Для зміни ціни/latency потрібно виміряти додатковий пошук.

**Правку не впроваджено, before/after прогін не виконано.** Сирі eval-результати й активний промпт стенду не змінені. Наявний clean control із правильним тарифом показує еталонну поведінку, але не доводить ефект майбутньої правки. Повторна перевірка правки — лише через реальний запуск тестів.

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
