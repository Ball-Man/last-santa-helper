"""Define gifts for levels."""
from .logic import JointConstraint, ItemSetConstraint, ItemsNumberConstraint

# Some useful constants for part names
LIGHTBULB = 'lightbulb'
BASE1 = 'base1'
BASES = 'base1', 'base2', 'base3'
WHEEL = 'wheel'
DRAGON_HEAD = 'dragon_head'
HUMAN_PARTS = 'arm', 'leg', 'eye'
BATTERY = 'battery'

CRITICAL_ITEMS = 'uranium', 'bullet'


gifts = {
    'test':
        JointConstraint(
            ItemSetConstraint(1, BASE1),
            ItemSetConstraint(1, LIGHTBULB)
        ),
    'tutorial1': ItemSetConstraint(1, LIGHTBULB),
    'tutorial2':
        JointConstraint(
            ItemSetConstraint(1, BASE1),
            ItemSetConstraint(1, LIGHTBULB)
        ),
    'tutorial3':
        JointConstraint(
            ItemSetConstraint(1, BASE1),
            ItemSetConstraint(1, WHEEL),
            ItemSetConstraint(1, LIGHTBULB)
        ),
    'dragon_head':
        JointConstraint(
            ItemSetConstraint(1, DRAGON_HEAD),
            ItemSetConstraint(2, *HUMAN_PARTS)
        ),
    'carpet': ItemSetConstraint(3, *BASES),
    'car': JointConstraint(
            ItemSetConstraint(1, *BASES),
            ItemSetConstraint(2, WHEEL),
            ItemSetConstraint(2, BATTERY)
        ),
}
