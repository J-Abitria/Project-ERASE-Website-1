from django.shortcuts import render, redirect
from django.views import View
from django.core.exceptions import PermissionDenied
from .models import Student


class StudentDatabaseView(View):
    """Class-Based View for viewing and managing the student database."""
    template_name = 'studentdb.html'

    def get(self, request, *args, **kwargs):
        search = request.GET.get('search', '').strip()
        gender = request.GET.get('gender', '').strip()
        school = request.GET.get('school', '').strip()

        students = Student.objects.apply_filters(
            search=search or None,
            gender=gender or None,
            school=school or None
        )

        return render(request, self.template_name, {
            'students': students,
            'search': search,
            'gender': gender,
            'school': school,
        })

    def post(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied

        action = request.POST.get('action')
        if action == 'add':
            self._add_student(request)
        elif action == 'bulk_add':
            self._bulk_add_students(request)
        elif action == 'delete':
            self._delete_student(request)

        return redirect('pages:studentdb')

    def _add_student(self, request):
        name = request.POST.get('name')
        gender = request.POST.get('gender')
        school = request.POST.get('school')
        photo = request.FILES.get('photo')

        if name:
            Student.objects.create(
                name=name,
                gender=gender,
                school=school,
                photo=photo
            )

    def _bulk_add_students(self, request):
        count_str = request.POST.get('bulk_count', '0')
        count = int(count_str) if count_str.isdigit() else 0

        for i in range(count):
            name = request.POST.get(f'name_{i}')
            gender = request.POST.get(f'gender_{i}')
            school = request.POST.get(f'school_{i}')
            photo = request.FILES.get(f'photo_{i}')

            if name:
                Student.objects.create(
                    name=name,
                    gender=gender,
                    school=school,
                    photo=photo
                )

    def _delete_student(self, request):
        student_id = request.POST.get('student_id')
        if student_id:
            Student.objects.filter(pk=student_id).delete()