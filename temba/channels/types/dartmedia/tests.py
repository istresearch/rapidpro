from __future__ import unicode_literals, absolute_import

from django.test import override_settings
from django.urls import reverse
from temba.tests import TembaTest
from ...models import Channel


class DartMediaTypeTest(TembaTest):

    @override_settings(IP_ADDRESSES=('10.10.10.10', '172.16.20.30'))
    def test_claim(self):
        Channel.objects.all().delete()

        url = reverse('channels.claim_dartmedia')

        self.login(self.admin)

        response = self.client.get(reverse('channels.channel_claim'))
        self.assertNotContains(response, url)

        self.org.timezone = "Asia/Jakarta"
        self.org.save()

        # check that claim page URL appears on claim list page
        response = self.client.get(reverse('channels.channel_claim'))
        self.assertContains(response, url)

        # try to claim a channel
        response = self.client.get(url)
        self.assertEquals(response.context['view'].get_country({}), 'Indonesia')

        post_data = response.context['form'].initial

        post_data['username'] = 'uname'
        post_data['password'] = 'pword'
        post_data['number'] = '5151'
        post_data['country'] = 'ID'

        response = self.client.post(url, post_data)

        channel = Channel.objects.get()

        self.assertEquals('ID', channel.country)
        self.assertTrue(channel.uuid)
        self.assertEquals(post_data['number'], channel.address)
        self.assertEquals(post_data['username'], channel.config_json()['username'])
        self.assertEquals(post_data['password'], channel.config_json()['password'])
        self.assertEquals('DA', channel.channel_type)

        config_url = reverse('channels.channel_configuration', args=[channel.pk])
        self.assertRedirect(response, config_url)

        response = self.client.get(config_url)
        self.assertEquals(200, response.status_code)

        self.assertContains(response, reverse('courier.da', args=[channel.uuid, 'receive']))
        self.assertContains(response, reverse('courier.da', args=[channel.uuid, 'delivered']))

        # check we show the IP to whitelist
        self.assertContains(response, "10.10.10.10")
        self.assertContains(response, "172.16.20.30")
