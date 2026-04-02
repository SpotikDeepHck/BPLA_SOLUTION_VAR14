import json
import os


# =====================================================================
# УРОВЕНЬ 1: Базовый — дескриптор координат
# =====================================================================

class Coord:
    """Дескриптор для координат с проверкой диапазона."""

    def __set_name__(self, owner, name):
        self.name = "_" + name
        self.range = (-90, 90) if name == "lat" else (-180, 180)

    def __get__(self, instance, owner):
        return getattr(instance, self.name, 0)

    def __set__(self, instance, value):
        if not isinstance(value, (int, float)):
            raise TypeError("Координата должна быть числом")
        min_val, max_val = self.range
        if value < min_val or value > max_val:
            raise ValueError(
                f"{self.name[1:]} должна быть от {min_val} до {max_val}")
        setattr(instance, self.name, float(value))


# =====================================================================
# УРОВЕНЬ 2: Средний — дескриптор пункта назначения
# =====================================================================

class Destination:
    """Дескриптор для контроля пункта назначения."""

    def __set_name__(self, owner, name):
        self.name = "_" + name                          # → _destination

    def __get__(self, instance, owner):
        return getattr(instance, self.name, "")

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError('Адрес должен быть в формате "улица, дом"')
        if not value or "," not in value:
            raise TypeError('Адрес должен быть в формате "улица, дом"')
        setattr(instance, self.name, value)


# =====================================================================
# УРОВЕНЬ 3: Singleton — Логистический центр
# =====================================================================

class LogisticsCenter:
    """
    Единый диспетчерский центр — единственный экземпляр в системе.

    Паттерн Singleton:
    Сколько раз ни вызывай LogisticsCenter() — всегда получишь один объект.
    Инициализация происходит только один раз.
    Диспетчер хранит список всех активных складов.
    """

    _instance = None                       # ← ссылка на единственный экземпляр

    def __new__(cls, *args, **kwargs):
        # Если экземпляр ещё не создан — создаём.
        # Если уже есть — возвращаем существующий.
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Важно: __init__ вызывается каждый раз при обращении к классу!
        # Поэтому нужен флаг _initialized, чтобы инициализация прошла один раз.
        if not hasattr(self, '_initialized'):
            self.warehouses = []            # список зарегистрированных складов
            self.total_deliveries = 0       # количество выполненных доставок
            self._initialized = True

    def register_warehouse(self, warehouse):
        """Добавляет склад в список зарегистрированных."""
        if warehouse not in self.warehouses:
            self.warehouses.append(warehouse)
            print(f"📦 Склад #{warehouse.warehouse_number} "
                  f"зарегистрирован в центре")

    def add_delivery(self):
        """Увеличивает счётчик доставок."""
        self.total_deliveries += 1

    def get_stats(self):
        """Возвращает словарь со статистикой."""
        return {
            "total_deliveries": self.total_deliveries,
            "warehouses_count": len(self.warehouses)
        }

    def __str__(self):
        return (f"🏢 Логистический центр | "
                f"Доставок: {self.total_deliveries} | "
                f"Складов: {len(self.warehouses)}")


# =====================================================================
# УРОВЕНЬ 3: Multiton — Склад
# =====================================================================

