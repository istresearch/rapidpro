from decimal import Decimal

from django.contrib.auth.models import User
from django.core import checks
from django.db import connection, models
from django.test import TestCase

from temba.contacts.models import Contact
from temba.flows.models import Flow
from temba.tests import TembaTest

from .base import patch_queryset_count
from .es import IDSliceQuerySet
from .fields import JSONAsTextField


class ModelsTest(TembaTest):
    def test_patch_queryset_count(self):
        self.create_contact("Ann", urns=["twitter:ann"])
        self.create_contact("Bob", urns=["twitter:bob"])

        with self.assertNumQueries(0):
            qs = Contact.objects.all()
            patch_queryset_count(qs, lambda: 33)

            self.assertEqual(qs.count(), 33)


class IDSliceQuerySetTest(TembaTest):
    def test_fields(self):
        # if we don't specify fields, we fetch *
        users = IDSliceQuerySet(User, [self.user.id, self.editor.id], offset=0, total=3)

        self.assertEqual(
            f"""SELECT t.* FROM auth_user t JOIN (VALUES (1, {self.user.id}), (2, {self.editor.id})) tmp_resultset (seq, model_id) ON t.id = tmp_resultset.model_id ORDER BY tmp_resultset.seq""",
            users.raw_query,
        )

        with self.assertNumQueries(1):
            users = list(users)
        with self.assertNumQueries(0):  # already fetched
            users[0].email

        # if we do specify fields, it's like only on a regular queryset
        users = IDSliceQuerySet(User, [self.user.id, self.editor.id], only=("id", "first_name"), offset=0, total=3)

        self.assertEqual(
            f"""SELECT t.id, t.first_name FROM auth_user t JOIN (VALUES (1, {self.user.id}), (2, {self.editor.id})) tmp_resultset (seq, model_id) ON t.id = tmp_resultset.model_id ORDER BY tmp_resultset.seq""",
            users.raw_query,
        )

        with self.assertNumQueries(1):
            users = list(users)
        with self.assertNumQueries(1):  # requires fetch
            users[0].email

    def test_slicing(self):
        empty = IDSliceQuerySet(User, [], offset=0, total=0)
        self.assertEqual(0, len(empty))

        users = IDSliceQuerySet(User, [self.user.id, self.editor.id, self.admin.id], offset=0, total=3)
        self.assertEqual(self.user.id, users[0].id)
        self.assertEqual(self.editor.id, users[0:3][1].id)
        self.assertEqual(0, users.offset)
        self.assertEqual(3, users.total)

        with self.assertRaises(IndexError):
            users[4]

        with self.assertRaises(IndexError):
            users[-1]

        with self.assertRaises(IndexError):
            users[1:2]

        with self.assertRaises(TypeError):
            users["foo"]

        users = IDSliceQuerySet(User, [self.user.id, self.editor.id, self.admin.id], offset=10, total=100)
        self.assertEqual(self.user.id, users[10].id)
        self.assertEqual(self.user.id, users[10:11][0].id)

        with self.assertRaises(IndexError):
            users[0]

        with self.assertRaises(IndexError):
            users[11:15]

    def test_filter(self):
        users = IDSliceQuerySet(User, [self.user.id, self.editor.id, self.admin.id], offset=10, total=100)

        filtered = users.filter(pk=self.user.id)
        self.assertEqual(User, filtered.model)
        self.assertEqual([self.user.id], filtered.ids)
        self.assertEqual(0, filtered.offset)
        self.assertEqual(1, filtered.total)

        filtered = users.filter(pk__in=[self.user.id, self.admin.id])
        self.assertEqual(User, filtered.model)
        self.assertEqual([self.user.id, self.admin.id], filtered.ids)
        self.assertEqual(0, filtered.offset)
        self.assertEqual(2, filtered.total)

        # pks can be strings
        filtered = users.filter(pk=str(self.user.id))
        self.assertEqual([self.user.id], filtered.ids)

        # only filtering by pk is supported
        with self.assertRaises(ValueError):
            users.filter(name="Bob")

    def test_none(self):
        users = IDSliceQuerySet(User, [self.user.id, self.editor.id], offset=0, total=2)
        empty = users.none()
        self.assertEqual([], empty.ids)
        self.assertEqual(0, empty.total)

    def test_prefetch_related(self):
        flow1 = self.create_flow("Test 1")
        flow2 = self.create_flow("Test 2")
        with self.assertNumQueries(2):
            flows = list(IDSliceQuerySet(Flow, [flow1.id, flow2.id], offset=0, total=2).prefetch_related("org"))
            self.assertEqual(self.org, flows[0].org)
            self.assertEqual(self.org, flows[1].org)


class JsonModelTestDefaultNull(models.Model):
    field = JSONAsTextField(default=dict, null=True)


class JsonModelTestDefault(models.Model):
    field = JSONAsTextField(default=dict, null=False)


class JsonModelTestNull(models.Model):
    field = JSONAsTextField(null=True)


