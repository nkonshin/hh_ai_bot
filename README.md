# hh-mcp-server

MCP-сервер для API hh.ru, который позволяет Claude искать вакансии, оценивать их релевантность, генерировать персонализированные сопроводительные письма и откликаться на подходящие позиции.

Работает в связке с [hh-applicant-tool](https://github.com/s3rgeym/hh-applicant-tool), который берёт на себя рутину: поднятие резюме по крону и обновление OAuth-токенов.

## Возможности

| Инструмент | Описание |
|---|---|
| `search_vacancies` | Поиск вакансий с фильтрами (регион, зарплата, опыт, график, тип занятости) |
| `get_vacancy` | Подробная информация о вакансии (описание, навыки, условия) |
| `get_my_resumes` | Список резюме текущего пользователя |
| `get_similar_vacancies` | Вакансии, похожие на указанное резюме |
| `apply_to_vacancy` | Отклик на вакансию с сопроводительным письмом |
| `get_negotiations` | Список текущих откликов и их статусы |

## Быстрый старт

### Установка

```bash
git clone https://github.com/nkonshin/hh_ai_bot.git
cd hh_ai_bot
pip install -e .
```

### Настройка токена

**Вариант 1** — через hh-applicant-tool (рекомендуется):

```bash
pip install hh-applicant-tool
hh-applicant-tool auth
```

Сервер автоматически прочитает токен из `~/.config/hh-applicant-tool/config.json`.

**Вариант 2** — через переменную окружения:

```bash
export HH_ACCESS_TOKEN=your_token_here
```

### Запуск

```bash
hh-mcp-server
```

Или напрямую:

```bash
python -m hh_mcp_server.server
```

## Подключение к Claude

### Claude Desktop

Добавить в `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hh-job-search": {
      "command": "hh-mcp-server"
    }
  }
}
```

Если токен передаётся через переменную окружения:

```json
{
  "mcpServers": {
    "hh-job-search": {
      "command": "hh-mcp-server",
      "env": {
        "HH_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add hh-job-search hh-mcp-server
```

## Пример использования

После подключения можно общаться с Claude естественным языком:

> Посмотри новые вакансии по Python backend в Москве с зарплатой от 300к, откликнись на подходящие

Claude сам вызовет нужные инструменты: получит резюме, найдёт вакансии, прочитает каждую, оценит релевантность, напишет персональное сопроводительное письмо и отправит отклик.

## Ограничения API hh.ru

- На вакансии типа `direct` (с внешним URL отклика) откликнуться через API нельзя
- На вакансии с обязательным тестом откликнуться через API нельзя
- Есть rate-лимиты на запросы
- Токены истекают через ~2 недели (hh-applicant-tool обновляет их автоматически)

## Разработка

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Структура проекта

```
src/hh_mcp_server/
  config.py      — загрузка токена (env или hh-applicant-tool)
  hh_client.py   — async HTTP-клиент для API hh.ru
  server.py      — MCP-сервер с инструментами (FastMCP)
```

## Лицензия

MIT
