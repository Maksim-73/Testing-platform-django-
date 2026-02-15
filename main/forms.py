from django import forms
from django.contrib.auth.models import User
from .models import Test, Question, Option, Profile, GradingScheme

# Форма для регистрации нового пользователя
class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Подтверждение пароля")
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, label="Роль")

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Применяем класс form-control ко всем текстовым и email полям
        for field_name, field in self.fields.items():
            if isinstance(field, (forms.CharField, forms.EmailField)):
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name == 'role':  # Специально для ChoiceField (role)
                field.widget.attrs.update({'class': 'form-select'})

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            user.profile.role = self.cleaned_data["role"]
            user.profile.save()
        return user

# Форма для создания теста
class TestForm(forms.ModelForm):
    grading_type = forms.ChoiceField(choices=GradingScheme.GRADING_TYPE_CHOICES, label="Тип оценивания")
    threshold_2 = forms.IntegerField(required=False, label="Порог для оценки 2", initial=40)
    threshold_3 = forms.IntegerField(required=False, label="Порог для оценки 3", initial=60)
    threshold_4 = forms.IntegerField(required=False, label="Порог для оценки 4", initial=80)
    threshold_5 = forms.IntegerField(required=False, label="Порог для оценки 5", initial=90)
    pass_threshold = forms.IntegerField(required=False, label="Порог для зачёта", initial=60)
    save_as_template = forms.BooleanField(required=False, label="Сохранить как шаблон")
    template_name = forms.CharField(max_length=255, required=False, label="Название шаблона")
    load_template = forms.ModelChoiceField(
        queryset=GradingScheme.objects.none(),
        required=False,
        label="Загрузить шаблон",
        empty_label="Выберите шаблон (необязательно)"
    )

    class Meta:
        model = Test
        fields = ['title', 'description', 'time_limit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Применяем класс form-control ко всем полям
        for field_name, field in self.fields.items():
            if isinstance(field, (forms.CharField, forms.IntegerField, forms.ChoiceField, forms.ModelChoiceField)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field, forms.BooleanField):
                field.widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()
        grading_type = cleaned_data.get('grading_type')
        pass_threshold = cleaned_data.get('pass_threshold')
        load_template = cleaned_data.get('load_template')

        # Если используется шаблон, поле pass_threshold не обязательно
        if load_template:
            return cleaned_data

        # Иначе применяем стандартную валидацию
        if grading_type == 'non_differentiated' and pass_threshold is None:
            self.add_error(None, "Порог для зачёта должен быть задан.")
        return cleaned_data

# Форма для создания вопроса
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'is_text_answer', 'is_multiple_choice', 'correct_text_answer']
        widgets = {
            'correct_text_answer': forms.TextInput(attrs={
                'placeholder': 'Правильный текстовый ответ',
                'class': 'correct-text-answer-field'
            }),
        }

# Форма для создания вариантов ответа
class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ['text', 'is_correct']

class TestCodeForm(forms.Form):
    code = forms.CharField(label='Введите код теста', max_length=10)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Применяем класс form-control ко всем текстовым полям
        for field_name, field in self.fields.items():
            if isinstance(field, forms.CharField):
                field.widget.attrs.update({'class': 'form-control'})