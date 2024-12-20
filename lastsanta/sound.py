"""Handle sound."""
import random

import desper
from ddesigner.default_model import ExecuteNode

DELIVERY_BUTTON_SFX = 'media/button'
PAPER_OUT_SFX = 'media/paper_out'
STEPS_IN_SFX = 'media/steps_in'
VOICE_SFX_FOLDER = 'media/voice'
HIT_SFXS = 'media/hits/hit1', 'media/hits/hit2'
PICKUP_SFX = 'media/pickup'
DROP_SFX = 'media/drop'
HOOK_SFX = 'media/hook'


@ExecuteNode.subscriber
def sfx_subscriber(sfx: str, _):
    """Interpret all commands as SFX, for simplicity."""
    # Check for mute?
    desper.resource_map[sfx].play()


@desper.event_handler('on_delivery', 'on_pickup', 'on_drop', 'on_hook', 'on_bounce')
class SFXManager:
    """Play sounds based on triggered events."""
    mute = False

    @desper.coroutine
    def on_delivery(self, *args):
        """Play sound of the delivery button."""
        if self.mute:
            return

        desper.resource_map[PAPER_OUT_SFX].play()

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

    def on_bounce(self):
        if self.mute:
            return

        desper.resource_map[random.choice(HIT_SFXS)].play()


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
