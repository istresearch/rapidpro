from django.template import Context, Template

from temba.tests import TembaTest

from .sms import attachment_button


class TestSMSTagLibrary(TembaTest):
    def test_attachment_button(self):
        # complete attachment with subtype and extension
        self.assertEqual(
            {
                "content_type": "image/jpeg",
                "category": "image",
                "preview": "JPEG",
                "url": "https://example.com/test.jpg",
                "is_playable": False,
            },
            attachment_button("image/jpeg:https://example.com/test.jpg"),
        )

        # missing extension and thus no subtype
        self.assertEqual(
            {
                "content_type": "image",
                "category": "image",
                "preview": "IMAGE",
                "url": "https://example.com/test.aspx",
                "is_playable": False,
            },
            attachment_button("image:https://example.com/test.aspx"),
        )

        # ogg file with wrong content type
        self.assertEqual(
            {
                "content_type": "audio/ogg",
                "category": "audio",
                "preview": "OGG",
                "url": "https://example.com/test.ogg",
                "is_playable": True,
            },
            attachment_button("application/octet-stream:https://example.com/test.ogg"),
        )

        # geo coordinates
        self.assertEqual(
            {
                "content_type": "geo",
                "category": "geo",
                "preview": "-35.998287,26.478109",
                "url": "http://www.openstreetmap.org/?mlat=-35.998287&mlon=26.478109#map=18/-35.998287/26.478109",
                "is_playable": False,
            },
            attachment_button("geo:-35.998287,26.478109"),
        )

        context = Context(attachment_button("image/jpeg:https://example.com/test.jpg"))
        template = Template("""{% load sms %}{% attachment_button 'image/jpeg:https://example.com/test.jpg' %}""")
        self.assertIn("data-featherlight", template.render(context))
        self.assertIn('src="https://example.com/test.jpg"', template.render(context))
