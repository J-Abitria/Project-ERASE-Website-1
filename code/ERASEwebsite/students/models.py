from django.db import models


class StudentQuerySet(models.QuerySet):
    def search(self, query):
        if query:
            return self.filter(name__icontains=query)
        return self

    def filter_gender(self, gender):
        if gender:
            return self.filter(gender=gender)
        return self

    def filter_school(self, school):
        if school:
            return self.filter(school__icontains=school)
        return self

    def apply_filters(self, search=None, gender=None, school=None):
        return (
            self.search(search)
            .filter_gender(gender)
            .filter_school(school)
        )


class StudentManager(models.Manager):
    def get_queryset(self):
        return StudentQuerySet(self.model, using=self._db)

    def apply_filters(self, *args, **kwargs):
        return self.get_queryset().apply_filters(*args, **kwargs)


class Student(models.Model):
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    school = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='students', blank=True, null=True)

    objects = StudentManager()

    class Meta:
        db_table = 'pages_student'

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.photo:
            self.photo.storage.delete(self.photo.name)
        super().delete(*args, **kwargs)
