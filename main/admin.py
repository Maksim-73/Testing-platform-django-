


from django.contrib import admin
from django.contrib.auth.models import User  # Стандартный импорт
from .models import Test, Question, Option, StudentAnswer
from .models import Profile

# admin.site.register(User)  # Не нужно создавать UserAdmin
admin.site.register(Test)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(StudentAnswer)

admin.site.register(Profile)

