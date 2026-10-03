# ДЗ №1 — Quality Bar Proposal

Навігація для перевірки: [артефакти ДЗ №1](HOMEWORK-01-README.md). Здача — через гілку roman-olshevskyi/labs.

Автор: Roman Olshevskyi. Основний документ: [quality-bar-proposal.md](quality-bar-proposal.md).
Числа отримано власним прогоном 2026-10-03: clean ×2 і lesson-02 ×3, 13 кейсів, 65 відповідей.
Суддя: Anthropic claude-haiku-4-5; CLOCK_OVERRIDE=2026-09-15T10:00:00Z.
Сирий звіт: [reports/l02-clean-lesson-02-20261003-202039.json](reports/l02-clean-lesson-02-20261003-202039.json).
Походження й SHA256 використаних файлів: [run manifest](reports/run-manifest-20261003.json).
Domain: clean 24/24, lesson-02 12/36; оцінка вартості ≈USD0.94 збігається з записаними показниками білінгу.
Evidence pass означає успішний збір доказів, а не правильність відповіді. R1–R3 та гіпотеза §6 ще не перевірені після правки.

## Відтворення нашого прогону

Потрібні Docker, окремий локальний PayPilot stand з live-провайдером Anthropic і каталог stand поруч із цим репозиторієм.
Створіть локальний .env із .env.example; задайте STAND_DIR=../paypilot-stand,
EVAL_STAND_URL=http://host.docker.internal:8000, JUDGE_MODEL=claude-haiku-4-5,
CLOCK_OVERRIDE=2026-09-15T10:00:00Z і ключ Anthropic. Ключ агента також налаштуйте локально на stand.
.env і ключі не входять до комплекту.

З кореня цього репозиторію:

~~~powershell
docker compose build eval
docker compose run --rm -T eval --profiles clean,lesson-02 --runs 3 --baseline-runs 2 --dry-run
docker compose run --rm -T eval --profiles clean,lesson-02 --runs 3 --baseline-runs 2
~~~

Runner послідовно перемикає глобальні профілі, скидає дані й установлює clock; наприкінці залишає lesson-02.
Не запускайте інші набори паралельно на тому самому стенді. Live-прогін витрачає API-токени; нові відповіді й scores можуть відрізнятися.
Усі звернення до стенду в нашій роботі виконуються через реальні тести або eval-runner.

Для відтворення read-only аудиту §6 **після повного eval**, коли stand має lesson-02:

~~~powershell
docker compose run --rm -T --entrypoint python eval -m unittest discover -s tests -p test_l02_audit_evidence.py -v
~~~

Аудит використовує історичний request_id зі збереженого прогону. На новій БД цього trace може не бути; тоді
перевіряйте архівований evidence/l02-audit/C-01-run3.trace.json, а новий кейс потребує нового request_id.
Оригінальний тест не гарантує відтворення історичного trace на іншому стенді.

## Комплект для перевірки

- quality-bar-proposal.md — розділи 0–7.
- reports/ — сирий eval JSON, журнали та окремо позначені похідні розрахунки.
- cases.json, l02_eval.py, requirements.txt, Dockerfile, docker-compose.yml — файли відтворення.
- evidence/ — переносні докази L01 SWIFT і аудит L02.
- case-review.md, run-summary.md — пояснення відбору та прогону.

Повні документи L01 лишаються у paypilot-stand і до архіву цього ДЗ не включені.
Нижче збережено загальну інструкцію вихідного навчального репозиторію; параметри саме нашого прогону наведено вище.

---

# L02 · Скрипт метрик

Три текстові метрики DeepEval (faithfulness, answer relevancy, hallucination
rate) поруч із доменною коректністю, яку рахують рушії стенду PayPilot.
Скрипт до заняття L02 курсу з тестування LLM-агентів.

Python локально не потрібен: скрипт запускається в Docker. Усе для
лабораторної береш звідси одним `git clone`, окремо нічого завантажувати не
треба.

## Що зробити, коротко

Корінь курсу завжди `~/paypilot`: стенд у `~/paypilot/paypilot-stand`, цей репозиторій — у
`~/paypilot/l02` (папка уроку; наступні уроки лягають поруч: `l03`, …).

1. Підняти локальний стенд: у `~/paypilot/paypilot-stand` — `docker compose up -d --build`, потім `docker compose exec stand python scripts/doctor.py`.
2. Склонувати цей репозиторій поруч зі стендом:
   `git clone https://github.com/sergeytkachenko/paypilot-l02-eval.git ~/paypilot/l02`
3. `cd ~/paypilot/l02`, `cp .env.example .env`, вписати в `.env`
   ключ судді (`STAND_DIR` за замовчуванням уже `../paypilot-stand`).
4. `docker compose build` — один раз.
5. `docker compose run --rm eval --runs 3 --baseline-runs 2 --dry-run`, потім
   те саме без `--dry-run`.

Деталі кожного кроку нижче.

## Що в репозиторії

| Файл | Що це |
|---|---|
| `complaints.md` | двадцять скарг C-01…C-20 — вхідний матеріал кроку 1 |
| `triage.md` | дошка кроку 1: бот як новий співробітник підтримки і три купки для скарг — не знайшов, сказав не те, застосував не так |
| `l02_eval.py` | скрипт: шле кейси боту, рахує метрики, друкує звіт |
| `cases.json` | 13 кейсів зі скарг: запит, оракул, перевірка, метрики, контекст |
| `requirements.txt` | залежності, ставляться в образ |
| `Dockerfile`, `docker-compose.yml` | образ і запуск |
| `.env.example` | шаблон `.env`: шлях до стенду і ключ судді |

