# Описание юнит-тестов для класса Scheduler

Юнит-тесты для класса Scheduler реализованы с использованием фреймворка `pytest` и библиотеки `unittest.mock` для изоляции от внешнего API.

Используется `unittest.mock` для мока HTTP-запросов к эндпоинту https://ofc-test-01.tspb.su/test-task/, что исключает зависимость от интернета.
Фикстура `mock_data` предоставляет тестовые данные, имитирующие реальный ответ API.

Запуск тестов:
```shell
  pytest -v
```
