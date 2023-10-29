import time
import asyncio
import curses
from random import randint, choice
from os import listdir
from os.path import join
from itertools import cycle
from curses_tools import draw_frame, read_controls


TIC_TIMEOUT = 0.1
STARS_SYMBOLS = '*.:+'


class Position:
    def __init__(self, raw, col, max_raw, max_col) -> None:
        self.raw = raw
        self.col = col
        self.max_raw = max_raw
        self.max_col = max_col

    def move(self, delta_raw, delta_col):
        new_raw = self.raw + delta_raw
        if self.max_raw > new_raw > 0:
            self.raw = new_raw
        new_col = self.col + delta_col
        if self.max_col > new_col > 0:
            self.col = new_col


class StarShip:
    rocket_path = './media/star_ship'

    def __init__(self, canvas, raw: int = 1, col: int = 1) -> None:
        star_shim_files = sorted(listdir(self.rocket_path))
        star_ship_animations = []
        heght, width = curses.window.getmaxyx(canvas)
        max_raw, max_col = heght - 1, width - 1
        for file in star_shim_files:
            with open(
                join(self.rocket_path, file),
                'r', encoding='utf-8'
            ) as file:
                shot = ''
                line = file.readline()
                lines_count = 0
                while line:
                    lines_count += 1
                    shot = shot + line
                    max_col = min(max_col, width - len(line) + 1)
                    line = file.readline()
                max_raw = min(max_raw, heght - lines_count)
                star_ship_animations.append(shot)
        self.star_ship_animation = cycle(star_ship_animations)
        self.canvas = canvas
        self.prev_animation = None
        self.position = Position(raw, col, max_raw, max_col)

    def draw(self):
        if self.prev_animation:
            draw_frame(
                self.canvas,
                self.position.raw,
                self.position.col,
                self.prev_animation,
                True
            )
        delta_raw, delta_col, _ = read_controls(self.canvas)
        self.position.move(delta_raw*10, delta_col*10)
        self.prev_animation = next(self.star_ship_animation)
        draw_frame(
            self.canvas,
            self.position.raw,
            self.position.col,
            self.prev_animation,
        )


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*', initial_sleep=0):
    for _ in range(initial_sleep):
        await asyncio.sleep(0)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


def draw(canvas):
    canvas.border()
    canvas.nodelay(True)

    star_ship = StarShip(canvas)

    stars_count = 100
    max_raw, max_column = curses.window.getmaxyx(canvas)
    coroutines = [
        blink(
            canvas,
            randint(1, max_raw-2),
            randint(1, max_column-2),
            choice(STARS_SYMBOLS),
            randint(0, 20)
        )
        for _ in range(stars_count)
    ]
    coroutines.append(fire(canvas, 5, 5))
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        star_ship.draw()
        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


def main():
    curses.update_lines_cols()
    curses.wrapper(draw)
    curses.curs_set(False)


if __name__ == '__main__':
    main()
