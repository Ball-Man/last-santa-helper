"""Main game logic and user interactions."""
import desper
import pyglet
from pyglet.math import Vec2
from pyglet.sprite import Sprite

from . import physics


class Item:
    """Represents an in game item."""


@desper.event_handler('on_mouse_game_press', 'on_mouse_game_motion')
class ItemDragManager(desper.Controller):
    """When clicked, drag items."""
    dragged: desper.Controller | None = None
    offset: Vec2 = Vec2()

    def on_mouse_game_press(self, point: Vec2, buttons: int, mod):
        """Event: handle mouse."""
        if pyglet.window.mouse.LEFT & buttons:
            self.begin_drag(point)

    def on_mouse_game_motion(self, mouse_position: Vec2):
        """If something is being dragged, drag it."""
        if self.dragged is None:        # Nothing to drag
            return

        transform = self.dragged.get_component(desper.Transform2D)
        transform.position = desper.math.Vec2(*(mouse_position - self.offset))

    def begin_drag(self, point: Vec2):
        """On mouse press, find intersecting items and grab one."""
        # TODO: pixel perfect check
        # Find top item
        top_item = None
        top_order = -1
        for item_entity, _ in self.world.get(Item):
            item_controller = desper.controller(item_entity, self.world)
            sprite: Sprite = item_controller.get_component(Sprite)
            if physics.point_collision(point, item_controller) and top_order < sprite.group.order:
                top_item = item_controller
                top_order = sprite.group.order

        if top_item is None:            # Nothing to drag
            return

        # Save current item and mouse offset for dragging
        self.dragged = top_item
        self.offset = point - top_item.get_component(desper.Transform2D).position
        top_item.remove_component(physics.Velocity)