class Warehouse:
    """
    Склад поддерживает логику: 1 уникальный номер = 1 объект.

    Паттерн Multiton:
    Первый вызов Warehouse(1) → создаёт новый объект.
    Второй вызов Warehouse(1) → возвращает существующий.
    Но Warehouse(2) создаст отдельный объект.
    """

    _instances = {}                        # {номер_склада: экземпляр}

    def __new__(cls, warehouse_number, address="Не указан", max_cargo=5):
        # Есть ли уже склад с таким номером?
        if warehouse_number not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[warehouse_number] = instance
        return cls._instances[warehouse_number]

    def __init__(self, warehouse_number, address="Не указан", max_cargo=5):
        # Важно: __init__ вызывается каждый раз при обращении к классу!
        # Поэтому нужна проверка, была ли уже инициализация.
        if not hasattr(self, '_initialized'):
            self.warehouse_number = warehouse_number
            self.address = address
            self.max_cargo = max_cargo
            self._initialized = True
            # Автоматическая регистрация в логистическом центре
            center = LogisticsCenter()
            center.register_warehouse(self)

    def calculate_delivery_cost(self, weight, distance, rate=10):
        """
        Расчёт стоимости доставки.
        Формула: вес × расстояние × тариф.
        """
        cost = weight * distance * rate
        center = LogisticsCenter()
        center.add_delivery()
        print(f"✅ Стоимость доставки: {cost} руб.")
        return cost

    def __str__(self):
        return (f"🏭 Склад #{self.warehouse_number} | "
                f"Адрес: {self.address} | Макс. груз: {self.max_cargo} кг")

    def __repr__(self):
        return f"Warehouse({self.warehouse_number})"

    @classmethod
    def show_all(cls):
        """Показать все созданные склады."""
        for num, inst in cls._instances.items():
            print(inst)


# =====================================================================
# ГЛАВНЫЙ КЛАСС: FlightRecorder (бортовой самописец дрона)
# =====================================================================

