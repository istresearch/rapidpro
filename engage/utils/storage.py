import os
import re

from django.contrib.staticfiles.utils import matches_patterns
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

# class ManifestStaticFilesStorage is used to debug issues with WhiteNoise (to determine if WN is the issue)
#from django.contrib.staticfiles.storage import ManifestStaticFilesStorage as BaseStaticFilesStorage
from whitenoise.storage import (
    CompressedManifestStaticFilesStorage as BaseStaticFilesStorage,
    MissingFileError,
)


class EngageStaticFilesStorage(BaseStaticFilesStorage):
    """
    Library, framework, and ancestor assets in tests may be malformed or missing.
    However, these assets are not used, so we need to ignore them during
    static file processing/compression. Even if the `self.manifest_strict` is
    set to False a used resource that we don't care about (js .map files) still
    generates an exception. Tweak a few of the methods to ignore
    malformed/missing files we do not care about in production.
    """
    manifest_strict = False
    ignore_ext_list = ('.map',)

    # known problems that can be ignored (e.g. lib that cannot be fixed/patched)
    ignore_utf8_error_list = (
        '*/node-uuid/lib/sha1-browser.js'
    )

    # def save_manifest(self):
    #     import json
    #     print(json.dumps(sorted(self.hashed_files.items())))
    #     super().save_manifest()

    def post_process(self, *args, **kwargs):
        files = super().post_process(*args, **kwargs)
        for name, hashed_name, processed in files:
            if isinstance(processed, MissingFileError) or isinstance(processed, ValueError):
                re_err_msg = re.compile(r"^The file '(.+)' could not be found")
                match = re_err_msg.search(processed.args[0])
                if match:
                    file_name = match.group(1)
                    #print(file_name)
                    file_ext = os.path.splitext(os.path.basename(file_name))[1]
                    #print(file_ext)
                    file_paths = os.path.dirname(file_name).split(os.sep)
                    #print(file_paths)
                    if file_ext in self.ignore_ext_list or 'test' in file_paths:
                        print(f"  ignoring missing '{file_name}' for '{name}'")
                        processed = True
                    #endif ext is one we ignore
                #endif match found in exception msg
            #endif MissingFileError
            if isinstance(processed, Exception):
                print(f"  EX on '{name}': {processed}")
            elif processed:
                print(f"processed '{name}'")
            else:
                print(f" NOT proc '{name}'")
            #endif
            yield name, hashed_name, processed
        #endfor
    #enddef post_process

    def decode_utf8_mode(self, path: str, name: str) -> str:
        result = 'strict'
        if matches_patterns(name, self.ignore_utf8_error_list):
            result = 'ignore'
        elif matches_patterns(path + os.sep + name, self.ignore_utf8_error_list):
            result = 'ignore'
        return result
    #enddef decode_utf8_mode

    def _post_process(self, paths, adjustable_paths, hashed_files):
        """
        Overriding from Django staticfiles/storage.py because utf-8 decode fail
        does _not_ give you which @*(@* file actually tossed the exception.
        """
        # Sort the files by directory level
        def path_level(name):
            return len(name.split(os.sep))

        for name in sorted(paths, key=path_level, reverse=True):
            try:
                substitutions = True
                # use the original, local file, not the copied-but-unprocessed
                # file, which might be somewhere far away, like S3
                storage, path = paths[name]
                with storage.open(path) as original_file:
                    cleaned_name = self.clean_name(name)
                    hash_key = self.hash_key(cleaned_name)

                    # generate the hash with the original content, even for
                    # adjustable files.
                    if hash_key not in hashed_files:
                        hashed_name = self.hashed_name(name, original_file)
                    else:
                        hashed_name = hashed_files[hash_key]

                    # then get the original's file content..
                    if hasattr(original_file, "seek"):
                        original_file.seek(0)

                    hashed_file_exists = self.exists(hashed_name)
                    processed = False

                    # ..to apply each replacement pattern to the content
                    if name in adjustable_paths:
                        old_hashed_name = hashed_name
                        decode_err_mode = self.decode_utf8_mode(storage, path)
                        content = original_file.read().decode("utf-8", errors=decode_err_mode)
                        for extension, patterns in self._patterns.items():
                            if matches_patterns(path, (extension,)):
                                for pattern, template in patterns:
                                    converter = self.url_converter(
                                        name, hashed_files, template
                                    )
                                    try:
                                        content = pattern.sub(converter, content)
                                    except ValueError as exc:
                                        yield name, None, exc, False
                        if hashed_file_exists:
                            self.delete(hashed_name)
                        # then save the processed result
                        content_file = ContentFile(content.encode())
                        if self.keep_intermediate_files:
                            # Save intermediate file for reference
                            self._save(hashed_name, content_file)
                        hashed_name = self.hashed_name(name, content_file)

                        if self.exists(hashed_name):
                            self.delete(hashed_name)

                        saved_name = self._save(hashed_name, content_file)
                        hashed_name = self.clean_name(saved_name)
                        # If the file hash stayed the same, this file didn't change
                        if old_hashed_name == hashed_name:
                            substitutions = False
                        processed = True

                    if not processed:
                        # or handle the case in which neither processing nor
                        # a change to the original file happened
                        if not hashed_file_exists:
                            processed = True
                            saved_name = self._save(hashed_name, original_file)
                            hashed_name = self.clean_name(saved_name)

                    # and then set the cache accordingly
                    hashed_files[hash_key] = hashed_name

                    yield name, hashed_name, processed, substitutions
            except Exception as ex:
                storage: FileSystemStorage
                path: str
                storage, path = paths[name]
                raise Exception(f"'{storage.location}/{path}' caused {ex}") from ex
            #endtry
        #endfor each filepath
    #enddef _post_process

#endclass EngageStaticFilesStorage
