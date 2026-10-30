# Block Royale — 3D-модели для королевской битвы

Оригинальный набор 3D-моделей в стиле «блочной» королевской битвы: оружие, персонажи с анимациями,
танк, сундуки, лут, постройки и природа. Скриптов игры здесь нет — только модели.

## Что внутри

| Категория | Модели | Анимации |
|---|---|---|
| **Персонажи** (`models/characters`) | Ranger (солдат), BoltRobot (робот), ShadowNinja (ниндзя), Astronaut (космонавтка) | Idle, Walk, Run, Jump, Crouch, Aim, Dance, Wave, Death (+ AntennaBlink, ScarfFlutter) |
| **Оружие** (`models/weapons`) | SMG_Uzi (компактный ПП), AssaultRifle, SniperRifle, PumpShotgun, Pistol, RocketLauncher, Grenade | Fire (отдача + вспышка), Reload, BoltCycle, PullPin |
| **Техника** (`models/vehicles`) | Tank | Drive, TurretRotate, Fire, HatchOpen |
| **Предметы и мир** (`models/props`) | Chest, ChestRare, AmmoBox, SupplyDrop, Medkit, Bandage, ShieldPotion, BuildWall, BuildFloor, BuildRamp, PineTree, OakTree, Rock, Bush | Open, Idle, Descend, Float, Build, Sway, Rustle |

* `models/**/*.glb` — glTF 2.0 с иерархией узлов и анимациями (Roblox Studio 3D Importer, Unity, Godot, Unreal, Blender, three.js).
* `models/obj/**` — статичные `.obj` + `.mtl` в позе покоя (для движков без поддержки glTF).
* `models/manifest.json` — список моделей, полигонов и анимаций.

Все модели проходят официальный Khronos glTF-Validator без ошибок и предупреждений.

## Соглашения

* Единицы — метры, ось Y вверх, «перед» модели смотрит в **+Z**.
* Персонажи: рост ~1.85 м, ноги на `y = 0`. Анимации вращают узлы-шарниры
  `Root > Hips > Spine > Neck / Shoulder_L/R > Elbow_L/R > Hand_L/R`, `Hip_L/R > Knee_L/R`.
  Оружие крепится к узлу `Hand_R`.
* Оружие: начало координат — у рукояти. Узел `Flash` — вспышка выстрела (в покое масштаб 0).
* Танк: `Turret` вращается по Y, `GunPivot` поднимает ствол, `Hatch` — люк.
* Сундук: крышка — узел `Lid` с петлёй сзади.

## Просмотр

```bash
python3 -m http.server 8000
# открыть http://localhost:8000/viewer/  (или ?m=Tank&a=Fire)
```

## Пересборка / правка моделей

Модели генерируются кодом из примитивов — меняйте размеры и цвета в `tools/assets_*.py`:

```bash
python3 tools/build.py
```

Зависимостей нет, нужен только Python 3.
