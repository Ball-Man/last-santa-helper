"""Define gifts for levels."""
from .logic import JointConstraint, ItemSetConstraint, ItemsNumberConstraint

# Some useful constants for part names
LIGHTBULB = 'lightbulb'
BASE1 = 'base1'

CRITICAL_ITEMS = 'uranium', 'bullet'


gifts = {
    'test':
        JointConstraint(
            ItemSetConstraint(1, BASE1),
            ItemSetConstraint(1, LIGHTBULB)
        )
}
