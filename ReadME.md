# Zeekr Vehicle Integration для Home Assistant

Кастомная интеграция для чтения телеметрии автомобилей Zeekr через API официального приложения.

Репозиторий: https://github.com/Potia/ha_zeekr

## Возможности
- Авторизация по SMS на китайский номер (+86), токены в config entry
- 58 сенсоров + 17 бинарных сенсоров + device_tracker на автомобиль
- Опрос каждые 60 с, режим read-only (без удалённых команд)
- Русские статусы без эмодзи; координаты в градусах, без GPS — unknown

## Установка (HACS)
1. HACS → Интеграции → ⋮ → Пользовательские репозитории → `https://github.com/Potia/ha_zeekr` (тип: Integration)
2. Найти **Zeekr Vehicle Integration** → Установить → перезагрузить Home Assistant
3. Настройки → Устройства и службы → Интеграции → Добавить → Zeekr → телефон (+86…) → SMS-код

## Важно
- Используется неофициальный API Zeekr — он может измениться в любой момент
- Автор не связан с Zeekr/Geely; использование на свой риск
- Версия в `manifest.json` всегда совпадает с тегом GitHub

## Поддержка
Issues: https://github.com/Potia/ha_zeekr/issues
