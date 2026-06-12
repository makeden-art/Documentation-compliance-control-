# Documentation-compliance-control

Сервис **нормоконтроля** — отдельный контейнер платформы.

- Репозиторий: `git@github.com:makeden-art/Documentation-compliance-control-.git`
- Маршрут в портале: `/norm` (прокси с :8080)
- Порт контейнера: `8083`

```bash
docker compose -f ../docker-compose.platform.yml up -d norm-control
```
