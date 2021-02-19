from formtools.wizard.storage.base import BaseStorage
from formtools.wizard.storage.exceptions import NoFileStorageConfigured
from django.core.files.uploadedfile import UploadedFile
import six

class CustomSessionStorage(BaseStorage):
    """
    Customize Session Storage to handle multiple files upload
    """
    def __init__(self, *args, **kwargs):
        super(CustomSessionStorage, self).__init__(*args, **kwargs)
        if self.prefix not in self.request.session:
            self.init_data()

    def _get_data(self):
        self.request.session.modified = True
        return self.request.session[self.prefix]

    def _set_data(self, value):
        self.request.session[self.prefix] = value
        self.request.session.modified = True

    data = property(_get_data, _set_data)

    def reset(self):
        # Store unused temporary file names in order to delete them
        # at the end of the response cycle through a callback attached in
        # `update_response`.
        wizard_files = self.data[self.step_files_key]
        for step_files in six.itervalues(wizard_files):
            for field_dict in six.itervalues(step_files):
                for step_file in field_dict:
                    self._tmp_files.append(step_file['tmp_name'])
        self.init_data()

    def get_step_files(self, step):
        wizard_files = self.data[self.step_files_key].get(step, {})

        if wizard_files and not self.file_storage:
            raise NoFileStorageConfigured(
                "You need to define 'file_storage' in your "
                "wizard view in order to handle file uploads.")

        files = {}
        for key in wizard_files.keys():
            files[key] = {}
            uploaded_file_array = []
            for field_dict in wizard_files.get(key, []):
                field_dict = field_dict.copy()
                tmp_name = field_dict.pop('tmp_name')
                if (step, key, field_dict['name']) not in self._files:
                    self._files[(step, key, field_dict['name'])] = UploadedFile(
                        file=self.file_storage.open(tmp_name), **field_dict)
                uploaded_file_array.append(self._files[(step, key, field_dict['name'])])
            files[key] = uploaded_file_array

        return files or None

    def set_step_files(self, step, files):
        if files and not self.file_storage:
            raise NoFileStorageConfigured(
                "You need to define 'file_storage' in your "
                "wizard view in order to handle file uploads.")

        if step not in self.data[self.step_files_key]:
            self.data[self.step_files_key][step] = {}

        for key in files.keys():
            self.data[self.step_files_key][step][key] = []
            for field_file in files.getlist(key):
                tmp_filename = self.file_storage.save(field_file.name, field_file)
                file_dict = {
                    'tmp_name': tmp_filename,
                    'name': field_file.name,
                    'content_type': field_file.content_type,
                    'size': field_file.size,
                    'charset': field_file.charset
                }
                self.data[self.step_files_key][step][key].append(file_dict)