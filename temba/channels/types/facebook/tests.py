from __future__ import unicode_literals, absolute_import

import json

from django.test import override_settings
from django.urls import reverse
from mock import patch
from temba.tests import TembaTest, MockResponse
from ...models import Channel


class FacebookTypeTest(TembaTest):
    def setUp(self):
        super(FacebookTypeTest, self).setUp()

        self.channel = Channel.create(self.org, self.user, None, 'FB', name="Facebook", address="1234567",
                                      role="SR", scheme='facebook', config={'auth_token': '09876543'})

    @override_settings(IS_PROD=True)
    @patch('requests.get')
    @patch('requests.post')
    def test_claim(self, mock_post, mock_get):
        url = reverse('channels.claim_facebook')

        self.login(self.admin)

        # check that claim page URL appears on claim list page
        response = self.client.get(reverse('channels.channel_claim'))
        self.assertContains(response, url)

        token = 'x' * 200
        mock_get.return_value = MockResponse(400, json.dumps({'error': {'message': "Failed validation"}}))

        # try to claim facebook, should fail because our verification of the token fails
        response = self.client.post(url, {'page_access_token': token})

        # assert we got a normal 200 and it says our token is wrong
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Failed validation")

        # ok this time claim with a success
        mock_get.return_value = MockResponse(200, json.dumps({'name': "Temba", 'id': 10}))
        response = self.client.post(url, {'page_access_token': token}, follow=True)

        # assert our channel got created
        channel = Channel.objects.get(address='10')
        self.assertEqual(channel.config_json()[Channel.CONFIG_AUTH_TOKEN], token)
        self.assertEqual(channel.config_json()[Channel.CONFIG_PAGE_NAME], 'Temba')
        self.assertEqual(channel.address, '10')

        # should be on our configuration page displaying our secret
        self.assertContains(response, channel.secret)

        # test validating our secret
        handler_url = reverse('handlers.facebook_handler', args=['invalid'])
        response = self.client.get(handler_url)
        self.assertEqual(response.status_code, 400)

        # test invalid token
        handler_url = reverse('handlers.facebook_handler', args=[channel.uuid])
        payload = {'hub.mode': 'subscribe', 'hub.verify_token': 'invalid', 'hub.challenge': 'challenge'}
        response = self.client.get(handler_url, payload)
        self.assertEqual(response.status_code, 400)

        # test actual token
        payload['hub.verify_token'] = channel.secret

        # try with unsuccessful callback to subscribe (this fails silently)
        mock_post.return_value = MockResponse(400, json.dumps({'success': True}))

        response = self.client.get(handler_url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'challenge')

        # assert we subscribed to events
        self.assertEqual(mock_post.call_count, 1)

        # but try again and we should try again
        mock_post.reset_mock()
        mock_post.return_value = MockResponse(200, json.dumps({'success': True}))

        response = self.client.get(handler_url, payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'challenge')

        # assert we subscribed to events
        self.assertEqual(mock_post.call_count, 1)

    @override_settings(IS_PROD=True)
    @patch('requests.delete')
    def test_release(self, mock_delete):
        mock_delete.return_value = MockResponse(200, json.dumps({'success': True}))
        self.channel.release()

        mock_delete.assert_called_once_with('https://graph.facebook.com/v2.5/me/subscribed_apps',
                                            params={'access_token': '09876543'})
