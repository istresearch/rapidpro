import inspect
import logging
from typing import Any, Callable


logger = logging.getLogger()

class MonkeyPatcher:
    """
    Refactored from an earlier attempt so that we are explicitly NOT part of the class inheritance chain in order to
    avoid Django magically detecting our model patch class as a legitimate model class and such.
    Additionally, we avoid the inherited attributes that muck up the waters for what should be overriden or not.
    Just descend from this class (at minimum), assign `patch_class`, define your mixins and vars/methods. Then call
    your new class' applyPatches() method in the apps.py ready() method.
    """
    patch_class: type[Any]
    patch_attrs: dict
    patch_ignore: list  # only define if your overridden obj contains class vars like Django Models.
    on_apply_patches: Callable  # only need to define if you have merges rather than overrides.

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
    def applyPatches(cls) -> None:
        ignore_attrs = getattr(cls, 'patch_ignore', ()) + (
                'patch_class', 'patch_attrs', 'patch_ignore', 'on_apply_patches',
                'getOrigClsAttr', 'inheritors', 'patchClassMethod',
                'applyPatches', 'applyPatches',
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
    #enddef applyPatches

#endclass MonkeyPatcher
