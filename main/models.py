from django.db import models
from django.contrib.auth.models import User
import uuid
from .utils import generate_unique_code


class GradingScheme(models.Model):
    GRADING_TYPE_CHOICES = [
        ('differentiated', 'Дифференцированное'),
        ('non_differentiated', 'Недифференцированное'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default="Мои настройки")  # Название шаблона
    grading_type = models.CharField(max_length=20, choices=GRADING_TYPE_CHOICES, default='non_differentiated')
    threshold_2 = models.IntegerField(null=True, blank=True, default=40)  # Оценка 2
    threshold_3 = models.IntegerField(null=True, blank=True, default=60)  # Оценка 3
    threshold_4 = models.IntegerField(null=True, blank=True, default=80)  # Оценка 4
    threshold_5 = models.IntegerField(null=True, blank=True, default=90)  # Оценка 5
    pass_threshold = models.IntegerField(null=True, blank=True, default=60)  # Порог "зачёта"

    def __str__(self):
        return f"{self.name} ({self.get_grading_type_display()})"

class Test(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tests')
    code = models.CharField(max_length=10, unique=True, blank=True)
    time_limit = models.IntegerField()
    is_active = models.BooleanField(default=True)
    is_personalized = models.BooleanField(default=False)
    grading_scheme = models.ForeignKey(GradingScheme, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_unique_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    is_text_answer = models.BooleanField(default=False)
    is_multiple_choice = models.BooleanField(default=False)
    correct_text_answer = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)  # Новое поле

    def __str__(self):
        return self.text


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.question.is_multiple_choice and self.is_correct:
            Option.objects.filter(question=self.question).exclude(pk=self.pk).update(is_correct=False)
        super().save(*args, **kwargs)


class StudentAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True)
    answer_text = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    score = models.FloatField(default=0)

    def __str__(self):
        return f"Ответ студента {self.user.username} на вопрос {self.question.text}"


class Profile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('teacher', 'Преподаватель'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