class FlightRecorder:
    """Бортовой самописец для одного полёта дрона."""

    # Дескрипторы уровня класса
    lat = Coord()
    lon = Coord()
    destination = Destination()            # УРОВЕНЬ 2: дескриптор пункта назначения

    def __new__(cls, *args, **kwargs):
        print("🆕 Создание нового экземпляра самописца")
        return super().__new__(cls)

    def __init__(self, flight_id, pilot):
        print("📋 Инициализация базовых параметров")
        self.flight_id = flight_id
        self.pilot = pilot
        self.__altitude = 0
        self.max_altitude = 500
        self._waypoints = []

        # УРОВЕНЬ 1: новые атрибуты для доставки
        self._cargo_weight = 0.0           # защищённый — вес груза (кг)
        self.__destination = ""            # приватный — пункт назначения

        # УРОВЕНЬ 3: привязка к складу и центру
        self.warehouse = None
        self._center = LogisticsCenter()

        print(f"🚁 Борт {flight_id} | Пилот: {pilot}")

    def __del__(self):
        print(f"🗑 Борт {self.flight_id}: отключен")

    # ==================================================================
    # УРОВЕНЬ 2: __setattr__ — контроль перегруза
    # ==================================================================
    def __setattr__(self, name, value):
        """Контроль значений при установке атрибутов."""
        # Контроль max_altitude — не может быть отрицательной
        if name == "max_altitude" and isinstance(value, (int, float)) and value < 0:
            value = 0

        # НОВОЕ: контроль перегруза
        if name == "_cargo_weight":
            if isinstance(value, (int, float)) and value > 5:
                print(f"⚠️ Перегруз! Вес {value} кг превышает лимит 5 кг. "
                      f"Установка заблокирована.")
                return                     # ← блокируем установку

        super().__setattr__(name, value)

    # ==================================================================
    # УРОВЕНЬ 1: __getattr__ — значения по умолчанию
    # ==================================================================
    def __getattr__(self, name):
        """Значения по умолчанию для отсутствующих атрибутов."""
        defaults = {"battery": 100, "flight_time": 0, "distance": 15}
        if name in defaults:
            return defaults[name]
        raise AttributeError(f"Нет атрибута {name}")

    # ==================================================================
    # УРОВЕНЬ 1: deliver() — информация о доставке
    # ==================================================================
    def deliver(self):
        """
        Собирает информацию о текущей доставке.
        Использует __getattr__ для получения distance.
        """
        try:
            dist = self.distance
        except AttributeError:
            dist = "Нет данных"

        # Приоритет: дескриптор destination → приватный __destination
        dest = self.destination
        if not dest:
            dest = self.__destination
        if not dest:
            dest = "Не указан"

        return (f"Груз: {self._cargo_weight} кг | "
                f"Пункт: {dest} | "
                f"Расстояние: {dist} км")

    # ==================================================================
    # УРОВЕНЬ 2: property weight — контроль веса
    # ==================================================================
    @property
    def weight(self):
        """Геттер: возвращает текущий вес груза."""
        return self._cargo_weight

    @weight.setter
    def weight(self, value):
        """Сеттер: проверяет, что вес не более 5 кг."""
        if not isinstance(value, (int, float)):
            raise TypeError("Вес должен быть числом")
        if value < 0:
            raise ValueError("Вес не может быть отрицательным")
        if value > 5:
            raise ValueError("❌ Максимальный вес груза: 5 кг")
        self._cargo_weight = value
        print(f"📦 Вес груза установлен: {value} кг")

    # ==================================================================
    # УРОВЕНЬ 3: __call__ — для удобного интерфейса
    # ==================================================================
    def __call__(self, weight=None, distance=None):
        """
        Если переданы weight и distance — расчёт стоимости через склад.
        Если без аргументов — текущий вес груза.
        """
        if weight is not None and distance is not None:
            if self.warehouse is None:
                print("❌ Склад не привязан к дрону!")
                return False
            return self.warehouse.calculate_delivery_cost(weight, distance)
        return self._cargo_weight

    # ==================================================================
    # Базовые методы (из исходного кода)
    # ==================================================================
    @property
    def altitude(self):
        return self.__altitude

    @altitude.setter
    def altitude(self, value):
        if value < 0:
            print("⚠️ Высота не может быть отрицательной, установлено 0")
            value = 0
        self.__altitude = value
        if value > self.max_altitude:
            self.max_altitude = value

    def add_point(self, lat, lon, alt):
        """Добавление точки маршрута."""
        self.lat = lat
        self.lon = lon
        self.altitude = alt
        self._waypoints.append({
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.__altitude
        })
        print(f"📍 Точка {len(self._waypoints)}: ({lat}, {lon}) (alt:{alt})")

    def get_points(self):
        """Доступ к точкам маршрута (копия)."""
        return self._waypoints.copy()

    def stats(self):
        """Статистика полёта."""
        if not self._waypoints:
            return {"points": 0, "max": 0, "avg": 0}
        alts = [p["alt"] for p in self._waypoints]
        return {
            "points": len(alts),
            "max": max(alts),
            "avg": round(sum(alts) / len(alts), 1)
        }

    def save(self, filename=None):
        """Сохранение данных рейса в JSON."""
        name = filename or f"{self.flight_id}.json"
        data = {
            "flight_id": self.flight_id,
            "pilot": self.pilot,
            "max_altitude": self.max_altitude,
            "cargo_weight": self._cargo_weight,
            "waypoints": self._waypoints
        }
        with open(name, "w") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Сохранено в {name} ({os.path.getsize(name)} байт)")
        return name

    @classmethod
    def load(cls, filename):
        """Загрузка данных рейса из JSON."""
        try:
            with open(filename) as f:
                data = json.load(f)
            flight = cls(data["flight_id"], data["pilot"])
            flight.max_altitude = data["max_altitude"]
            flight._cargo_weight = data.get("cargo_weight", 0)
            flight._waypoints = data["waypoints"]
            if flight._waypoints:
                flight.__altitude = flight._waypoints[-1]["alt"]
            return flight
        except FileNotFoundError:
            print(f"❌ Файл {filename} не найден")
            return None

    def __str__(self):
        return (f"🚁 Борт {self.flight_id} | "
                f"Пилот: {self.pilot} | "
                f"Груз: {self._cargo_weight} кг")


# =====================================================================
# Часть 3. Демонстрация работы всей системы
# =====================================================================

