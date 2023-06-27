from django.test.utils import override_settings
from django.urls import reverse

from temba.tests import CRUDLTestMixin, TembaTest

from .models import Global


class GlobalTest(TembaTest):
    def test_model(self):
        global1 = Global.get_or_create(self.org, self.admin, "org_name", "Org Name", "Acme Ltd")
        global2 = Global.get_or_create(self.org, self.admin, "access_token", "Access Token", "23464373")

        self.assertEqual("org_name", global1.key)
        self.assertEqual("Org Name", global1.name)
        self.assertEqual("Acme Ltd", global1.value)
        self.assertEqual("Org Name", str(global1))

        # update value if provided
        g1 = Global.get_or_create(self.org, self.admin, "org_name", "Org Name", "Acme Holdings")
        self.assertEqual(global1, g1)

        global1.refresh_from_db()
        self.assertEqual("Acme Holdings", global1.value)

        # generate name if not provided
        global3 = Global.get_or_create(self.org, self.admin, "secret_value", name="", value="")
        self.assertEqual("secret_value", global3.key)
        self.assertEqual("Secret Value", global3.name)
        self.assertEqual("", global3.value)

        flow1 = self.get_flow("color")
        flow2 = self.get_flow("favorites")

        flow1.global_dependencies.add(global1, global2)
        flow2.global_dependencies.add(global1)

        with self.assertNumQueries(1):
            g1, g2, g3 = Global.annotate_usage(self.org.globals.order_by("id"))
            self.assertEqual(2, g1.usage_count)
            self.assertEqual(1, g2.usage_count)
            self.assertEqual(0, g3.usage_count)

        global1.release(self.admin)
        global2.release(self.admin)
        global3.release(self.admin)

        self.assertEqual(0, Global.objects.filter(is_active=True).count())

    def test_make_key(self):
        self.assertEqual("org_name", Global.make_key("Org Name"))
        self.assertEqual("account_name", Global.make_key("Account   Name  "))
        self.assertEqual("caf", Global.make_key("café"))
        self.assertEqual(
            "323_ffsn_slfs_ksflskfs_fk_anfaddgas",
            Global.make_key("  ^%$# %$$ $##323 ffsn slfs ksflskfs!!!! fk$%%%$$$anfaDDGAS ))))))))) "),
        )

    def test_is_valid_key(self):
        self.assertTrue(Global.is_valid_key("token"))
        self.assertTrue(Global.is_valid_key("token_now_2"))
        self.assertTrue(Global.is_valid_key("email"))
        self.assertFalse(Global.is_valid_key("Token"))  # must be lowercase
        self.assertFalse(Global.is_valid_key("token!"))  # can't have punctuation
        self.assertFalse(Global.is_valid_key("âge"))  # a-z only
        self.assertFalse(Global.is_valid_key("2up"))  # can't start with a number
        self.assertFalse(Global.is_valid_key("a" * 37))  # too long

    def test_is_valid_name(self):
        self.assertTrue(Global.is_valid_name("Age"))
        self.assertTrue(Global.is_valid_name("Age Now 2"))
        self.assertFalse(Global.is_valid_name("Age>Now"))  # can't have punctuation
        self.assertTrue(Global.is_valid_name("API_KEY-2"))  # except underscores and hypens
        self.assertFalse(Global.is_valid_name("âge"))  # a-z only


