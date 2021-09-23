from approxeng.task.menu import MenuTask, MenuAction
from time import sleep


class TriangulaMenuClass(MenuTask):

    # noinspection PyMethodMayBeStatic
    def get_menu_action(self, world):
        # Get any buttons pressed since last check
        buttons_pressed = world.joystick.presses

        if 'dleft' in buttons_pressed:
            return MenuAction.previous
        elif 'dright' in buttons_pressed:
            return MenuAction.next
        elif 'dup' in buttons_pressed:
            return MenuAction.up
        elif 'cross' in buttons_pressed:
            return MenuAction.select

    # noinspection PyMethodMayBeStatic
    def display_menu(self, world, title, item_title, item_index, item_count):
        # Push information to the display
        sleep(0.1)
        world.display.text = [f'{title} {item_index + 1} / {item_count}', item_title]
