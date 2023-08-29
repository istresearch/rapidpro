import inspect
import logging
from typing import Any, Callable

from django import forms
from django.db.models import Model


logger = logging.getLogger()

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
    override_ignore: list  # only define if your overridden obj contains class vars like Django Models.
    _super_class: type[Any]
    _super_attrs: dict
    on_apply_overrides: Callable  # only define if you have merges rather than overrides.

    @classmethod
    def getSuperClass(cls):
        return cls._super_class
    #enddef get_super_class

    @classmethod
    def getOrigClsAttr(cls, attr_name: str):
        return cls._super_attrs.get(attr_name)
    #enddef getOrigAttr

    @staticmethod
    def setOrigMethod(under_cls, method_name: str) -> None:
        # child class wonky super() makes this workaround necessary
        setattr(under_cls, 'orig_'+method_name, under_cls.getOrigClsAttr(method_name))
        logger.debug(f"override: set attr {str(under_cls)}.orig_{method_name} to {str(under_cls.getOrigClsAttr(method_name))}")
    #enddef setOrigMethod

    @classmethod
    def setClassOverrides(cls) -> None:
        ignore_attrs = getattr(cls, 'override_ignore', ()) + ('override_ignore', 'on_apply_overrides',)
        parents = cls.__bases__
        under_cls = parents[-1]
        under_cls._super_class = under_cls
        under_cls._super_attrs = {}
        under_cls.getOrigClsAttr = cls.getOrigClsAttr
        # stuff all mixins into temba_cls, too
        class_list = parents[1:-1] if len(parents) > 2 else () + (cls,)
        logger.debug(f"bases= {str(class_list)}")
        for a_class in class_list:
            logger.debug(f"apply overrides from {str(a_class)}")
            override_members = a_class.__dict__
            for name in override_members:
                if not name.startswith("__") and name not in ignore_attrs:
                    logger.debug(f"override: set attr {str(under_cls)}.{name} to {getattr(a_class, name)}")
                    orig_attr = getattr(under_cls, name, None)
                    under_cls._super_attrs.update({name: orig_attr})
                    # provide overridden method a "super_" prefix so that we can easily call it
                    # more-or-less required to use this if overridden method is called by child classes, too.
                    if callable(orig_attr):
                        setattr(under_cls, f"super_{name}", orig_attr)
                    #endif
                    setattr(under_cls, name, getattr(a_class, name))
                #endif
            #endfor each attr
        #endfor each parent
        if getattr(cls, 'on_apply_overrides', None) and callable(getattr(cls, 'on_apply_overrides')):
            logger.debug(f"calling {str(cls)}.on_apply_overrides({under_cls})")
            cls.on_apply_overrides(under_cls)
        #endif
    #enddef setClassOverrides

#endclass ClassOverrideMixinMustBeFirst

class MonkeyPatcher:
    patch_class: type[Any]
    patch_attrs: dict
    on_apply_overrides: Callable  # only define if you have merges rather than overrides.

    @classmethod
    def getOrigClsAttr(cls, attr_name: str):
        return cls.patch_attrs.get(attr_name)
    #enddef getOrigAttr

    @classmethod
    def setClassOverrides(cls) -> None:
        ignore_attrs = ('patch_class', 'patch_attrs', 'on_apply_overrides', 'getOrigClsAttr', 'setClassOverrides',)
        parents = cls.__bases__
        under_cls = cls.patch_class
        under_cls_members = dict(inspect.getmembers(under_cls))
        # stuff all mixins into temba_cls, too
        class_list = parents
        logger.debug(f"bases= {str(class_list)}")
        for a_class in class_list:
            logger.debug(f"apply overrides from {str(a_class)}")
            override_members = dict(inspect.getmembers(a_class))
            for name, memloc in override_members.items():
                if not name.startswith("__") and name not in ignore_attrs and (name not in under_cls_members or memloc != under_cls_members[name]):
                    logger.debug(f"override: set attr {str(under_cls)}.{name} to {getattr(a_class, name)}", extra={
                        'mem_name': name, 'mem_loc': memloc, 'mem_cls': under_cls_members[name] if name in under_cls_members else 'N/A',
                    })
                    orig_attr = getattr(under_cls, name, None)
                    cls.patch_attrs.update({name: orig_attr})
                    # provide overridden method a "super_" prefix so that we can easily call it
                    # more-or-less required to use this if overridden method is called by child classes, too.
                    if callable(orig_attr):
                        setattr(cls, f"super_{name}", orig_attr)
                    #endif
                    setattr(under_cls, name, getattr(a_class, name))
                #endif
            #endfor each class member
        #endfor each parent
        if getattr(cls, 'on_apply_overrides', None) and callable(getattr(cls, 'on_apply_overrides')):
            logger.debug(f"calling {str(cls)}.on_apply_overrides({under_cls})")
            cls.on_apply_overrides(under_cls)
        #endif
    #enddef setClassOverrides

#endclass MonkeyPatcher
