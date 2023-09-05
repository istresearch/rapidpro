from engage.utils.class_overrides import MonkeyPatcher

from temba.msgs.models import Label
from temba.msgs.tests import LabelCRUDLTest


class LabelCRUDLTestOverrides(MonkeyPatcher):
    patch_class = LabelCRUDLTest

    def test_label_delete_with_flow_dependency(self):

        label_one = Label.create(self.org, self.user, "label1")

        from temba.flows.models import Flow

        self.get_flow("dependencies")
        flow = Flow.objects.filter(name="Dependencies").first()

        flow.label_dependencies.add(label_one)

        # release method raises ValueError
        with self.assertRaises(ValueError) as release_error:
            label_one.release()

        self.assertEqual(str(release_error.exception), f"Cannot delete Label: {label_one.name}, used by 1 flows")
    #enddef test_label_delete_with_flow_dependency

#endclass LabelCRUDLTestOverrides