def main():
    print("=" * 60)
    print("   СИСТЕМА УПРАВЛЕНИЯ ДРОНАМИ ДОСТАВКИ «FastDelivery»")
    print("=" * 60)

    # ── ТЕСТ 1: Проверка Singleton ─────────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 1: ПРОВЕРКА SINGLETON")
    print("=" * 50)

    c1 = LogisticsCenter()
    c2 = LogisticsCenter()
    print(f"c1 is c2 = {c1 is c2}")                    # True
    print(c1)

    # ── ТЕСТ 2: Проверка Multiton ──────────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 2: ПРОВЕРКА MULTITON")
    print("=" * 50)

    w1 = Warehouse(1, "ул. Складская, 1")
    w2 = Warehouse(2, "ул. Промышленная, 5")
    w3 = Warehouse(1)                                   # тот же объект
    print(f"w1 is w3 = {w1 is w3}")                     # True
    print(f"w1 is w2 = {w1 is w2}")                     # False
    Warehouse.show_all()

    # ── ТЕСТ 3: Создание дрона ─────────────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 3: СОЗДАНИЕ ДРОНА")
    print("=" * 50)

    drone = FlightRecorder("LOG-001", "Елена")
    print(drone)

    # ── ТЕСТ 4: property weight ────────────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 4: УСТАНОВКА ВЕСА (PROPERTY)")
    print("=" * 50)

    drone.weight = 3.5
    print(f"Текущий вес: {drone.weight} кг")

    # Попытка перегруза через property
    try:
        drone.weight = 6
    except ValueError as e:
        print(f"Ошибка: {e}")

    # ── ТЕСТ 5: Дескриптор Destination ─────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 5: ПУНКТ НАЗНАЧЕНИЯ (ДЕСКРИПТОР)")
    print("=" * 50)

    drone.destination = "ул. Ленина, 10"
    print(f"Пункт назначения: {drone.destination}")

    # Неправильный формат
    try:
        drone.destination = "Неверный адрес"
    except TypeError as e:
        print(f"Ошибка: {e}")

    # ── ТЕСТ 6: deliver() ─────────────────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 6: ИНФОРМАЦИЯ О ДОСТАВКЕ")
    print("=" * 50)

    print(drone.deliver())

    # ── ТЕСТ 7: __setattr__ — блокировка перегруза ─────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 7: БЛОКИРОВКА ПЕРЕГРУЗА (__setattr__)")
    print("=" * 50)

    drone._cargo_weight = 10                            # блокируется
    print(f"Вес после попытки: {drone._cargo_weight} кг")

    # ── ТЕСТ 8: __call__ — расчёт стоимости ────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 8: РАСЧЁТ СТОИМОСТИ (__call__)")
    print("=" * 50)

    drone.warehouse = w1
    result = drone(3.5, 15)
    print(f"Результат: {result}")

    # Без аргументов — текущий вес
    print(f"drone() = {drone()}")

    # ── ТЕСТ 9: Статистика центра ──────────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 9: СТАТИСТИКА ЦЕНТРА")
    print("=" * 50)

    print(c1.get_stats())

    # ── ТЕСТ 10: Запись маршрута ───────────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 10: ЗАПИСЬ МАРШРУТА")
    print("=" * 50)

    drone.add_point(55.75, 37.62, 100)
    drone.add_point(55.80, 37.65, 150)
    drone.add_point(55.70, 37.58, 200)

    # ── ТЕСТ 11: Работа с полосами ─────────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 11: УПРАВЛЕНИЕ ПОЛОСОЙ")
    print("=" * 50)

    route = drone.get_points()
    for i, pt in enumerate(route, 1):
        print(f"  Точка {i}: lat={pt['lat']}, lon={pt['lon']}, alt={pt['alt']}")
    print(f"Статистика: {drone.stats()}")

    # ── ТЕСТ 12: Сохранение и загрузка ─────────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 12: СОХРАНЕНИЕ И ЗАГРУЗКА")
    print("=" * 50)

    filename = drone.save()
    loaded = FlightRecorder.load(filename)
    if loaded:
        print(f"Загружен: {loaded}")

    # ── ТЕСТ 13: Дополнительные возможности ────────────────────
    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 13: ДОПОЛНИТЕЛЬНЫЕ ВОЗМОЖНОСТИ")
    print("=" * 50)

    print(f"Статистика через __call__: {drone()}")
    print(f"Заряд батареи (c.__getattr__): {drone.battery}%")

    print("\n" + "=" * 60)
    print("   ✅ СИСТЕМА УСПЕШНО ПРОТЕСТИРОВАНА!")
    print("=" * 60)


if __name__ == "__main__":
    main()
