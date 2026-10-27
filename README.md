# Horizon Resource Downloader

Простая скачалка ресурсов Minecraft: Java Edition для [Horizon](https://playhorizon.dev/). Работает на **Windows, Linux и macOS** без сторонних пакетов.

- Загружает файлы только с официальных серверов Mojang.
- Скачивает клиент, assets и библиотеки для текущей ОС.
- Показывает прогресс, докачивает оборванные файлы и проверяет SHA-1.
- Пропускает уже существующие файлы при повторном запуске.

## Требования

- Python **3.10 или новее**: https://www.python.org/downloads/
- Для Windows при установке Python включи **Add Python to PATH**.
- Своя легально приобретённая копия Minecraft: Java Edition.

## Быстрый старт

Скачай репозиторий:

```bash
git clone https://github.com/neverlane/horizon-downloader.git
cd horizon-downloader
```

### Windows

Дважды нажми **`download.bat`** или выполни в PowerShell / CMD:

```bat
download.bat
```

По умолчанию файлы попадут в `%APPDATA%\.minecraft`.

### Linux

```bash
chmod +x download.sh
./download.sh
```

По умолчанию файлы попадут в `~/.minecraft`.

### macOS

```bash
chmod +x download.sh
./download.sh
```

По умолчанию файлы попадут в `~/Library/Application Support/minecraft`.

По умолчанию загружается **Minecraft 26.3**. После завершения открой **Horizon → Play → Prepare**. Если Horizon не найдёт игру сам, нажми **Choose…** и укажи папку из строки `Destination`. Для подготовки также нужен JDK 25 — лаунчер Horizon может скачать его сам.

## Опции

Опции одинаковые для всех ОС. В Windows используй `download.bat`, в Linux и macOS — `./download.sh`.

```bash
# Только проверить версию и узнать размер загрузки
./download.sh --dry-run

# Другая версия Minecraft
./download.sh --version 1.21.10

# Другая папка установки
./download.sh --dir "/полный/путь/к/.minecraft"

# Число одновременных загрузок (от 1 до 32)
./download.sh --jobs 12
```

Пример для Windows PowerShell с другой папкой:

```powershell
.\download.bat --dir "$env:APPDATA\.minecraft" --jobs 12
```

Можно запускать и напрямую: `python download.py` на Windows либо `python3 download.py` на Linux/macOS.

Эта утилита не выполняет вход в Microsoft и не обходит лицензию Minecraft.