class GlobalCRUDLTest(TembaTest, CRUDLTestMixin):
    def setUp(self):
        super().setUp()

        self.global1 = Global.get_or_create(self.org, self.admin, "org_name", "Org Name", "Acme Ltd")
        self.global2 = Global.get_or_create(self.org, self.admin, "access_token", "Access Token", "23464373")
        self.other_org_global = Global.get_or_create(self.org2, self.admin, "access_token", "Access Token", "653732")

        self.flow = self.create_flow("Color Flow")
        self.flow.global_dependencies.add(self.global1)

    def test_list_views(self):
        list_url = reverse("globals.global_list")

        response = self.assertListFetch(
            list_url, allow_viewers=False, allow_editors=False, context_objects=[self.global2, self.global1]
        )
        self.assertContains(response, "Acme Ltd")
        self.assertContains(response, "23464373")
        self.assertContains(response, "1 Use")

        response = self.client.get(list_url + "?search=access")
        self.assertEqual(list(response.context["object_list"]), [self.global2])

        unused_url = reverse("globals.global_unused")

        self.assertListFetch(unused_url, allow_viewers=False, allow_editors=False, context_objects=[self.global2])

    @override_settings(ORG_LIMIT_DEFAULTS={"globals": 4})
    def test_create(self):
        create_url = reverse("globals.global_create")

        self.assertCreateFetch(create_url, allow_viewers=False, allow_editors=False, form_fields=["name", "value"])

        # try to submit with invalid name and missing value
        self.assertCreateSubmit(
            create_url,
            {"name": "/?:"},
            form_errors={"name": "Can only contain letters, numbers and hypens.", "value": "This field is required."},
        )

        # try to submit with name that would become invalid key
        self.assertCreateSubmit(create_url, {"name": "-", "value": "123"}, form_errors={"name": "Isn't a valid name"})

        # submit with valid values
        self.assertCreateSubmit(
            create_url,
            {"name": "Secret", "value": "[xyz]"},
            success_status=200,
            new_obj_query=Global.objects.filter(org=self.org, name="Secret", value="[xyz]"),
        )

        # try to submit with same name
        self.assertCreateSubmit(
            create_url, {"name": "Secret", "value": "[abc]"}, form_errors={"name": "Must be unique."}
        )

        # works if name is unique
        self.assertCreateSubmit(
            create_url,
            {"name": "Secret2", "value": "[abc]"},
            success_status=200,
            new_obj_query=Global.objects.filter(org=self.org, name="Secret2", value="[abc]"),
        )

        # try to create another now that we've reached the limit
        self.assertCreateSubmit(
            create_url,
            {"name": "Secret3", "value": "[abc]"},
            form_errors={
                "__all__": "This workspace has reached its limit of 4 globals. You must delete existing ones before you can create new ones."
            },
        )

    def test_update(self):
        update_url = reverse("globals.global_update", args=[self.global1.id])

        self.assertUpdateFetch(update_url, allow_viewers=False, allow_editors=False, form_fields=["value"])

        # try to submit with missing value
        self.assertUpdateSubmit(
            update_url, {}, form_errors={"value": "This field is required."}, object_unchanged=self.global1
        )

        self.assertUpdateSubmit(update_url, {"value": "Acme Holdings"})

        self.global1.refresh_from_db()
        self.assertEqual("Org Name", self.global1.name)
        self.assertEqual("Acme Holdings", self.global1.value)

        # can't view update form for global in other org
        update_url = reverse("globals.global_update", args=[self.other_org_global.id])
        response = self.client.get(update_url)
        self.assertLoginRedirect(response)

        # can't update global in other org
        response = self.client.post(update_url, {"value": "436734573"})
        self.assertLoginRedirect(response)

        # global should be unchanged
        self.other_org_global.refresh_from_db()
        self.assertEqual("653732", self.other_org_global.value)

    def test_usages(self):
        detail_url = reverse("globals.global_usages", args=[self.global1.uuid])

        response = self.assertReadFetch(
            detail_url, allow_viewers=False, allow_editors=False, context_object=self.global1
        )

        self.assertEqual({"flow": [self.flow]}, {t: list(qs) for t, qs in response.context["dependents"].items()})

    def test_delete(self):
        delete_url = reverse("globals.global_delete", args=[self.global2.uuid])

        # fetch delete modal
        response = self.assertDeleteFetch(delete_url)
        self.assertContains(response, "You are about to delete")

        response = self.assertDeleteSubmit(delete_url, object_deactivated=self.global2, success_status=200)
        self.assertEqual("/global/", response["Temba-Success"])

        # should see warning if global is being used
        delete_url = reverse("globals.global_delete", args=[self.global1.uuid])

        self.assertFalse(self.flow.has_issues)

        response = self.assertDeleteFetch(delete_url)
        self.assertContains(response, "is used by the following items but can still be deleted:")
        self.assertContains(response, "Color Flow")

        response = self.assertDeleteSubmit(delete_url, object_deactivated=self.global1, success_status=200)
        self.assertEqual("/global/", response["Temba-Success"])

        self.flow.refresh_from_db()
        self.assertTrue(self.flow.has_issues)
        self.assertNotIn(self.global1, self.flow.global_dependencies.all())
