from django.utils import timezone

from engage.utils.class_overrides import MonkeyPatcher

from temba.msgs.models import Msg, Label


class MsgModelOverride(MonkeyPatcher):
    patch_class = Msg

    def archive(self):
        """
        Archives this message
        """
        # engage: allow for any kind of msg type
        #if self.direction != Msg.DIRECTION_IN:
        #    raise ValueError("Can only archive incoming non-test messages")

        self.visibility = Msg.VISIBILITY_ARCHIVED
        self.save(update_fields=("visibility", "modified_on"))
    #enddef archive

    def restore(self):
        """
        Restores (i.e. un-archives) this message
        """
        # engage: allow for any kind of msg type
        #if self.direction != Msg.DIRECTION_IN:  # pragma: needs cover
        #    raise ValueError("Can only restore incoming non-test messages")

        self.visibility = Msg.VISIBILITY_VISIBLE
        self.save(update_fields=("visibility", "modified_on"))
    #enddef restore

#endclass MsgModelOverride


class LabelModelOverride(MonkeyPatcher):
    patch_class = Label

    def toggle_label(self, msgs, add):
        """
        Adds or removes this label from the given messages
        """

        assert not self.is_folder(), "can't assign messages to label folders"

        changed = set()

        for msg in msgs:
            # engage: allow for any kind of msg type
            #if msg.direction != Msg.DIRECTION_IN:
            #    raise ValueError("Can only apply labels to incoming messages")

            # if we are adding the label and this message doesn't have it, add it
            if add:
                if not msg.labels.filter(pk=self.pk):
                    msg.labels.add(self)
                    changed.add(msg.pk)

            # otherwise, remove it if not already present
            else:
                if msg.labels.filter(pk=self.pk):
                    msg.labels.remove(self)
                    changed.add(msg.pk)

        # update modified on all our changed msgs
        Msg.objects.filter(id__in=changed).update(modified_on=timezone.now())

        return changed
    #enddef toggle_label

#endclass LabelModelOverride
