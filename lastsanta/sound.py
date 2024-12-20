"""Handle sound."""
import desper

DELIVERY_BUTTON_SFX = 'media/button'
STEPS_IN_SFX = 'media/steps_in'


@desper.event_handler('on_delivery')
class SFXManager:
    """Play sounds based on triggered events."""
    mute = False

    @desper.coroutine
    def on_delivery(self, *args):
        """Play sound of the delivery button."""
        if self.mute:
            return

        desper.resource_map[DELIVERY_BUTTON_SFX].play()

        yield 0.1
        desper.resource_map[STEPS_IN_SFX].play()
