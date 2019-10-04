from unittest.mock import patch

from django.urls import reverse

from temba.classifiers.models import Classifier
from temba.tests import MockResponse, TembaTest

from .type import WitType


class WitTypeTest(TembaTest):
    def test_connect(self):
        url = reverse("classifiers.classifier_connect")
        response = self.client.get(url)
        self.assertRedirect(response, "/users/login/")

        self.login(self.admin)
        response = self.client.get(url)

        # should have url for claiming our type
        url = reverse("classifiers.types.wit.connect")
        self.assertContains(response, url)

        response = self.client.get(url)
        post_data = response.context["form"].initial

        # will fail as we don't have anything filled out
        response = self.client.post(url, post_data)
        self.assertFormError(response, "form", "app_id", ["This field is required."])

        # ok, will everything out
        post_data["name"] = "Booker"
        post_data["app_id"] = "12345"
        post_data["access_token"] = "sesame"

        # can't connect
        with patch("requests.get") as mock_get:
            mock_get.return_value = MockResponse(400, '{ "error": "true" }')
            response = self.client.post(url, post_data)
            self.assertEqual(200, response.status_code)
            self.assertFalse(Classifier.objects.all())

            self.assertContains(response, "Unable to access wit.ai with credentials")

        # no intent entity
        with patch("requests.get") as mock_get:
            mock_get.side_effect = [
                MockResponse(200, '["wit$age_of_person"]'),
                MockResponse(404, '{"error": "not found"}'),
            ]

            response = self.client.post(url, post_data)
            self.assertEqual(200, response.status_code)
            self.assertFalse(Classifier.objects.all())
            self.assertContains(response, "Unable to get intent entity")

        # all good
        with patch("requests.get") as mock_get:
            mock_get.side_effect = [
                MockResponse(200, '["intent", "wit$age_of_person"]'),
                MockResponse(200, '{"builtin": false, "name": "intent"}'),
            ]

            response = self.client.post(url, post_data)
            self.assertEqual(302, response.status_code)
            c = Classifier.objects.get()
            self.assertEqual("Booker", c.name)
            self.assertEqual("wit", c.classifier_type)
            self.assertEqual("sesame", c.config[WitType.CONFIG_ACCESS_TOKEN])
            self.assertEqual("12345", c.config[WitType.CONFIG_APP_ID])