## Що потрібно

- Docker Desktop (macOS, Windows) або Docker Engine з compose (Linux).
- Піднятий **локальний** стенд `~/paypilot/paypilot-stand` (`docker compose up -d --build`, перевірка — `docker compose exec stand python scripts/doctor.py`)
  на `http://localhost:8000`. Скрипт перемикає профілі, скидає базу й ставить
  годинник, тому на спільному стенді його не запускай.
- Каталог стенду на цьому ж комп'ютері: скрипт імпортує з нього рушії
  (`app/engines`). Клонуй цей репозиторій у `~/paypilot/l02`, поруч зі стендом:
  тоді `STAND_DIR` за замовчуванням (`../paypilot-stand`) уже правильний.

## Запуск

```bash
mkdir -p ~/paypilot
git clone https://github.com/sergeytkachenko/paypilot-l02-eval.git ~/paypilot/l02
cd ~/paypilot/l02
cp .env.example .env        # впиши STAND_DIR і ключ судді
docker compose build        # один раз, близько хвилини

# план і кількість викликів, нічого не викликає
docker compose run --rm eval --runs 3 --baseline-runs 2 --dry-run

# повний прогін: clean двічі, lesson-02 тричі; ≈6 хв, ≈$1 на Haiku 4.5
docker compose run --rm eval --runs 3 --baseline-runs 2
```

Команди однакові для macOS, Linux і Windows (PowerShell). Усе після `eval` —
прапорці скрипта. Звіт друкується в термінал, сирі дані лягають у
`reports/*.json` у цьому каталозі. Щоб зберегти й звіт, додай `-T` і `tee`:

```bash
mkdir -p reports
docker compose run --rm -T eval --runs 3 --baseline-runs 2 2>&1 | tee reports/full-run.txt
```

`l02_eval.py` і `cases.json` підмонтовані в контейнер, тож правки в них
діють одразу, без перезбирання. `docker compose build` потрібен лише після
зміни `requirements.txt` або `Dockerfile`.

## `.env`

| Змінна | Що це |
|---|---|
| `STAND_DIR` | шлях до каталогу `paypilot-stand`, за замовчуванням `../paypilot-stand`. Windows: `C:/paypilot/paypilot-stand` |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | ключ судді, той самий, що в `.env` стенду; якщо задано кілька ключів, береться Anthropic, потім OpenAI, потім Gemini |
| `GEMINI_API_KEY` | ключ Google AI Studio, якщо суддею буде Gemini. Якщо образ зібраний до появи Gemini, після `git pull` один раз виконай `docker compose build` |
| `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN` | для стенду через OpenRouter: `https://openrouter.ai/api` і той самий ключ |
| `JUDGE_MODEL` | суддя, за замовчуванням `claude-haiku-4-5`, `gpt-4.1-mini` або `gemini-3.5-flash-lite` |
| `EVAL_STAND_URL` | адреса стенду зсередини контейнера, див. нижче |
| `STAND_PORT`, `STAND_PROFILE` | окремий стенд: порт на `127.0.0.1` (за замовчуванням `8010`) і стартовий профіль (`lesson-02`) |
| `AGENT_PRICE_IN`, `AGENT_PRICE_OUT` | ціна агента, USD за 1M токенів, для рядка вартості |

## Адреса стенду

Усередині контейнера `localhost` — це сам контейнер, а не твій комп'ютер.
Тому сервіс `eval` ходить на стенд через `http://host.docker.internal:8000`.
Стенд на іншому порту — задай `EVAL_STAND_URL` у `.env`, наприклад
`http://host.docker.internal:8010`.

Linux, стенд опублікований лише на `127.0.0.1`: `host.docker.internal`
туди не дістане. Бери сервіс `eval-host`, він працює в мережі хоста:

```bash
EVAL_STAND_URL=http://127.0.0.1:8010 docker compose run --rm eval-host --runs 3 --baseline-runs 2
```

## Окремий стенд

Якщо `localhost:8000` зайнятий спільним стендом (як на devhub), не чіпай
його: `docker compose up` у `paypilot-stand` перестворить спільний контейнер. Підніми окремий стенд із
цього ж `docker-compose.yml`. Сервіс `stand` збирається з каталогу
`STAND_DIR`, бере його `.env` і слухає лише `127.0.0.1:8010`:

```bash
docker compose up -d --build stand   # профіль lesson-02
curl -s http://127.0.0.1:8010/health
```

У `.env` цього репозиторію додай `EVAL_STAND_URL=http://stand:8000`:
сервіс `eval` дістає стенд за іменем, бо обидва в одному compose. Команди
запуску ті самі, з `eval`. Після прогону прибери стенд:

```bash
docker compose --profile stand down
```

## Корисні прапорці

| Прапорець | Що робить |
|---|---|
| `--profiles clean,lesson-02` | профілі по черзі; перший — baseline |
| `--runs 3` / `--baseline-runs 2` | прогони профілю заняття / прогони `clean` |
| `--only C-03,C-04` | лише ці кейси |
| `--metrics domain` | лише доменна коректність: без судді; live-генерація агента витрачає токени |
| `--workers 4` | паралельні кейси; при rate limit зменш |
| `--dry-run` | план і кількість викликів, нічого не викликає |
