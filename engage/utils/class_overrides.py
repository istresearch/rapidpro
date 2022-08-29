import logging
from typing import Any, Callable

from django import forms
from django.db.models import Model


logger = logging.getLogger(__name__)

def ignoreDjangoModelAttrs(aDjangoModelClass: type[Model]):
    """
    Django models contain some class attributes we should avoid stomping when
    we define MyClassOverrides class containers.
    :param aDjangoModelClass: a model class we will be expanding/overriding.
    :return: Returns a list of attributes to ignore when calling setClassOverrides().
    """
    return (
        'Meta',
        '_meta',
        'DoesNotExist',
        'MultipleObjectsReturned',
        f"{aDjangoModelClass.__name__.lower()}_ptr_id",
        f"{aDjangoModelClass.__name__.lower()}_ptr",
    )
#enddef ignoreDjangoModelAttrs

def ignoreDjangoModelFormAttrs(aDjangoModelFormsClass: type[forms.ModelForm]):
    """
    Django Forms based on models contain some class attributes we should avoid stomping when
    we define MyClassOverrides class containers.
    :param aDjangoModelFormsClass: a form model class we will be expanding/overriding.
    :return: Returns a list of attributes to ignore when calling setClassOverrides().
    """
    return (
        'Meta',
        '_meta',
        'base_fields',
        'declared_fields',
        'media',
    )
#enddef ignoreDjangoModelFormAttrs

class ClassOverrideMixinMustBeFirst:
    override_ignore: list  #only define if your overridden obj contains class vars like Django Models.
    myClassType: type[Any]
    origattrs: dict
    on_apply_overrides: Callable  #only define if you have merges rather than overrides.

    @classmethod
    def getOrigClsAttr(cls, attr_name: str):
        return cls.origattrs.get(attr_name)
    #enddef getOrigAttr

    @classmethod
    def setClassOverrides(cls) -> None:
        ignore_attrs = getattr(cls, 'override_ignore', ()) + ('on_apply_overrides',)
        parents = cls.__bases__
        under_cls = parents[-1]
        under_cls.myClassType = under_cls
        under_cls.origattrs = {}
        under_cls.getOrigClsAttr = cls.getOrigClsAttr
        # stuff all mixins into temba_cls, too
        class_list = parents[1:-1] + (cls,)
        for a_class in class_list:
            for name in a_class.__dict__:
                if not name.startswith("__") and name != 'override_ignore' and name not in ignore_attrs:
                    logger.debug(f"override: set attr {str(under_cls)}.{name} to {getattr(a_class, name)}")
                    orig_attr = getattr(under_cls, name, None)
                    under_cls.origattrs.update({name: orig_attr})
                    setattr(under_cls, name, getattr(a_class, name))
                #endif
            #endfor each attr
        #endfor each parent
        if getattr(cls, 'on_apply_overrides', None) and callable(getattr(cls, 'on_apply_overrides')):
            cls.on_apply_overrides()
        #endif
    #enddef setClassOverrides

#endclass ClassOverrideMixinMustBeFirst
