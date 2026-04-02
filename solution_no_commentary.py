import json
import os


class Coord:
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
            raise ValueError(f"{self.name[1:]} должна быть от {min_val} до {max_val}")
        setattr(instance, self.name, float(value))


class Destination:
    def __set_name__(self, owner, name):
        self.name = "_" + name

    def __get__(self, instance, owner):
        return getattr(instance, self.name, "")

    def __set__(self, instance, value):
        if not isinstance(value, str):
            raise TypeError('Адрес должен быть в формате "улица, дом"')
        if not value or "," not in value:
            raise TypeError('Адрес должен быть в формате "улица, дом"')
        setattr(instance, self.name, value)


class LogisticsCenter:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.warehouses = []
            self.total_deliveries = 0
            self._initialized = True

    def register_warehouse(self, warehouse):
        if warehouse not in self.warehouses:
            self.warehouses.append(warehouse)
            print(f"📦 Склад #{warehouse.warehouse_number} зарегистрирован в центре")

    def add_delivery(self):
        self.total_deliveries += 1

    def get_stats(self):
        return {
            "total_deliveries": self.total_deliveries,
            "warehouses_count": len(self.warehouses)
        }

    def __str__(self):
        return (f"🏢 Логистический центр | "
                f"Доставок: {self.total_deliveries} | "
                f"Складов: {len(self.warehouses)}")


class Warehouse:
    _instances = {}

    def __new__(cls, warehouse_number, address="Не указан", max_cargo=5):
        if warehouse_number not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[warehouse_number] = instance
        return cls._instances[warehouse_number]

    def __init__(self, warehouse_number, address="Не указан", max_cargo=5):
        if not hasattr(self, '_initialized'):
            self.warehouse_number = warehouse_number
            self.address = address
            self.max_cargo = max_cargo
            self._initialized = True
            center = LogisticsCenter()
            center.register_warehouse(self)

    def calculate_delivery_cost(self, weight, distance, rate=10):
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
        for num, inst in cls._instances.items():
            print(inst)


class FlightRecorder:
    lat = Coord()
    lon = Coord()
    destination = Destination()

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
        self._cargo_weight = 0.0
        self.__destination = ""
        self.warehouse = None
        self._center = LogisticsCenter()
        print(f"🚁 Борт {flight_id} | Пилот: {pilot}")

    def __del__(self):
        print(f"🗑 Борт {self.flight_id}: отключен")

    def __setattr__(self, name, value):
        if name == "max_altitude" and isinstance(value, (int, float)) and value < 0:
            value = 0
        if name == "_cargo_weight":
            if isinstance(value, (int, float)) and value > 5:
                print(f"⚠️ Перегруз! Вес {value} кг превышает лимит 5 кг. Установка заблокирована.")
                return
        super().__setattr__(name, value)

    def __getattr__(self, name):
        defaults = {"battery": 100, "flight_time": 0, "distance": 15}
        if name in defaults:
            return defaults[name]
        raise AttributeError(f"Нет атрибута {name}")

    def deliver(self):
        try:
            dist = self.distance
        except AttributeError:
            dist = "Нет данных"
        dest = self.destination
        if not dest:
            dest = self.__destination
        if not dest:
            dest = "Не указан"
        return (f"Груз: {self._cargo_weight} кг | "
                f"Пункт: {dest} | "
                f"Расстояние: {dist} км")

    @property
    def weight(self):
        return self._cargo_weight

    @weight.setter
    def weight(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("Вес должен быть числом")
        if value < 0:
            raise ValueError("Вес не может быть отрицательным")
        if value > 5:
            raise ValueError("❌ Максимальный вес груза: 5 кг")
        self._cargo_weight = value
        print(f"📦 Вес груза установлен: {value} кг")

    def __call__(self, weight=None, distance=None):
        if weight is not None and distance is not None:
            if self.warehouse is None:
                print("❌ Склад не привязан к дрону!")
                return False
            return self.warehouse.calculate_delivery_cost(weight, distance)
        return self._cargo_weight

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
        return self._waypoints.copy()

    def stats(self):
        if not self._waypoints:
            return {"points": 0, "max": 0, "avg": 0}
        alts = [p["alt"] for p in self._waypoints]
        return {
            "points": len(alts),
            "max": max(alts),
            "avg": round(sum(alts) / len(alts), 1)
        }

    def save(self, filename=None):
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


def main():
    print("=" * 60)
    print("   СИСТЕМА УПРАВЛЕНИЯ ДРОНАМИ ДОСТАВКИ «FastDelivery»")
    print("=" * 60)

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 1: ПРОВЕРКА SINGLETON")
    print("=" * 50)

    c1 = LogisticsCenter()
    c2 = LogisticsCenter()
    print(f"c1 is c2 = {c1 is c2}")
    print(c1)

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 2: ПРОВЕРКА MULTITON")
    print("=" * 50)

    w1 = Warehouse(1, "ул. Складская, 1")
    w2 = Warehouse(2, "ул. Промышленная, 5")
    w3 = Warehouse(1)
    print(f"w1 is w3 = {w1 is w3}")
    print(f"w1 is w2 = {w1 is w2}")
    Warehouse.show_all()

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 3: СОЗДАНИЕ ДРОНА")
    print("=" * 50)

    drone = FlightRecorder("LOG-001", "Елена")
    print(drone)

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 4: УСТАНОВКА ВЕСА (PROPERTY)")
    print("=" * 50)

    drone.weight = 3.5
    print(f"Текущий вес: {drone.weight} кг")

    try:
        drone.weight = 6
    except ValueError as e:
        print(f"Ошибка: {e}")

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 5: ПУНКТ НАЗНАЧЕНИЯ (ДЕСКРИПТОР)")
    print("=" * 50)

    drone.destination = "ул. Ленина, 10"
    print(f"Пункт назначения: {drone.destination}")

    try:
        drone.destination = "Неверный адрес"
    except TypeError as e:
        print(f"Ошибка: {e}")

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 6: ИНФОРМАЦИЯ О ДОСТАВКЕ")
    print("=" * 50)

    print(drone.deliver())

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 7: БЛОКИРОВКА ПЕРЕГРУЗА (__setattr__)")
    print("=" * 50)

    drone._cargo_weight = 10
    print(f"Вес после попытки: {drone._cargo_weight} кг")

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 8: РАСЧЁТ СТОИМОСТИ (__call__)")
    print("=" * 50)

    drone.warehouse = w1
    result = drone(3.5, 15)
    print(f"Результат: {result}")
    print(f"drone() = {drone()}")

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 9: СТАТИСТИКА ЦЕНТРА")
    print("=" * 50)

    print(c1.get_stats())

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 10: ЗАПИСЬ МАРШРУТА")
    print("=" * 50)

    drone.add_point(55.75, 37.62, 100)
    drone.add_point(55.80, 37.65, 150)
    drone.add_point(55.70, 37.58, 200)

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 11: УПРАВЛЕНИЕ ПОЛОСОЙ")
    print("=" * 50)

    route = drone.get_points()
    for i, pt in enumerate(route, 1):
        print(f"  Точка {i}: lat={pt['lat']}, lon={pt['lon']}, alt={pt['alt']}")
    print(f"Статистика: {drone.stats()}")

    print("\n" + "=" * 50)
    print("🔷 ТЕСТ 12: СОХРАНЕНИЕ И ЗАГРУЗКА")
    print("=" * 50)

    filename = drone.save()
    loaded = FlightRecorder.load(filename)
    if loaded:
        print(f"Загружен: {loaded}")

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
