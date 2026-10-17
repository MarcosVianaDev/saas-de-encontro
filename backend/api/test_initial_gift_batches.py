from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection, transaction
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from kombu.exceptions import OperationalError as BrokerOperationalError

from api import test_initial_gifts
from apps.audit.models import AuditLog
from apps.notifications.models import Notification
from apps.participants.models import EventParticipant
from apps.passes.gifts import due_initial_gift_participants, grant_due_initial_gifts, grant_initial_gift
from apps.passes.models import InitialGiftSweep, ParticipantPass, PassActivation
from apps.passes.tasks import GIFT_LEASE_SECONDS, initial_gift_batch, initial_gifts
from config.testing import DisposableTransactionTestCase


class InitialGiftBatchTests(TestCase):
    setUp = test_initial_gifts.InitialGiftTests.setUp
    configure = test_initial_gifts.InitialGiftTests.configure

    def start(self):
        with patch('apps.passes.tasks.initial_gift_batch.delay') as enqueue:
            self.assertTrue(initial_gifts())
        return enqueue.call_args.args[0]

    def add_participants(self, count):
        users = get_user_model().objects.bulk_create([
            get_user_model()(username=f'batch-{index}') for index in range(count)
        ])
        return EventParticipant.objects.bulk_create([
            EventParticipant(event=self.event, user=user, is_active=True, activated_at=self.now)
            for user in users
        ])

    def test_dispatcher_does_not_deliver_and_overlapping_beat_is_skipped(self):
        self.configure()
        with patch('apps.passes.gifts.grant_initial_gift') as grant:
            with patch('apps.passes.tasks.initial_gift_batch.delay') as enqueue:
                self.assertTrue(initial_gifts())
                self.assertFalse(initial_gifts())
            enqueue.assert_called_once()
            grant.assert_not_called()
        self.assertFalse(ParticipantPass.objects.exists())

    @override_settings(INITIAL_GIFT_BATCH_SIZE=25)
    def test_5000_participants_are_split_by_cursor_without_loading_or_granting_all(self):
        self.configure()
        self.add_participants(4999)
        token = self.start()
        after = None
        seen = []
        batches = 0
        with patch('apps.passes.gifts.grant_initial_gift', side_effect=lambda p: seen.append(p.pk) or True):
            while True:
                with patch('apps.passes.tasks.initial_gift_batch.delay') as enqueue:
                    with CaptureQueriesContext(connection) as queries:
                        self.assertEqual(initial_gift_batch(token, after), 25)
                self.assertEqual(len(queries), 3)  # lease, bounded ID query, cursor/release
                self.assertIn('LIMIT 26', queries[1]['sql'])
                batches += 1
                if not enqueue.called:
                    break
                self.assertEqual(enqueue.call_count, 1)
                self.assertEqual(enqueue.call_args.args[0], token)
                after = enqueue.call_args.args[1]
        self.assertEqual(batches, 200)
        self.assertEqual(len(set(seen)), 5000)
        self.assertEqual(seen, sorted(seen))
        self.assertTrue(initial_gifts_with_mocked_publish())

    @override_settings(INITIAL_GIFT_BATCH_SIZE=2)
    def test_synchronous_helper_is_also_bounded(self):
        self.configure()
        self.add_participants(4)
        with patch('apps.passes.gifts.grant_initial_gift', return_value=True) as grant:
            self.assertEqual(grant_due_initial_gifts(), 2)
        self.assertEqual(grant.call_count, 2)

    def test_batch_redelivery_does_not_duplicate_pass_activation_notification_or_audit(self):
        self.configure()
        token = self.start()
        self.assertEqual(initial_gift_batch(token), 1)
        self.assertEqual(initial_gift_batch(token), 0)
        new_token = self.start()
        self.assertEqual(initial_gift_batch(new_token), 0)
        self.assertEqual(ParticipantPass.objects.count(), 1)
        self.assertEqual(PassActivation.objects.count(), 1)
        self.assertEqual(Notification.objects.filter(kind='pass_activated').count(), 1)
        self.assertEqual(AuditLog.objects.filter(action='pass.initial_gift_granted').count(), 1)

    def test_ended_event_and_disabled_participant_are_rechecked_at_execution(self):
        self.configure()
        token = self.start()
        self.event.ends_at = timezone.now() - timedelta(seconds=1)
        type(self.event).objects.filter(pk=self.event.pk).update(ends_at=self.event.ends_at)
        self.assertEqual(initial_gift_batch(token), 0)
        self.assertFalse(ParticipantPass.objects.exists())
        type(self.event).objects.filter(pk=self.event.pk).update(ends_at=self.now + timedelta(hours=2))
        token = self.start()
        EventParticipant.objects.filter(pk=self.participant.pk).update(is_active=False)
        self.assertEqual(initial_gift_batch(token), 0)
        self.assertFalse(ParticipantPass.objects.exists())

    def test_clock_is_checked_again_for_every_grant(self):
        self.configure()
        token = self.start()
        # The selection can happen before the deadline, with the grant occurring
        # after it (including time waiting for a participant row lock).
        with patch('apps.passes.gifts.timezone.now', side_effect=[self.now, self.event.ends_at, self.event.ends_at]):
            self.assertEqual(initial_gift_batch(token), 0)
        self.assertFalse(ParticipantPass.objects.exists())

    def test_future_gifts_are_filtered_before_granting(self):
        self.configure(delay_minutes=15)
        self.assertFalse(due_initial_gift_participants(self.now + timedelta(minutes=14)).exists())
        self.assertEqual(list(due_initial_gift_participants(self.now + timedelta(minutes=15))), [self.participant])

    @override_settings(INITIAL_GIFT_BATCH_SIZE=2)
    def test_real_deliveries_continue_until_every_participant_has_one_activated_gift(self):
        self.configure()
        self.add_participants(4)
        token = self.start()
        after = None
        delivered = []
        while True:
            with patch('apps.passes.tasks.initial_gift_batch.delay') as enqueue:
                delivered.append(initial_gift_batch(token, after))
            if not enqueue.called:
                break
            after = enqueue.call_args.args[1]
        self.assertEqual(delivered, [2, 2, 1])
        self.assertEqual(ParticipantPass.objects.count(), 5)
        self.assertEqual(PassActivation.objects.count(), 5)
        self.assertEqual(Notification.objects.filter(kind='pass_activated').count(), 5)
        self.assertEqual(AuditLog.objects.filter(action='pass.initial_gift_granted').count(), 5)

    def test_failed_delivery_rolls_back_and_is_retried_in_the_next_sweep(self):
        self.configure()
        token = self.start()
        with patch('apps.passes.gifts.notify', side_effect=ValueError('notification failure')):
            with self.assertLogs('apps.passes.tasks', level='ERROR'):
                self.assertEqual(initial_gift_batch(token), 0)
        self.assertFalse(ParticipantPass.objects.exists())
        self.assertFalse(PassActivation.objects.exists())
        self.assertFalse(AuditLog.objects.filter(action='pass.initial_gift_granted').exists())
        self.assertEqual(initial_gift_batch(self.start()), 1)

    @override_settings(INITIAL_GIFT_BATCH_SIZE=2)
    def test_failure_in_one_participant_does_not_starve_the_others(self):
        self.configure()
        self.add_participants(3)
        token = self.start()
        ordered = list(EventParticipant.objects.order_by('pk').values_list('pk', flat=True))
        seen = []

        def grant(participant):
            seen.append(participant.pk)
            if participant.pk == ordered[0]:
                raise ValueError('broken participant configuration')
            return True

        with patch('apps.passes.gifts.grant_initial_gift', side_effect=grant):
            with self.assertLogs('apps.passes.tasks', level='ERROR'):
                with patch('apps.passes.tasks.initial_gift_batch.delay') as enqueue:
                    self.assertEqual(initial_gift_batch(token), 1)
            self.assertEqual(initial_gift_batch(token, enqueue.call_args.args[1]), 2)
        self.assertEqual(seen, ordered)

    def test_time_budget_publishes_continuation_before_batch_limit(self):
        self.configure()
        self.add_participants(4)
        token = self.start()
        with patch('apps.passes.tasks.monotonic', side_effect=[0, 6]):
            with patch('apps.passes.gifts.grant_initial_gift', return_value=True) as grant:
                with patch('apps.passes.tasks.initial_gift_batch.delay') as enqueue:
                    self.assertEqual(initial_gift_batch(token), 1)
        grant.assert_called_once()
        enqueue.assert_called_once_with(token, str(grant.call_args.args[0].pk))

    def test_lease_expiration_recovers_a_lost_worker_and_rejects_old_task(self):
        self.configure()
        old_token = self.start()
        now = timezone.now()
        InitialGiftSweep.objects.update(expires_at=now - timedelta(seconds=1))
        token = self.start()
        self.assertNotEqual(token, old_token)
        self.assertEqual(initial_gift_batch(old_token), 0)
        self.assertEqual(initial_gift_batch(token), 1)

    def test_each_continuation_renews_the_lease_and_stale_cursor_is_ignored(self):
        self.configure()
        self.add_participants(settings.INITIAL_GIFT_BATCH_SIZE)
        token = self.start()
        now = timezone.now()
        InitialGiftSweep.objects.update(expires_at=now + timedelta(seconds=1))
        with patch('apps.passes.gifts.grant_initial_gift', return_value=True):
            with patch('apps.passes.tasks.initial_gift_batch.delay') as enqueue:
                self.assertEqual(initial_gift_batch(token), settings.INITIAL_GIFT_BATCH_SIZE)
            self.assertEqual(initial_gift_batch(token), 0)
        sweep = InitialGiftSweep.objects.get()
        self.assertGreater(sweep.expires_at, now + timedelta(seconds=GIFT_LEASE_SECONDS - 1))
        self.assertEqual(sweep.cursor, UUID(enqueue.call_args.args[1]))

    def test_publish_failure_releases_lease_for_next_beat(self):
        with patch('apps.passes.tasks.initial_gift_batch.delay', side_effect=BrokerOperationalError('offline')):
            with self.assertRaises(BrokerOperationalError):
                initial_gifts()
        self.assertTrue(initial_gifts_with_mocked_publish())

    @override_settings(INITIAL_GIFT_BATCH_SIZE=1)
    def test_failed_continuation_can_be_recovered_by_a_new_sweep(self):
        self.configure()
        self.add_participants(1)
        token = self.start()
        with patch('apps.passes.tasks.initial_gift_batch.delay', side_effect=BrokerOperationalError('offline')):
            with self.assertRaises(BrokerOperationalError):
                initial_gift_batch.run.__wrapped__(token)
        token = self.start()
        self.assertEqual(initial_gift_batch(token), 1)
        self.assertEqual(ParticipantPass.objects.count(), 2)


