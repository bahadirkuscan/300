# Import the MPI module from the mpi4py library
import math
import Classes
from mpi4py import MPI

# Initialize the communicator, which is the default communication group
comm = MPI.COMM_WORLD

# Get the total number of processes in the communicator
n_ranks = comm.Get_size()

# Get the rank (unique ID) of the current process in the communicator
rank = comm.Get_rank()
wave_count = 0
round_count = 0


# Gets absolute coordinates of a cell and returns the rank of its processor and relative coordinates
def get_sub_grid_coordinates(x, y, sub_grid_size):
    x_relative = x % sub_grid_size
    y_relative = y % sub_grid_size
    row = x // sub_grid_size
    col = y // sub_grid_size
    rank = row * math.sqrt(n_ranks - 1) // 1 + col + 1
    return rank, x_relative, y_relative


# gets relative rank of a processor given relative addresses
def get_target_rank_offset(new_x, new_y):
    row_diff = new_x // sub_grid_size
    col_diff = new_y // sub_grid_size
    if col_diff == -1 and rank % math.sqrt(n_ranks - 1) == 1:
        return None
    if col_diff == 1 and rank % math.sqrt(n_ranks - 1) == 0:
        return None
    if row_diff == -1 and rank <= math.sqrt(n_ranks - 1):
        return None
    if row_diff == 1 and rank > n_ranks - math.sqrt(n_ranks):
        return None
    return row_diff * math.sqrt(n_ranks - 1) + col_diff


# Parses a wave input
def parse_units(lines):
    units = [[] * n_ranks]
    for i in range(4):
        line = lines[i]
        line = line.split(":")
        positions = line[1].split(",")
        for j in range(unit_count):
            x, y = map(int, positions[j].split())
            target_rank, x_relative, y_relative = get_sub_grid_coordinates(x, y, sub_grid_size)
            units[target_rank].append((line[0], x_relative, y_relative))
    return units


# returns the rank of a processor using its row and col number. Not absolute coordinates
def get_rank(row, col):
    return row * Classes.Grid.grid_index_limit + col + 1


# Returns number of targets can be shot by an imaginary air unit deployed in a specific coordinate using a big_grid
def get_targets_airunit(big_grid, row, col):
    target_number = 0
    for [x, y] in Classes.AirUnit.attack_pattern:
        # There is nothing to shoot outside of grid + we can't shoot our allies
        if big_grid[row + x][col + y] == "X" or isinstance(big_grid[row + x][col + y], Classes.AirUnit):
            continue
        # If the cell is neutral look at the cell after it, it should not be neutral, an ally or outside of the main grid
        elif big_grid[row + x][col + y] == ".":
            if big_grid[row + 2 * x][col + 2 * y] != "." and \
                    not isinstance(big_grid[row + 2 * x][col + 2 * y], Classes.AirUnit) and \
                    not big_grid[row + 2 * x][col + 2 * y] == "X":
                target_number += 1
        else:
            target_number += 1
    return target_number