class TestJSONAsTextField(TestCase):
    def test_invalid_default(self):
        class InvalidJsonModel(models.Model):
            field = JSONAsTextField(default={})

        model = InvalidJsonModel()
        self.assertEqual(
            model.check(),
            [
                checks.Warning(
                    msg=(
                        "JSONAsTextField default should be a callable instead of an instance so that it's not shared "
                        "between all field instances."
                    ),
                    hint="Use a callable instead, e.g., use `dict` instead of `{}`.",
                    obj=InvalidJsonModel._meta.get_field("field"),
                    id="postgres.E003",
                )
            ],
        )

    def test_to_python(self):
        field = JSONAsTextField(default=dict)

        self.assertEqual(field.to_python({}), {})

        self.assertEqual(field.to_python("{}"), {})

    def test_default_with_null(self):
        model = JsonModelTestDefaultNull()
        model.save()
        model.refresh_from_db()

        # the field in the database is null, and we have set the default value so we get the default value
        self.assertEqual(model.field, {})

        with connection.cursor() as cur:
            cur.execute("select * from utils_jsonmodeltestdefaultnull")

            data = cur.fetchall()
        # but in the database the field is saved as null
        self.assertEqual(data[0][1], None)

    def test_default_without_null(self):
        model = JsonModelTestDefault()
        model.save()
        model.refresh_from_db()

        # the field in the database saves the default value, and we get the default value back
        self.assertEqual(model.field, {})

        with connection.cursor() as cur:
            cur.execute("select * from utils_jsonmodeltestdefault")

            data = cur.fetchall()
        # and in the database the field saved as default value
        self.assertEqual(data[0][1], "{}")

    def test_invalid_field_values(self):
        model = JsonModelTestDefault()
        model.field = "53"
        self.assertRaises(ValueError, model.save)

        model.field = 34
        self.assertRaises(ValueError, model.save)

        model.field = ""
        self.assertRaises(ValueError, model.save)

    def test_invalid_unicode(self):
        # invalid unicode escape sequences are stripped out
        model = JsonModelTestDefault()
        model.field = {"foo": "bar\u0000"}
        model.save()

        self.assertEqual({"foo": "bar"}, JsonModelTestDefault.objects.first().field)

    def test_write_None_value(self):
        model = JsonModelTestDefault()
        # assign None (null) value to the field
        model.field = None

        self.assertRaises(Exception, model.save)

    def test_read_values_db(self):
        with connection.cursor() as cur:
            # read a NULL as None
            cur.execute("DELETE FROM utils_jsonmodeltestnull")
            cur.execute("INSERT INTO utils_jsonmodeltestnull (field) VALUES (%s)", (None,))
            self.assertEqual(JsonModelTestNull.objects.first().field, None)

            # read JSON object as dict
            cur.execute("DELETE FROM utils_jsonmodeltestdefault")
            cur.execute("INSERT INTO utils_jsonmodeltestdefault (field) VALUES (%s)", ('{"foo": "bar"}',))
            self.assertEqual({"foo": "bar"}, JsonModelTestDefault.objects.first().field)

    def test_jsonb_columns(self):
        with connection.cursor() as cur:
            # simulate field being converted to actual JSONB
            cur.execute("DELETE FROM utils_jsonmodeltestdefault")
            cur.execute("INSERT INTO utils_jsonmodeltestdefault (field) VALUES (%s)", ('{"foo": "bar"}',))
            cur.execute("ALTER TABLE utils_jsonmodeltestdefault ALTER COLUMN field TYPE jsonb USING field::jsonb;")

            obj = JsonModelTestDefault.objects.first()
            self.assertEqual({"foo": "bar"}, obj.field)

            obj.field = {"zed": "doh"}
            obj.save()

            self.assertEqual({"zed": "doh"}, JsonModelTestDefault.objects.first().field)

    def test_invalid_field_values_db(self):
        with connection.cursor() as cur:
            cur.execute("DELETE FROM utils_jsonmodeltestdefault")
            cur.execute("INSERT INTO utils_jsonmodeltestdefault (field) VALUES (%s)", ("53",))
            self.assertRaises(ValueError, JsonModelTestDefault.objects.first)

            cur.execute("DELETE FROM utils_jsonmodeltestdefault")
            cur.execute("INSERT INTO utils_jsonmodeltestdefault (field) VALUES (%s)", ("None",))
            self.assertRaises(ValueError, JsonModelTestDefault.objects.first)

            cur.execute("DELETE FROM utils_jsonmodeltestdefault")
            cur.execute("INSERT INTO utils_jsonmodeltestdefault (field) VALUES (%s)", ("null",))
            self.assertRaises(ValueError, JsonModelTestDefault.objects.first)

            # simulate field being something non-JSON at db-level
            cur.execute("DELETE FROM utils_jsonmodeltestdefault")
            cur.execute("INSERT INTO utils_jsonmodeltestdefault (field) VALUES (%s)", ("1234",))
            cur.execute("ALTER TABLE utils_jsonmodeltestdefault ALTER COLUMN field TYPE int USING field::int;")
            self.assertRaises(ValueError, JsonModelTestDefault.objects.first)


class TestJSONField(TembaTest):
    def test_jsonfield_decimal_encoding(self):
        contact = self.create_contact("Xavier", phone="+5939790990001")

        contact.fields = {"1eaf5c91-8d56-4ca0-8e00-9b1c0b12e722": {"number": Decimal("123.4567890")}}
        contact.save(update_fields=("fields",))

        contact.refresh_from_db()
        self.assertEqual(contact.fields, {"1eaf5c91-8d56-4ca0-8e00-9b1c0b12e722": {"number": Decimal("123.4567890")}})
