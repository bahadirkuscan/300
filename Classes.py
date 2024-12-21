class Grid:
    grid_index_limit = 0
    def _init_(self, size, row, col):
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
            return True
        return False

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
    attack_pattern = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]
    max_health = 10

    def _init_(self, x, y, grid):
        self.skip = True
        self.grid = grid
        self.x = x
        self.y = y
        self.health = 10  # Initial health
        self.attack_power = 2  # Base attack power
        self.healing_rate = 2  # Health restored when skipping an attack

    def heal(self):
        self.health = min(self.health + self.healing_rate, AirUnit.max_health)  # Maximum health is 10

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0

    def target_coordinates(self):
        result_queue =[]
        for [i, j] in AirUnit.attack_pattern:
            result_queue.append([self.x+i, self.y+j, i, j])
        return result_queue
class FireUnit:
    attack_pattern = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]

    def _init_(self, x, y, grid):
        self.skip = True
        self.inferno_applied = False
        self.grid = grid
        self.x = x
        self.y = y
        self.health = 12  # Initial health
        self.max_health = 12
        self.attack_power = 4  # Base attack power
        self.healing_rate = 1  # Health restored when skipping an attack

    def heal(self):
        self.health = min(self.health + self.healing_rate, self.max_health)  # Maximum health is 12

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0  # Ensure health does not go below zero

    def is_alive(self):
        return self.health > 0

    def inferno(self):
        if self.inferno_applied or self.skip:
            return
        self.attack_power = max(self.attack_power + 1, 6) # max attack power is 6
        self.inferno_applied = True

    def target_coordinates(self):
        result_queue =[]
        for [i, j] in FireUnit.attack_pattern:
            result_queue.append([self.x+i, self.y+j, i, j])
        return result_queue
class EarthUnit:
    attack_pattern = [[-1, 0], [0, -1], [0, 1], [1, 0]]


    def _init_(self, x, y, grid):
        self.skip = True
        self.grid =grid
        self.x = x
        self.y = y
        self.health = 18  # Initial health
        self.max_health = 18
        self.attack_power = 2  # Base attack power
        self.healing_rate = 3  # Health restored when skipping an attack

    def heal(self):
        self.health = min(self.health + self.healing_rate, self.max_health)  # Maximum health is 10

    def take_damage(self, damage):
        self.health -= damage // 2
        if self.health <= 0:
            self.health = 0

    def is_alive(self):
        return self.health > 0

    def target_coordinates(self):
        result_queue =[]
        for [i, j] in EarthUnit.attack_pattern:
            result_queue.append([self.x+i, self.y+j, i, j])
        return result_queue
class WaterUnit:
    attack_pattern = [[-1, -1], [-1, 1], [1, -1], [1, 1]]


    def _init_(self, x, y, grid):
        self.skip = True
        self.grid = grid
        self.x = x
        self.y = y
        self.health = 14  # Initial health
        self.max_health = 14
        self.attack_power = 3  # Base attack power
        self.healing_rate = 2  # Health restored when skipping an attack

    def heal(self):
        self.health = min(self.health + self.healing_rate, self.max_health)  # Maximum health is 10

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.health = 0  # Ensure health does not go below zero

    def is_alive(self):
        return self.health > 0

    def target_coordinates(self):
        result_queue = []
        for [i, j] in WaterUnit.attack_pattern:
            result_queue.append([self.x + i, self.y + j, i, j])
        return result_queue
