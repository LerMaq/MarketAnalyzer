Запустить локально:
``` bash
uvicorn main:app --reload
```

Закрыть, если завис:
``` bash
taskkill /F /IM python.exe
```

Шаблон .env:
```
DB_USER=postgres
DB_PASS=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
```