# Gets a big_grid and for each air unit in the middle section returns a movement_queue
def air_unit_movement(big_grid):
    n = len(big_grid) // 3
    result_array = []
    # Only look at the middle region
    for row_count in range(n, 2 * n):
        for col_count in range(n, 2 * n):
            # For each air unit
            if isinstance(big_grid[row_count][col_count], Classes.AirUnit):
                # Get target number for each possible movement
                max_targets = 0
                # new x and new y will be represented
                new_x, new_y = row_count, col_count
                for [x, y] in [[0, 0], [-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]:
                    # You can only move to neutral cells and other air units
                    if big_grid[row_count + x][col_count + y] == "." or isinstance(
                            big_grid[row_count + x][col_count + y], Classes.AirUnit):
                        target_number = get_targets_airunit(big_grid, row_count + x, col_count + y)
                        if target_number > max_targets:
                            max_targets = target_number
                            # New x and new y are the coordinates in big_grid
                            new_x, new_y = row_count + x, col_count + y
                result_array.append([row_count - n, col_count - n, new_x - n, new_y - n])
    return result_array


if rank == 0:
    # Initialize
    file = open('input.txt', 'r')
    line = file.readline()
    # The size of main grid = N
    main_grid_size, wave_count, unit_count, round_count = map(int, line.split())
    # Calculate size of each grid
    sub_grid_size = main_grid_size // math.sqrt(n_ranks - 1)
    Classes.Grid.grid_index_limit = main_grid_size // sub_grid_size
    for rank in range(1, n_ranks):
        # Send the sub-grid size to workers and wait for them to initialize sub-grids
        comm.send(sub_grid_size, rank)
    for rank in range(1, n_ranks):
        comm.recv(source=rank)

    for wave_number in range(wave_count):
        # Get the coordinates of each unit and put them in an array
        line = file.readline()
        lines = []
        for i in range(4):
            line = file.readline()
            lines.append(line)
        units = parse_units(lines)

        # Send each array to corresponding processor
        for i in range(1, n_ranks):
            comm.send(units[i], i)

        # Wait for all the workers to place the new units
        for rank in range(1, n_ranks):
            comm.recv(source=rank)

        for round_number in range(round_count):

            # MOVEMENT PHASE
            # Start with even-even coords and end with odd-odd coords
            for a, b in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                signal_count = 0
                for row in range(a, Classes.Grid.grid_index_limit, 2):
                    for col in range(b, Classes.Grid.grid_index_limit, 2):
                        comm.send("proceed", get_rank(row, col))
                        signal_count += 1
                for _ in range(signal_count):
                    comm.recv()

            for i in range(1, n_ranks):
                comm.send("finish", i)

            # After finishing calculating phase of movement phase now we need to apply those movements
            # First every worker will process its own queue
            for _ in range(n_ranks - 1):
                comm.recv()
            # Once every worker is finished with their own queue signal all the workers to continue
            for i in range(1, n_ranks):
                comm.send("queue finished", i)

            # After that each worker will process requests from other workers
            for _ in range(n_ranks - 1):
                comm.recv()
            # Once each request is finished the current phase is also finished
            for i in range(1, n_ranks):
                comm.send("phase finished", i)

            # ACTION PHASE
            # Start with even-even coords and end with odd-odd coords
            for a, b in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                signal_count = 0
                for row in range(a, Classes.Grid.grid_index_limit, 2):
                    for col in range(b, Classes.Grid.grid_index_limit, 2):
                        comm.send("proceed", get_rank(row, col))
                        signal_count += 1
                for _ in range(signal_count):
                    comm.recv()

            for i in range(1, n_ranks):
                comm.send("decisions finished", i)

            # RESOLUTION PHASE
            # Start with even-even coords and end with odd-odd coords
            for a, b in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                signal_count = 0
                for row in range(a, Classes.Grid.grid_index_limit, 2):
                    for col in range(b, Classes.Grid.grid_index_limit, 2):
                        comm.send("proceed", get_rank(row, col))
                        signal_count += 1
                for _ in range(signal_count):
                    comm.recv()

            for i in range(1, n_ranks):
                comm.send("phase finished", i)

            # HEALING PHASE
            # Start with even-even coords and end with odd-odd coords
            for a, b in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                signal_count = 0
                for row in range(a, Classes.Grid.grid_index_limit, 2):
                    for col in range(b, Classes.Grid.grid_index_limit, 2):
                        comm.send("proceed", get_rank(row, col))
                        signal_count += 1
                for _ in range(signal_count):
                    comm.recv()
            for i in range(1, n_ranks):
                comm.send("phase finished", i)














else:
    # Wait for the manager to calculate sub-grid size
    sub_grid_size = comm.recv(source=0)
    row, col = rank // Classes.Grid.grid_index_limit, rank % Classes.Grid.grid_index_limit
    grid = Classes.Grid(sub_grid_size, row, col)
    comm.send(grid, dest=0)
    for wave_number in range(wave_count):
        units = comm.recv(source=0)
        for unit in units:
            grid.create_unit(unit)
        comm.send(dest=0)

        for round_number in range(round_count):
            movement_queue = []
            # MOVEMENT PHASE
            while True:
                # First wait for starting signal
                status = MPI.Status()
                signal = comm.recv(status=status)
                if signal == "proceed":
                    if not grid.has_airunit():
                        # If we don't have an air unit we are done in movement phase
                        comm.send("completed", dest=0)
                    else:
                        # If we do then get your neighbours' data to build a bigger grid
                        big_grid = [["X" for _ in range(3 * sub_grid_size)] for _ in range(3 * sub_grid_size)]

                        # First put your own grid inside it
                        for i in range(sub_grid_size):
                            for j in range(sub_grid_size):
                                big_grid[sub_grid_size + i][sub_grid_size + j] = grid.units[i][j]

                        # Then go to neighbours and put their data inside of it
                        for [x, y] in [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]:
                            # Invalid cells will remain as "X"
                            if 0 <= row + x < Classes.Grid.grid_index_limit and 0 <= col + y < Classes.Grid.grid_index_limit:
                                comm.send("send data", dest=get_rank(row + x, col + y))
                                new_grid = comm.recv(source=get_rank(row + x, col + y))
                                # Now put the new grid inside big grid
                                for i in range(sub_grid_size):
                                    for j in range(sub_grid_size):
                                        big_grid[(x + 1) * sub_grid_size + i][(y + 1) * sub_grid_size + j] = \
                                            new_grid.units[i][j]

                        movement_queue = air_unit_movement(big_grid)
                        comm.send("completed", dest=0)

                elif signal == "send data":
                    comm.send(grid.units, dest=status.Get_source())

                elif signal == "finish":
                    break

            # Applying movements of movement phase
            # First of all handle your own queue and send necessary signals to other workers
            for x, y, new_x, new_y in movement_queue:
                target_rank = rank + get_target_rank_offset(new_x, new_y)
                if target_rank == rank:
                    grid.add_unit(grid.remove_unit(grid.units[x][y]), new_x, new_y)
                else:
                    comm.send((grid.remove_unit(grid.units[x][y]), new_x % sub_grid_size, new_y % sub_grid_size),
                              dest=target_rank)
            comm.send("finished queue", dest=0)

            # Now handle signals came from other processors
            while True:
                status = MPI.Status()
                signal = comm.recv(status=status)
                if status.Get_source() == 0:
                    comm.send("phase finished", dest=0)
                    break
                else:
                    grid.add_unit(signal[0], signal[1], signal[2])

            # Wait for every other processor is done with current phase
            comm.recv(source=0)  # wait for "phase finished"

            # ATTACK PHASE

            # First we need to fetch the attackers
            attackers = []
            while True:
                status = MPI.Status()
                signal = comm.recv(status=status)
                if signal == "proceed":
                    for row in grid.units:
                        for unit in row:
                            if unit == ".":
                                continue
                            elif unit.health < unit.max_health // 2:
                                unit.skip = True
                            else:
                                relative_coordinates = unit.target_coordinates()
                                for [rel_x, rel_y] in relative_coordinates:
                                    # Get the rank offset for relative coordinates
                                    rank_offset = get_target_rank_offset(rel_x, rel_y)
                                    # If target coordinates in our grid check whether valid target exists or not
                                    if rank_offset is None:
                                        continue
                                    if rank_offset == 0 and grid.units[rel_x][rel_y] != "." and type(unit) != type(
                                            grid.units[rel_x][rel_y]):
                                        attackers.append(unit)
                                        unit.skip = False
                                        break
                                    elif rank_offset != 0:
                                        # If the target rank is another process request information of unit type
                                        comm.send((rel_x % sub_grid_size, rel_y % sub_grid_size), dest=rank + rank_offset)
                                        unit_type = comm.recv(dest=rank + rank_offset)
                                        if unit_type == type(unit) or unit_type == type("."):
                                            continue
                                        else:
                                            attackers.append(unit)
                                            unit.skip = False
                                            break
                                    else:
                                        continue

                    comm.send("finished", dest=0)

                elif signal == "decisions finished":
                    break
                else:
                    # Handle data request from another process
                    (x, y) = signal
                    comm.send(type(grid.units[x][y]), status.Get_source())

            # RESOLUTION PHASE

            # First deal the damages without killing anyone
            while True:
                status = MPI.Status()
                signal = comm.recv(status=status)
                # If proceed deal damage
                if signal == "proceed":
                    for attacker in attackers:
                        relative_coordinates = attacker.target_coordinates()
                        for [rel_x, rel_y] in relative_coordinates:
                            rank_offset = get_target_rank_offset(rel_x, rel_y)
                            # If target processor is invalid continue
                            if rank_offset is None:
                                continue
                            # If target coordinates in our grid check whether valid target exists or not
                            if rank_offset == 0 and grid.units[rel_x][rel_y] != "." and type(attacker) != type(
                                    grid.units[rel_x][rel_y]):
                                grid.units[rel_x][rel_y].take_damage(attacker.attack_power)
                            # If the target is not in our grid send a message to target processor
                            elif rank_offset != 0:
                                comm.send((rel_x % sub_grid_size, rel_y % sub_grid_size, attacker.attack_power,
                                           type(attacker)), dest=rank + rank_offset)
                            else:
                                continue
                    comm.send("finished", dest=0)
                elif signal == "phase finished":
                    break
                else:
                    (x, y, damage, attacker_type) = signal
                    if attacker_type == type(grid.units[x][y]) or grid.units[x][y] == ".":
                        continue
                    else:
                        grid.units[x][y].take_damage(damage)

            # HEALING PHASE
            # Bury the dead ones, heal the alive skippers
            while True:
                status = MPI.Status()
                signal = comm.recv(status=status)
                # If proceed start burying dead ones
                if signal == "proceed":
                    for row in grid.units:
                        for unit in row:
                            # If no dead unit continue
                            if unit == ".":
                                continue
                            if unit.is_alive():
                                if unit.skip:
                                    unit.heal()
                                continue
                            # If current unit is dead and not a fire unit look at neighbours and detect fire units
                            if not isinstance(unit, Classes.FireUnit):
                                for [i, j] in Classes.FireUnit.attack_pattern:
                                    rel_x, rel_y = unit.x + i, unit.y + j
                                    rank_offset = get_target_rank_offset(rel_x, rel_y)
                                    if rank_offset is None:
                                        continue
                                    elif rank_offset == 0:
                                        if isinstance(grid.units[rel_x][rel_y], Classes.FireUnit):
                                            grid.units[rel_x][rel_y].inferno()
                                    else:
                                        comm.send((rel_x % sub_grid_size, rel_y % sub_grid_size), dest=rank + rank_offset)
                            grid.remove_unit(unit)

                elif signal == "phase finished":
                    break
                else:
                    (x, y) = signal
                    if isinstance(grid.units[x][y], Classes.FireUnit):
                        grid.units[x][y].inferno()

            # Reset round-temporary information
            for row in grid.units:
                for unit in row:
                    if unit == ".":
                        continue
                    unit.skip = True
                    if isinstance(unit, Classes.FireUnit):
                        unit.inferno_applied = False

