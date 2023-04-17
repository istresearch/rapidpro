class RequireUpdateFieldsMixin(object):
    """
    Copied from older version so migrations still operate correctly.
    """
    def save(self, *args, **kwargs):
        if self.id and "update_fields" not in kwargs and "force_insert" not in kwargs:
            raise ValueError("Updating without specifying update_fields is disabled for this model")

        super().save(*args, **kwargs)
    #enddef save
#endclass RequireUpdateFieldsMixin
