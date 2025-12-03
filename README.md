# code-reviewer

Простой агент на Python, который загружает Pull Request из GitHub и отправляет его в GigaChat для краткого code-review.

## Подготовка

1. Установите зависимости:
```
pip install -r requirements.txt
```
2. Задайте переменные окружения:
- `GITHUB_TOKEN` — токен с правом чтения PR.
- `GITHUB_REPO` — репозиторий в формате `owner/name`.
- `GIGACHAT_TOKEN` — токен доступа к GigaChat.
- Необязательно: `GIGACHAT_API_URL` (по умолчанию `https://gigachat.devices.sberbank.ru/api/v1`), `GIGACHAT_MODEL`.

## Запуск

Отправить PR на ревью:
```
python main.py <pr_number>
```

Параметры можно передавать флагами вместо переменных окружения:
```
python main.py --repo owner/name --github-token ... --gigachat-token ... 123
```

Для отладки используйте `-v`, чтобы увидеть запросы.
