# Bitbucket code-review agent

Агент на Python3, который находит все открытые Pull Request в Bitbucket, отправляет дифф каждого PR в GigaChat и публикует комментарий с коротким code review.

## Подготовка

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Задайте переменные окружения:
   - `BITBUCKET_REPO` или `BITBUCKET_REPO_URL` — URL репозитория в Bitbucket или slug вида `workspace/repo`.
   - `BITBUCKET_USERNAME` — имя пользователя (используется с app password).
   - `BITBUCKET_TOKEN` — app password для Bitbucket.
   - `GIGACHAT_TOKEN` — токен доступа к GigaChat.
   - Необязательно: `BITBUCKET_API_URL` (по умолчанию `https://api.bitbucket.org/2.0`), `GIGACHAT_API_URL`, `GIGACHAT_MODEL`.

## Запуск

Отправить все открытые PR на ревью и добавить комментарии:
```bash
python main.py --repo-url https://bitbucket.org/<workspace>/<repo> --bitbucket-username <user> --bitbucket-token <app_password> --gigachat-token <token>
```

Параметры можно передавать флагами либо через переменные окружения. Добавьте `-v` для отладки запросов.
