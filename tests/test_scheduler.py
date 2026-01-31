import unittest

from config import AdvancedConfig, BehaviorConfig
from scheduler import Scheduler


class SchedulerTests(unittest.TestCase):
    def test_cooldowns_and_limits(self):
        behavior = BehaviorConfig(
            post_cooldown_minutes=60,
            comment_cooldown_minutes=1,
            max_posts_per_day=1,
        )
        scheduler = Scheduler(behavior, AdvancedConfig())

        self.assertTrue(scheduler.can_do("post"))
        scheduler.record_action("post")
        self.assertFalse(scheduler.can_do("post"))

        self.assertTrue(scheduler.can_do("comment"))
        scheduler.record_action("comment")
        self.assertFalse(scheduler.can_do("comment"))
        self.assertGreater(scheduler.next_available_in("comment"), 0)
