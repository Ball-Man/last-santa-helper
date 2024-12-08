"""Main game logic and user interactions."""
import desper
import pyglet
from pyglet.math import Vec2
from pyglet.sprite import Sprite

from . import physics


class Item:
    """Represents an in game item."""


@desper.event_handler('on_mouse_game_press')
class ItemDragManager(desper.Controller):
    """When clicked, drag items."""

    def on_mouse_game_press(self, point: Vec2, buttons: int, mod):
        """Event: handle mouse."""
        if pyglet.window.mouse.LEFT & buttons:
            self.begin_drag(point)

    def begin_drag(self, point: Vec2):
        """On mouse press, find intersecting items and grab one."""
        # Find top item
        top_item = -1
        top_order = -1
        for item_entity, _ in self.world.get(Item):
            item_controller = desper.controller(item_entity, self.world)
            sprite: Sprite = item_controller.get_component(Sprite)
            if physics.point_collision(point, item_controller) and top_order < sprite.group.order:
                top_item = item_entity
                top_order = sprite.group.order

        print('top item is', top_item)
