class Grid:
    grid_index_limit = 0
    def __init__(self, size, row, col):
        self.size = size
        self.row = row
        self.col = col
        self.units = [["." for _ in range(size)] for _ in range(size)]

    def create_unit(self, unit):
        faction, x, y = unit
        if self.units[x][y] == ".":
            if faction == "A":
                unit_object = AirUnit(x,y, self)
            elif faction == "F":
                unit_object = FireUnit(x,y, self)
            elif faction == "E":
                unit_object = EarthUnit(x,y, self)
            elif faction == "W":
                unit_object = WaterUnit(x,y, self)
            self.units[x][y] = unit_object
            unit_object.grid = self

    def has_airunit(self):
        for row in self.units:
            for unit in row:
                if isinstance(unit, AirUnit):
                    return True
        return False

    def add_unit(self, unit, x, y):
        occupier = self.units[x][y]
        if occupier == ".":
            self.units[x][y] = unit
            unit.x, unit.y = x, y
            unit.grid = self
        elif isinstance(occupier,AirUnit):
            occupier.health = min(occupier.health + unit.health, 14)
            occupier.attack_power += unit.attack_power

    def remove_unit(self, unit):
        self.units[unit.x][unit.y] = "."
        return unit



class AirUnit:
    def __init__(self, x, y, grid):
        """
        Initialize an Air unit with its position and attributes.
        :param x: The x-coordinate of the unit's position.
        :param y: The y-coordinate of the unit's position.
        """
        self.grid = grid
        self.x = x
        self.y = y
        self.health = 14  # Initial health
        self.attack_power = 3  # Base attack power
        self.healing_rate = 2  # Health restored when skipping an attack

        def heal(self):
            self.health = min(self.health + self.healing_rate, 14)  # Maximum health is 14

        def take_damage(self, damage):
            """
            Reduce the unit's health based on incoming damage.
            :param damage: The amount of damage to apply.
            """
            self.health -= damage
            if self.health <= 0:
                self.health = 0


class FireUnit:
    def __init__(self, x, y, grid):
        self.grid = grid
        self.x = x
        self.y = y
        self.health = 12  # Initial health
        self.attack_power = 4  # Base attack power
        self.healing_rate = 1  # Health restored when skipping an attack

        def heal(self):
            self.health = min(self.health + self.healing_rate, 12)  # Maximum health is 10

        def take_damage(self, damage):
            self.health -= damage
            if self.health <= 0:
                self.health = 0  # Ensure health does not go below zero

        def is_alive(self):
            return self.health > 0


class EarthUnit:
    def __init__(self, x, y, grid):
        self.grid =grid
        self.x = x
        self.y = y
        self.health = 18  # Initial health
        self.attack_power = 2  # Base attack power
        self.healing_rate = 3  # Health restored when skipping an attack

        def heal(self):
            self.health = min(self.health + self.healing_rate, 18)  # Maximum health is 10

        def take_damage(self, damage):
            self.health -= damage
            if self.health <= 0:
                self.health = 0  # Ensure health does not go below zero

        def is_alive(self):
            return self.health > 0


class WaterUnit:
    def __init__(self, x, y, grid):
        self.grid = grid
        self.x = x
        self.y = y
        self.health = 14  # Initial health
        self.attack_power = 3  # Base attack power
        self.healing_rate = 2  # Health restored when skipping an attack

        def heal(self):
            self.health = min(self.health + self.healing_rate, 14)  # Maximum health is 10

        def take_damage(self, damage):
            self.health -= damage
            if self.health <= 0:
                self.health = 0  # Ensure health does not go below zero

        def is_alive(self):
            return self.health > 0
