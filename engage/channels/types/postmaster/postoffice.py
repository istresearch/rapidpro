from django.conf import settings

po_server_url = getattr(settings, "POST_OFFICE_API_URL", ())
po_api_key = getattr(settings, "POST_OFFICE_API_KEY", ())
po_api_header = "po-api-key"
