"""Define gifts for levels."""
from .logic import JointConstraint, ItemSetConstraint, ItemsNumberConstraint

# Some useful constants for part names
LIGHTBULB = 'lightbulb'
BASE1 = 'base1'


gifts = {
    'test':
        JointConstraint(
            ItemSetConstraint(BASE1),
            ItemSetConstraint(LIGHTBULB)
        )
}