def initial_gifts_with_mocked_publish():
    with patch('apps.passes.tasks.initial_gift_batch.delay'):
        return initial_gifts()


class InitialGiftSweepConcurrencyTests(DisposableTransactionTestCase):
    setUp = test_initial_gifts.InitialGiftTests.setUp
    configure = test_initial_gifts.InitialGiftTests.configure

    def test_simultaneous_beat_dispatchers_publish_only_one_sweep(self):
        def dispatch():
            close_old_connections()
            try:
                return initial_gifts()
            finally:
                close_old_connections()

        with patch('apps.passes.tasks.initial_gift_batch.delay') as enqueue:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: dispatch(), range(2)))
        self.assertEqual(sorted(results), [False, True])
        enqueue.assert_called_once()

    def test_concurrent_deliveries_grant_only_one_pass_and_notification(self):
        with transaction.atomic():
            self.configure()
        barrier = Barrier(2)

        def grant():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return grant_initial_gift(self.participant)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: grant(), range(2)))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(ParticipantPass.objects.count(), 1)
        self.assertEqual(PassActivation.objects.count(), 1)
        self.assertEqual(Notification.objects.filter(kind='pass_activated').count(), 1)
        self.assertEqual(AuditLog.objects.filter(action='pass.initial_gift_granted').count(), 1)
