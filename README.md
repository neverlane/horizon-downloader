# Скачивалка ресурсов для Horizon

Скачивает ресурсы Minecraft: Java Edition **только с официальных серверов Mojang** в папку `.minecraft`: клиентский JAR, JSON версии, индекс и все assets. Нужен Python 3.10+, сторонние пакеты не требуются.

## Запуск

```bash
cd /Users/egdvach/Projects/neverlane/horizon-downloader
python3 download.py
```

По умолчанию скачивается Minecraft **26.3** в стандартную папку игры. На macOS это `~/Library/Application Support/minecraft`.

После загрузки открой **Horizon → Play → Prepare**. Если Horizon не найдёт папку сам, нажми **Choose…** и укажи папку из строки `Destination` в терминале. Для подготовки Horizon также потребуется JDK 25 — лаунчер может скачать его сам.

## Опции

```bash
# Только проверить версию и узнать размер загрузки
python3 download.py --dry-run

# Другая версия
python3 download.py --version 1.21.10

# Другая папка
python3 download.py --dir "/полный/путь/к/.minecraft"

# Число одновременных загрузок
python3 download.py --jobs 12
```

Есть прогресс, повторные попытки, продолжение недокачанных файлов и проверка SHA-1. При повторном запуске уже скачанные файлы пропускаются.

Эта утилита не выполняет вход в Microsoft и не обходит лицензию Minecraft. Используй её со своей легально приобретённой копией игры.
