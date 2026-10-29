# MobileCraft Launcher

Лаунчер Minecraft: Java Edition для Android-телефона, написан на Java (без Kotlin и сторонних библиотек).

## Возможности

- **Выбор персонажа** — 8 встроенных персонажей (Стив, Алекс, Рыцарь, Шахтёр, Маг, Ниндзя, Фермер, Ледяная).
  Скины 64×64 генерируются прямо в приложении.
- **Выбор модели** — классическая (Steve, руки 4px) или тонкая (Alex, руки 3px). Превью сразу перерисовывается.
- **Свой скин** — загрузка PNG 64×64 или старого формата 64×32 из галереи/файлов.
- **Превью персонажа** — пиксельный рендер спереди и сзади (нажмите на персонажа, чтобы повернуть).
- **Выбор версии** — список версий с серверов Mojang (релизы / снапшоты / старые), кэш и офлайн-список.
- **Установка игры** — скачивание JSON версии, клиента, библиотек и ресурсов в `Android/data/com.mobilecraft.launcher/files/.minecraft`.
- **Офлайн-ник** и UUID, как у ванильного сервера; команда запуска сохраняется в `launch_command.txt`.

## Запуск самой игры

Java-версия Minecraft — это настольная программа: для её запуска на телефоне нужна JVM, собранная под Android,
и прослойка OpenGL → OpenGL ES (так работает PojavLauncher). Этот лаунчер готовит файлы и команду запуска,
а если на телефоне установлен PojavLauncher — кнопка «Запустить» открывает игру через него.

## Сборка APK

Готовый APK собирается автоматически в GitHub Actions при каждом пуше:
вкладка **Actions → Build APK → Artifacts → MobileCraftLauncher-debug**.

Локально (нужны JDK 17 и Android SDK):

```bash
./gradlew assembleDebug
# APK: app/build/outputs/apk/debug/app-debug.apk
```

## Структура

```
app/src/main/java/com/mobilecraft/launcher/
  MainActivity.java       главный экран: превью, ник, версия, «Играть»
  CharacterActivity.java  выбор персонажа и модели, импорт скина
  VersionActivity.java    выбор версии игры
  SkinView.java           отрисовка скина (classic/slim, 64×64 и 64×32)
  SkinGenerator.java      генерация скинов встроенных персонажей
  Character.java          список персонажей
  GameInstaller.java      загрузка версии, библиотек и ресурсов
  LaunchCommand.java      сборка команды запуска (офлайн-режим)
  GameVersion.java, Http.java, Prefs.java
```

Minecraft — торговая марка Mojang AB. Проект не связан с Mojang и Microsoft;
для игры нужна купленная копия Minecraft: Java Edition.
