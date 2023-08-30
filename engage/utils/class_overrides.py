import inspect
import logging
import types
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
    """
    Deprecated, use MonkeyPatcher lower down in this file.
    """
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
    """
    I believe this class to be superior to the earlier ClassOverrideMixinMustBeFirst. It is a small shift to being
    explicitly NOT part of the class inheritance chain to avoid Django magically detecting model classes and such.
    Additionally, we avoid the inherited attributes that muck up the waters for what should be overriden or not.
    Just descend from this class (at minimum), assign `patch_class`, define your mixins and vars/methods. Then call
    your new class' setClassOverrides() method in the apps.py ready() method.
    """
    patch_class: type[Any]
    patch_attrs: dict
    patch_ignore: list  # only define if your overridden obj contains class vars like Django Models.
    on_apply_patches: Callable  # only need to define if you have merges rather than overrides.
    on_apply_overrides: Callable  # alias for legacy code

    @classmethod
    def getOrigClsAttr(cls, attr_name: str):
        return cls.patch_attrs.get(attr_name)
    #enddef getOrigAttr

    @staticmethod
    def inheritors(klass: type[Any]) -> set[type[Any]]:
        """
        Retrieves a set of all classes that inherit from the klass arg.
        :param klass: The ancestor class.
        :return: Returns the set of child classes, including all grandchildren.
        """
        subclasses = set()
        work = [klass]
        while work:
            parent = work.pop()
            for child in parent.__subclasses__():
                if child not in subclasses:
                    subclasses.add(child)
                    work.append(child)
                #endif
            #endfor
        #endwhile
        return subclasses
    #enddef inheritors

    @classmethod
    def patchClassMethod(cls, patch_cls, patch_attr):
        """
        Patching class methods is trickier as we need to redo what Python does to create them
        as our patching class is not part of the hierarchy.
        :param patch_cls: the class being patched.
        :param patch_attr: the method being patched as a @classmethod. DO NOT USE @classmethod decorator!
        :return: Returns the descriptor which mimics @classmethod, but using patch method from diff class.
        """
        class _PatchClassMethod(object):
            def __init__(self, method):
                self.method = method

            def __get__(self, obj, obj_type=None):
                return lambda *args, **kw: self.method(patch_cls, *args, **kw)
        #endclass
        return _PatchClassMethod(patch_attr)
    #enddef patchClassMethod

    @classmethod
    def setClassOverrides(cls) -> None:
        ignore_attrs = getattr(cls, 'patch_ignore', ()) + (
                'patch_class', 'patch_attrs', 'patch_ignore',
                'on_apply_patches', 'on_apply_overrides',
                'getOrigClsAttr', 'inheritors', 'patchClassMethod', 'setClassOverrides',
        )
        parents = cls.__bases__
        patch_cls = cls.patch_class
        patch_cls_attrs = dict(inspect.getmembers(patch_cls))
        cls.patch_attrs = {}
        # stuff all mixins into patch_cls, too
        class_list = [parent for parent in parents if parent != MonkeyPatcher] + [cls]
        for a_class in class_list:
            logger.debug(f"apply patches from {str(a_class)}")
            patch_members = dict(inspect.getmembers(a_class))
            for name, mem_loc in patch_members.items():
                if (not (name.startswith("__") and name.endswith("__"))) \
                        and name not in ignore_attrs \
                        and (name not in patch_cls_attrs or mem_loc != patch_cls_attrs[name]):
                    orig_attr = getattr(patch_cls, name, None)
                    cls.patch_attrs.update({name: orig_attr})
                    patch_val = getattr(a_class, name)
                    if inspect.ismethod(orig_attr) and orig_attr.__self__ is patch_cls:
                        patch_attr = cls.patchClassMethod(patch_cls, patch_val)
                        bPatchInheritors = True
                        logger.debug(f"patch: set classmethod {str(patch_cls)}.{name} to {patch_attr}", extra={
                            'attr': name, 'mem_loc': mem_loc, 'mem_cls': patch_cls_attrs[name] if name in patch_cls_attrs else 'N/A',
                        })
                    else:
                        patch_attr = patch_val
                        bPatchInheritors = False
                        logger.debug(f"patch: set attr {str(patch_cls)}.{name} to {patch_attr}", extra={
                            'attr': name, 'mem_loc': mem_loc, 'mem_cls': patch_cls_attrs[name] if name in patch_cls_attrs else 'N/A',
                        })
                    #endif
                    setattr(patch_cls, name, patch_attr)
                    if callable(orig_attr):
                        # provide patched method a "super_" prefix so that we can easily call orig method
                        setattr(patch_cls, f"super_{name}", orig_attr)
                        if bPatchInheritors:
                            patch_cls_inheritors = cls.inheritors(patch_cls)
                            for child_patch_cls in patch_cls_inheritors:
                                child_patch_attr = getattr(child_patch_cls, name, None)
                                # only patch if child inherited parent's method, thus we leave overridden methods alone.
                                if inspect.ismethod(child_patch_attr) and child_patch_attr.__self__ is child_patch_cls:
                                    logger.debug(f"skip patch descendent: {str(child_patch_cls)}.{name} defines their own override class method.")
                                else:
                                    patch_attr = cls.patchClassMethod(child_patch_cls, patch_val)
                                    setattr(child_patch_cls, name, patch_attr)
                                    logger.debug(f"patch descendent: set attr {str(child_patch_cls)}.{name} to {patch_attr}")
                                #endif inheritor defines their own class method
                            #endfor each inheritor
                        #endif bPatchInheritors
                    #endif
                #endif
            #endfor each class member
        #endfor each parent
        if getattr(cls, 'on_apply_patches', None) and callable(getattr(cls, 'on_apply_patches')):
            logger.debug(f"calling {str(cls)}.on_apply_patches({patch_cls})")
            cls.on_apply_patches(patch_cls)
        #endif
        if getattr(cls, 'on_apply_overrides', None) and callable(getattr(cls, 'on_apply_overrides')):
            logger.debug(f"calling {str(cls)}.on_apply_overrides({patch_cls})")
            cls.on_apply_overrides(patch_cls)
        #endif
    #enddef setClassOverrides

#endclass MonkeyPatcher
