"""Handle sound."""
import random
import desper

DELIVERY_BUTTON_SFX = 'media/button'
STEPS_IN_SFX = 'media/steps_in'
VOICE_SFX_FOLDER = 'media/voice'
PICKUP_SFX = 'media/pickup'
DROP_SFX = 'media/drop'
HOOK_SFX = 'media/hook'


@desper.event_handler('on_delivery', 'on_pickup', 'on_drop', 'on_hook')
class SFXManager:
    """Play sounds based on triggered events."""
    mute = False

    @desper.coroutine
    def on_delivery(self, *args):
        """Play sound of the delivery button."""
        if self.mute:
            return

        desper.resource_map[DELIVERY_BUTTON_SFX].play()

        yield 0.2
        desper.resource_map[STEPS_IN_SFX].play()

    def on_pickup(self):
        """Play pickup sound."""
        if self.mute:
            return

        desper.resource_map[PICKUP_SFX].play()

    def on_drop(self):
        """Play drop sound."""
        if self.mute:
            return

        desper.resource_map[DROP_SFX].play()

    def on_hook(self):
        """Play drop sound."""
        if self.mute:
            return

        desper.resource_map[HOOK_SFX].play()


@desper.event_handler('on_switch_in')
class VoiceSFXManager:
    """Handle voice sounds."""
    mute = False

    def on_switch_in(self, *args):
        """Play some voice eventually."""
        if self.mute:
            return

        all_voices = tuple(desper.resource_map[VOICE_SFX_FOLDER].handles.values())
        random.choice(all_voices)().play()
