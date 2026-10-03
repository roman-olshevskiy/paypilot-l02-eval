# Quality Bar Proposal — PayPilot, стадія Seed

Автор: Roman Olshevskyi. Дата створення чернетки: 2026-10-03.
Мандат: **Ship it**.

Пропозиція набору метрик і порогів для обговорення з CTO.

**Статус: чернетка.** Розділ 0 (R1–R3 і SWIFT-доказ) перенесено з L01. Результати L02 (§1–7) ще потрібно додати. Вимоги R1–R3 є навчальною пропозицією; їхня редакція v1.1 не перевірена на живому стенді. Документ ще не готовий до здачі.

## Паспорт даних

| Поле | Значення |
|---|---|
| Скрипт | `l02_eval.py` |
| Профілі й кількість прогонів | План: `clean` × 2, `lesson-02` × 3; фактично ще не виконано |
| Модель судді (JUDGE_MODEL) | Налаштовано `claude-haiku-4-5` (Anthropic); фактичне використання підтвердити звітом прогону |
| Дата прогону | Прогін ще не виконано |
| CLOCK_OVERRIDE | `2026-09-15T10:00:00Z`; перевірено через API стенду 2026-10-03; підтвердити у звіті прогону |
| Сирі звіти | Ще не отримано; додати точні шляхи `reports/*.json` |

Усі baseline, дельти, trade-off та вартість мають походити з власного прогону. Планова кількість прогонів не є результатом вимірювання.

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

Заповнити після аналізу власного прогону й triage кейсів.

| Шар | Тип збою | Метрика | Знаменник | Чому саме вона |
|---|---|---|---|---|
| Генерація | Потрібно визначити | Потрібно визначити | Потрібно визначити | Потрібно обґрунтувати |
| Генерація | Потрібно визначити | Потрібно визначити | Потрібно визначити | Потрібно обґрунтувати |
| Дія | Потрібно визначити | Потрібно визначити | Потрібно визначити | Потрібно обґрунтувати |
| Пошук | Потрібно визначити | Потрібно визначити | Потрібно визначити | Покриття шару пошуку — L04; конкретизувати метрику |
| Генерація | Потрібно визначити | Hallucination rate | Потрібно визначити | Повний курований еталон — L03; у L02 порівняти метрики на трьох кейсах |

Baseline, дельти й докази false confidence / false positive: ще не отримано. Напрямок шкали hallucination перевірити у встановленій версії.

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


