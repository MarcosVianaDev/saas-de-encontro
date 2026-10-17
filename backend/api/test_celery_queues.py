from unittest.mock import patch

from celery.app.task import Context
from django.conf import settings
from django.test import SimpleTestCase
from kombu import Connection, Producer

from apps.events.export_tasks import generate
from config.celery import app


class CeleryQueueRoutingTests(SimpleTestCase):
    def test_exports_route_to_dedicated_queue_for_delay_and_send_task(self):
        with Connection('memory://') as connection, Producer(connection) as producer:
            with patch.object(producer, 'publish') as publish:
                generate.apply_async(args=['export-id'], producer=producer)
                self.assertEqual(publish.call_args.kwargs['routing_key'], 'exports')
                self.assertEqual([queue.name for queue in publish.call_args.kwargs['declare']], ['exports'])
                app.send_task(generate.name, args=['export-id'], producer=producer)
                self.assertEqual(publish.call_args.kwargs['routing_key'], 'exports')

    def test_all_periodic_tasks_keep_the_operational_queue(self):
        app.autodiscover_tasks(force=True)
        for schedule in settings.CELERY_BEAT_SCHEDULE.values():
            with self.subTest(task=schedule['task']):
                self.assertIn(schedule['task'], app.tasks)
                route = app.amqp.router.route({}, schedule['task'])
                self.assertEqual(route['queue'].name, 'celery')
        self.assertEqual(app.conf.task_default_queue, 'celery')

    def test_export_retry_preserves_its_delivery_queue(self):
        request = Context(id='retry-id', args=['export-id'], kwargs={}, retries=1,
                          delivery_info={'exchange': '', 'routing_key': 'exports'})
        retry = generate.signature_from_request(request=request)
        self.assertEqual(retry.options['queue'], 'exports')
        self.assertEqual(retry.args, ('export-id',))
        self.assertTrue(generate.acks_late)
