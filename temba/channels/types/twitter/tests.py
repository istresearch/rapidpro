from __future__ import unicode_literals, absolute_import

import json

from django.test import override_settings
from django.urls import reverse
from mock import patch
from temba.tests import TembaTest
from ...models import Channel


class TwitterTypeTest(TembaTest):
    def setUp(self):
        super(TwitterTypeTest, self).setUp()

        self.channel = Channel.create(self.org, self.user, None, 'TT', name="Twitter", address="billy_bob",
                                      role="SR", scheme='twitter', config={})

    @override_settings(IS_PROD=True)
    @patch('twython.Twython.get_authentication_tokens')
    @patch('temba.utils.mage.MageClient.activate_twitter_stream')
    @patch('twython.Twython.get_authorized_tokens')
    def test_claim(self, mock_get_authorized_tokens, mock_activate_twitter_stream, mock_get_authentication_tokens):
        self.login(self.admin)

        self.channel.delete()  # remove existing twitter channel

        claim_url = reverse('channels.channel_claim_twitter')

        mock_get_authentication_tokens.return_value = {
            'oauth_token': 'abcde',
            'oauth_token_secret': '12345',
            'auth_url': 'http://example.com/auth'
        }

        response = self.client.get(claim_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['twitter_auth_url'], 'http://example.com/auth')
        self.assertEqual(self.client.session['twitter_oauth_token'], 'abcde')
        self.assertEqual(self.client.session['twitter_oauth_token_secret'], '12345')

        mock_activate_twitter_stream.return_value = {}

        mock_get_authorized_tokens.return_value = {
            'screen_name': 'billy_bob',
            'user_id': 123,
            'oauth_token': 'bcdef',
            'oauth_token_secret': '23456'
        }

        response = self.client.get(claim_url, {'oauth_verifier': 'vwxyz'}, follow=True)
        self.assertNotIn('twitter_oauth_token', self.client.session)
        self.assertNotIn('twitter_oauth_token_secret', self.client.session)
        self.assertEqual(response.status_code, 200)

        channel = response.context['object']
        self.assertEqual(channel.address, 'billy_bob')
        self.assertEqual(channel.name, '@billy_bob')
        config = json.loads(channel.config)
        self.assertEqual(config['handle_id'], 123)
        self.assertEqual(config['oauth_token'], 'bcdef')
        self.assertEqual(config['oauth_token_secret'], '23456')

        # re-add same account but with different auth credentials
        s = self.client.session
        s['twitter_oauth_token'] = 'cdefg'
        s['twitter_oauth_token_secret'] = '34567'
        s.save()

        mock_get_authorized_tokens.return_value = {
            'screen_name': 'billy_bob',
            'user_id': 123,
            'oauth_token': 'defgh',
            'oauth_token_secret': '45678'
        }

        response = self.client.get(claim_url, {'oauth_verifier': 'uvwxy'}, follow=True)
        self.assertEqual(response.status_code, 200)

        channel = response.context['object']
        self.assertEqual(channel.address, 'billy_bob')
        config = json.loads(channel.config)
        self.assertEqual(config['handle_id'], 123)
        self.assertEqual(config['oauth_token'], 'defgh')
        self.assertEqual(config['oauth_token_secret'], '45678')

    @override_settings(IS_PROD=True)
    @patch('temba.utils.mage.MageClient._request')
    def test_release(self, mock_mage_request):
        # check that removing Twitter channel notifies Mage
        self.channel.release()

        mock_mage_request.assert_called_once_with('DELETE', 'twitter/%s' % self.channel.uuid)
