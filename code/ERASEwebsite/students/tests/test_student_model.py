import tempfile
import os
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from students.models import Student


class StudentModelTests(TestCase):
    """Unit tests for Student model operations (creation, editing, deletion, and media cleanup)."""

    def setUp(self):
        self.student = Student.objects.create(
            name="Alice Smith",
            gender="Female",
            school="Lincoln High School",
        )

    def test_student_str_representation(self):
        """__str__ should return the student's name."""
        self.assertEqual(str(self.student), "Alice Smith")

    def test_student_edit(self):
        """Editing student attributes should persist changes in the database."""
        self.student.name = "Alice Johnson"
        self.student.gender = "Female"
        self.student.school = "Washington High School"
        self.student.save()

        updated = Student.objects.get(pk=self.student.pk)
        self.assertEqual(updated.name, "Alice Johnson")
        self.assertEqual(updated.school, "Washington High School")

    def test_student_deletion_without_photo(self):
        """Deleting a student without a photo deletes the record without error."""
        student_id = self.student.pk
        self.student.delete()
        self.assertFalse(Student.objects.filter(pk=student_id).exists())

    def test_student_deletion_with_photo_cleanup(self):
        """Deleting a student with a photo removes the file from the filesystem."""
        with tempfile.TemporaryDirectory() as temp_media:
            with override_settings(MEDIA_ROOT=temp_media):
                test_image = SimpleUploadedFile(
                    name="student_test.jpg",
                    content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
                    content_type="image/jpeg",
                )
                student = Student.objects.create(
                    name="Photo Student",
                    gender="Male",
                    school="Roosevelt High School",
                    photo=test_image,
                )
                file_path = student.photo.path
                self.assertTrue(os.path.isfile(file_path))

                # Delete student and verify file removal
                student.delete()
                self.assertFalse(os.path.isfile(file_path))
                self.assertFalse(Student.objects.filter(name="Photo Student").exists())

    def test_student_deletion_when_photo_file_is_missing(self):
        """Deleting a student when the referenced file does not exist on disk handles cleanly."""
        student = Student.objects.create(
            name="Ghost Photo Student",
            gender="Male",
            school="Jefferson High School",
        )
        student.photo = "students/nonexistent_photo.jpg"
        student.save()

        student.delete()
        self.assertFalse(Student.objects.filter(name="Ghost Photo Student").exists())

    def test_student_photo_cleanup_uses_storage_api(self):
        student = Student.objects.create(
            name="Remote Photo Student",
            gender="Female",
            school="Lincoln High School",
            photo="students/remote-photo.jpg",
        )

        with patch.object(student.photo.storage, 'delete') as storage_delete:
            student.delete()

        storage_delete.assert_called_once_with('students/remote-photo.jpg')
