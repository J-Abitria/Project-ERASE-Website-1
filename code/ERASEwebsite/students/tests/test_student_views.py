import tempfile
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from students.models import Student


class StudentViewsTests(TestCase):
    """Unit tests for StudentDatabaseView (GET filtering, and POST insertions/bulk-adds/deletions)."""

    def setUp(self):
        self.client = Client()
        self.url = reverse('pages:studentdb')

        self.normal_user = User.objects.create_user(username="normal", password="Password123!")
        self.staff_user = User.objects.create_user(username="staff", password="Password123!", is_staff=True)
        self.superuser = User.objects.create_superuser(username="admin", password="Password123!")

        self.s1 = Student.objects.create(name="Charlie Brown", gender="Male", school="West High")
        self.s2 = Student.objects.create(name="Lucy Van Pelt", gender="Female", school="East High")

    def test_studentdb_view_get_unfiltered(self):
        """GET request without query params displays all students."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'studentdb.html')
        self.assertEqual(len(response.context['students']), 2)
        self.assertContains(response, "Charlie Brown")
        self.assertContains(response, "Lucy Van Pelt")

    def test_studentdb_view_get_with_filters(self):
        """GET request with query params filters the displayed students."""
        response = self.client.get(self.url, {'search': 'Charlie', 'gender': 'Male', 'school': 'West'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['students']), 1)
        self.assertContains(response, "Charlie Brown")
        self.assertNotContains(response, "Lucy Van Pelt")

    def test_studentdb_post_unauthenticated_or_normal_user_forbidden(self):
        """Normal authenticated user and anonymous users cannot POST to modify student records."""
        # Anonymous POST
        anon_res = self.client.post(self.url, {'action': 'add', 'name': 'Hacker'})
        self.assertEqual(anon_res.status_code, 403)

        # Normal user POST
        self.client.login(username="normal", password="Password123!")
        user_res = self.client.post(self.url, {'action': 'add', 'name': 'Hacker'})
        self.assertEqual(user_res.status_code, 403)

        self.assertFalse(Student.objects.filter(name="Hacker").exists())

    def test_studentdb_post_add_student_by_staff(self):
        """Staff user can add a single student."""
        self.client.login(username="staff", password="Password123!")
        post_data = {
            'action': 'add',
            'name': 'Linus Van Pelt',
            'gender': 'Male',
            'school': 'East High',
        }
        response = self.client.post(self.url, post_data)
        self.assertRedirects(response, self.url)

        self.assertTrue(Student.objects.filter(name="Linus Van Pelt").exists())
        linus = Student.objects.get(name="Linus Van Pelt")
        self.assertEqual(linus.gender, "Male")
        self.assertEqual(linus.school, "East High")

    def test_studentdb_post_add_student_with_photo(self):
        """Staff user can add a student with an uploaded photo."""
        with tempfile.TemporaryDirectory() as temp_media:
            with override_settings(MEDIA_ROOT=temp_media):
                self.client.login(username="staff", password="Password123!")
                test_image = SimpleUploadedFile(
                    name="avatar.jpg",
                    content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
                    content_type="image/jpeg",
                )
                post_data = {
                    'action': 'add',
                    'name': 'Snoopy Dog',
                    'gender': 'Male',
                    'school': 'Canine Academy',
                    'photo': test_image,
                }
                response = self.client.post(self.url, post_data)
                self.assertRedirects(response, self.url)

                snoopy = Student.objects.get(name="Snoopy Dog")
                self.assertTrue(bool(snoopy.photo))

    def test_studentdb_post_add_student_missing_name_does_nothing(self):
        """POST with action 'add' but empty name does not create a record."""
        self.client.login(username="staff", password="Password123!")
        post_data = {
            'action': 'add',
            'name': '',
            'gender': 'Male',
            'school': 'Unknown High',
        }
        response = self.client.post(self.url, post_data)
        self.assertRedirects(response, self.url)
        self.assertEqual(Student.objects.count(), 2)

    def test_studentdb_post_bulk_add_students(self):
        """Staff user can add multiple students via action 'bulk_add'."""
        self.client.login(username="staff", password="Password123!")
        post_data = {
            'action': 'bulk_add',
            'bulk_count': '3',
            'name_0': 'Sally Brown',
            'gender_0': 'Female',
            'school_0': 'West High',
            'name_1': 'Peppermint Patty',
            'gender_1': 'Female',
            'school_1': 'Central High',
            'name_2': 'Marcie Johnson',
            'gender_2': 'Female',
            'school_2': 'Central High',
        }
        response = self.client.post(self.url, post_data)
        self.assertRedirects(response, self.url)

        self.assertEqual(Student.objects.count(), 5)
        self.assertTrue(Student.objects.filter(name="Sally Brown").exists())
        self.assertTrue(Student.objects.filter(name="Peppermint Patty").exists())
        self.assertTrue(Student.objects.filter(name="Marcie Johnson").exists())

    def test_studentdb_post_bulk_add_invalid_count(self):
        """POST with action 'bulk_add' and non-numeric count handles gracefully."""
        self.client.login(username="staff", password="Password123!")
        post_data = {
            'action': 'bulk_add',
            'bulk_count': 'invalid_number',
            'name_0': 'Never Added',
        }
        response = self.client.post(self.url, post_data)
        self.assertRedirects(response, self.url)
        self.assertEqual(Student.objects.count(), 2)

    def test_studentdb_post_delete_student(self):
        """Staff user can delete a student by name."""
        self.client.login(username="staff", password="Password123!")
        
        student = Student.objects.get(name="Charlie Brown")
        post_data = {
            'action': 'delete',
            'student_id': student.id,
        }
        response = self.client.post(self.url, post_data)
        self.assertRedirects(response, self.url)

        self.assertFalse(Student.objects.filter(name="Charlie Brown").exists())
        self.assertEqual(Student.objects.count(), 1)

    def test_studentdb_post_delete_student_empty_name(self):
        """POST with action 'delete' but no student_name does nothing."""
        self.client.login(username="staff", password="Password123!")
        post_data = {
            'action': 'delete',
            'student_name': '',
        }
        response = self.client.post(self.url, post_data)
        self.assertRedirects(response, self.url)
        self.assertEqual(Student.objects.count(), 2)

