from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Test, Question, Option, StudentAnswer, GradingScheme
from .forms import RegisterForm, TestForm, QuestionForm, OptionForm, TestCodeForm
from .models import Profile
from django.utils import timezone
import sqlite3
from django.db import IntegrityError
import random
import string
from django.db.models import Prefetch, Avg, Count, Max, Sum
from .utils import generate_unique_code
from django.db.models import Q


def index(request):
    context = {}
    if request.user.is_authenticated:
        if request.user.profile.role == 'student':
            # Для студентов показываем доступные активные тесты
            tests = Test.objects.filter(is_active=True).annotate(
                student_count=Count('studentanswer__user', distinct=True)
            )[:3]  # Показываем только 3 последних теста
            context['tests'] = tests
            context['user_role'] = 'student'
        elif request.user.profile.role == 'teacher':
            # Для преподавателей показываем их последние тесты
            tests = Test.objects.filter(creator=request.user).annotate(
                student_count=Count('studentanswer__user', distinct=True)
            ).order_by('-id')[:3]
            context['tests'] = tests
            context['user_role'] = 'teacher'
    return render(request, 'main/index.html', context)


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'main/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def create_test(request):
    if request.user.profile.role != 'teacher':
        return redirect('index')

    if request.method == 'POST':
        form = TestForm(request.POST)
        # Обновляем queryset для load_template при POST-запросе
        form.fields['load_template'].queryset = GradingScheme.objects.filter(
            creator=request.user
        ).exclude(name="Мои настройки")

        if form.is_valid():
            # Проверяем, выбран ли шаблон
            load_template = form.cleaned_data['load_template']
            if load_template:
                # Используем параметры из шаблона
                grading_scheme = GradingScheme(
                    creator=request.user,
                    grading_type=load_template.grading_type,
                    threshold_2=load_template.threshold_2,
                    threshold_3=load_template.threshold_3,
                    threshold_4=load_template.threshold_4,
                    threshold_5=load_template.threshold_5,
                    pass_threshold=load_template.pass_threshold,
                    name="Мои настройки"
                )
            else:
                # Создаём новую схему оценивания из введённых данных
                grading_scheme = GradingScheme(
                    creator=request.user,
                    grading_type=form.cleaned_data['grading_type'],
                    threshold_2=form.cleaned_data['threshold_2'],
                    threshold_3=form.cleaned_data['threshold_3'],
                    threshold_4=form.cleaned_data['threshold_4'],
                    threshold_5=form.cleaned_data['threshold_5'],
                    pass_threshold=form.cleaned_data['pass_threshold']
                )
            # Если отмечено "Сохранить как шаблон", изменяем имя
            if form.cleaned_data['save_as_template']:
                grading_scheme.name = form.cleaned_data['template_name'] or f"Шаблон_{request.user.username}_{timezone.now().strftime('%Y%m%d')}"
            grading_scheme.save()

            # Создаём тест
            test = form.save(commit=False)
            test.creator = request.user
            test.grading_scheme = grading_scheme
            test.save()

            question_index = 0
            while True:
                question_key = f'question_{question_index}_text'
                if question_key not in request.POST:
                    break
                question_text = request.POST.get(question_key)
                if question_text:
                    has_image = request.POST.get(f'question_{question_index}_has_image') == 'on'
                    image = request.FILES.get(f'question_{question_index}_image') if has_image else None
                    print(f"Creating question {question_index} with image: {image}")
                    question = Question.objects.create(
                        test=test,
                        text=question_text,
                        is_text_answer=request.POST.get(f'question_{question_index}_is_text_answer') == 'on',
                        is_multiple_choice=request.POST.get(f'question_{question_index}_is_multiple_choice') == 'on',
                        correct_text_answer=request.POST.get(f'question_{question_index}_correct_text_answer', ''),
                        image=image
                    )
                    if not question.is_text_answer:
                        option_index = 0
                        options_created = []
                        while True:
                            option_key = f'question_{question_index}_option_{option_index}_text'
                            if option_key not in request.POST:
                                break
                            option_text = request.POST.get(option_key)
                            is_correct = request.POST.get(f'question_{question_index}_option_{option_index}_is_correct') == 'on'
                            options_created.append(Option(
                                question=question,
                                text=option_text or f"Вариант {option_index + 1}",
                                is_correct=is_correct
                            ))
                            option_index += 1
                        if options_created:
                            Option.objects.bulk_create(options_created)
                            print(f"Saved {len(options_created)} options for question {question_index}")
                            if not any(opt.is_correct for opt in options_created):
                                options_created[0].is_correct = True
                                options_created[0].save()
                question_index += 1

            return redirect('test_detail', test_id=test.id)
    else:
        form = TestForm()
        form.fields['load_template'].queryset = GradingScheme.objects.filter(
            creator=request.user
        ).exclude(name="Мои настройки")

    return render(request, 'main/test_create.html', {'form': form, 'initial_questions': [{'options': [{} for _ in range(4)]}]})


@login_required
def start_test(request, test_id):
    test = get_object_or_404(Test, pk=test_id)
    if request.user.profile.role != 'student' or not test.is_active:
        return render(request, 'main/error.html', {'message': 'Этот тест сейчас недоступен.'})

    # Проверяем, проходил ли студент тест ранее
    student_answers = StudentAnswer.objects.filter(user=request.user, test=test).exists()
    if student_answers:
        return render(request, 'main/error.html', {
            'message': 'Вы уже проходили этот тест. Повторное прохождение невозможно.'
        })

    test = Test.objects.prefetch_related('questions__options').get(id=test_id)
    return render(request, 'main/test_timer.html', {'test': test})


@login_required
def submit_answers(request, test_id):
    test = get_object_or_404(Test.objects.prefetch_related('questions__options'), pk=test_id)
    if request.user.profile.role != 'student':
        return redirect('index')

    if request.method != 'POST':
        return redirect('start_test', test_id=test.id)

    total_score = 0
    max_possible_score = test.questions.count()
    detailed_results = []
    student_answers = []

    for question in test.questions.all():
        if question.is_text_answer:
            user_answer = request.POST.get(f'answer_{question.id}', '').strip().lower()
            correct_answer = question.correct_text_answer.strip().lower() if question.correct_text_answer else ''
            is_correct = user_answer == correct_answer
            question_score = 1 if is_correct else 0
            student_answers.append(
                StudentAnswer(
                    user=request.user,
                    test=test,
                    question=question,
                    answer_text=user_answer,
                    is_correct=is_correct,
                    score=question_score
                )
            )
        else:
            selected_ids = [int(id) for id in request.POST.getlist(f'answer_{question.id}') if id.isdigit()]
            correct_options = list(question.options.filter(is_correct=True).values_list('id', flat=True))
            correct_selected = len(set(selected_ids) & set(correct_options))
            incorrect_selected = len(set(selected_ids) - set(correct_options))
            if question.is_multiple_choice:
                question_score = max(0, (correct_selected - incorrect_selected)) / len(correct_options) if correct_options else 0
                for option_id in selected_ids:
                    option = Option.objects.get(id=option_id)
                    student_answers.append(
                        StudentAnswer(
                            user=request.user,
                            test=test,
                            question=question,
                            selected_option=option,
                            is_correct=(option.id in correct_options),
                            score=question_score if (option.id in correct_options) else 0
                        )
                    )
            else:
                question_score = 1 if (len(selected_ids) == 1 and selected_ids[0] in correct_options) else 0
                if selected_ids:
                    option = Option.objects.get(id=selected_ids[0])
                    student_answers.append(
                        StudentAnswer(
                            user=request.user,
                            test=test,
                            question=question,
                            selected_option=option,
                            is_correct=(option.id in correct_options),
                            score=question_score
                        )
                    )
        total_score += question_score
        detailed_results.append({
            'question': question,
            'score': question_score,
            'is_correct': (question_score == 1),
            'selected_ids': selected_ids,
            'correct_selected': correct_selected,
            'incorrect_selected': incorrect_selected,
            'total_correct': len(correct_options),
            'answer_text': user_answer if question.is_text_answer else None
        })

    fully_correct = sum(1 for result in detailed_results if result['score'] == 1)
    StudentAnswer.objects.bulk_create(student_answers)
    final_percentage = round((total_score / max_possible_score) * 100) if max_possible_score > 0 else 0

    # Определяем оценку на основе схемы
    grade = 'Зачёт' if final_percentage >= 60 else 'Незачёт'
    if test.grading_scheme:
        if test.grading_scheme.grading_type == 'differentiated':
            if final_percentage >= test.grading_scheme.threshold_5:
                grade = "5"
            elif final_percentage >= test.grading_scheme.threshold_4:
                grade = "4"
            elif final_percentage >= test.grading_scheme.threshold_3:
                grade = "3"
            elif final_percentage >= test.grading_scheme.threshold_2:
                grade = "2"
            else:
                grade = "Незачёт"
        else:
            grade = "Зачёт" if final_percentage >= test.grading_scheme.pass_threshold else "Незачёт"

    return render(request, 'main/result.html', {
        'test': test,
        'correct': total_score,
        'fully_correct': fully_correct,
        'total': max_possible_score,
        'score': final_percentage,
        'grade': grade,
        'incorrect': max_possible_score - total_score,
        'results': detailed_results,
        'answers_by_question': {
            answer.question_id: answer
            for answer in StudentAnswer.objects.filter(user=request.user, test=test)
        }
    })


@login_required
def test_result(request, test_id):
    test = get_object_or_404(Test, pk=test_id)
    student_answers = StudentAnswer.objects.filter(user=request.user, test=test).select_related('question', 'selected_option')
    total_questions_count = test.questions.count()
    total_score = 0
    fully_correct = 0
    results = []

    for question in test.questions.all():
        answers = student_answers.filter(question=question)
        if question.is_text_answer:
            answer = answers.first()
            question_score = answer.score if answer and answer.is_correct else 0
            result = {
                'question': question,
                'score': question_score,
                'is_correct': question_score == 1,
                'answer_text': answer.answer_text if answer else None,
            }
        else:
            selected_ids = [answer.selected_option.id for answer in answers if answer.selected_option]
            correct_options = list(question.options.filter(is_correct=True).values_list('id', flat=True))
            correct_selected = len(set(selected_ids) & set(correct_options))
            incorrect_selected = len(set(selected_ids) - set(correct_options))
            if question.is_multiple_choice:
                question_score = max(0, (correct_selected - incorrect_selected)) / len(correct_options) if correct_options else 0
            else:
                question_score = 1 if selected_ids and selected_ids[0] in correct_options else 0
            result = {
                'question': question,
                'score': question_score,
                'is_correct': question_score == 1,
                'selected_ids': selected_ids,
                'correct_selected': correct_selected,
                'incorrect_selected': incorrect_selected,
                'total_correct': len(correct_options),
            }
        total_score += question_score
        if question_score == 1:
            fully_correct += 1
        results.append(result)

    score = round((total_score / total_questions_count) * 100) if total_questions_count > 0 else 0
    grade = 'Зачёт' if score >= 60 else 'Незачёт'
    if test.grading_scheme:
        if test.grading_scheme.grading_type == 'differentiated':
            if score >= test.grading_scheme.threshold_5:
                grade = "5"
            elif score >= test.grading_scheme.threshold_4:
                grade = "4"
            elif score >= test.grading_scheme.threshold_3:
                grade = "3"
            elif score >= test.grading_scheme.threshold_2:
                grade = "2"
            else:
                grade = "Незачёт"
        else:
            grade = "Зачёт" if score >= test.grading_scheme.pass_threshold else "Незачёт"

    return render(request, 'main/test_result.html', {
        'test': test,
        'correct': total_score,
        'fully_correct': fully_correct,
        'total': total_questions_count,
        'score': score,
        'grade': grade,
        'results': results,
        'answers_by_question': {answer.question_id: answer for answer in student_answers},
    })


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            user = form.save()
            if hasattr(user, 'profile'):
                user.profile.role = role
                user.profile.save()
            else:
                Profile.objects.create(user=user, role=role)
            login(request, user)
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'main/register.html', {'form': form})


@login_required
def enter_test_code(request):
    form = TestCodeForm()
    error = None
    if request.method == 'POST':
        form = TestCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code'].strip().upper()
            try:
                test = Test.objects.get(code=code)
                if not test.is_active:
                    return render(request, 'main/error.html', {'message': 'Этот тест сейчас недоступен.'})
                return redirect('start_test', test_id=test.id)
            except Test.DoesNotExist:
                error = "Тест с таким кодом не найден."
    return render(request, 'main/enter_test_code.html', {
        'form': form,
        'error': error
    })


def test_created(request, test_code):
    test = get_object_or_404(Test, code=test_code)
    return render(request, 'main/test_created.html', {'test_code': test_code, 'test': test})


@login_required
def test_detail(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    test = Test.objects.prefetch_related('questions__options').get(id=test_id)
    return render(request, 'main/test_detail.html', {'test': test})


@login_required
def teacher_dashboard(request):
    if request.user.profile.role != 'teacher':
        return redirect('student_dashboard')
    tests = Test.objects.filter(creator=request.user).annotate(
        student_count=Count('studentanswer__user', distinct=True),
        avg_score=Avg('studentanswer__score') * 100
    )
    return render(request, 'main/teacher_dashboard.html', {
        'tests': tests,
    })


@login_required
def student_dashboard(request):
    if request.user.profile.role != 'student':  # Исправлено на 'student'
        return redirect('teacher_dashboard')
    test_attempts = StudentAnswer.objects.filter(user=request.user).values(
        'test__id', 'test__title'
    ).annotate(
        max_id=Max('id')  # Сортировка по id
    ).order_by('-max_id')
    total_tests = test_attempts.count()
    processed_attempts = []
    avg_score = 0
    if test_attempts:
        for attempt in test_attempts:
            test = Test.objects.get(id=attempt['test__id'])
            student_answers = StudentAnswer.objects.filter(user=request.user, test=test).select_related('question', 'selected_option')
            total_questions_count = test.questions.count()
            total_score = 0
            for question in test.questions.all():
                answers = student_answers.filter(question=question)
                if question.is_text_answer:
                    answer = answers.first()
                    question_score = answer.score if answer and answer.is_correct else 0
                else:
                    selected_ids = [answer.selected_option.id for answer in answers if answer.selected_option]
                    correct_options = list(question.options.filter(is_correct=True).values_list('id', flat=True))
                    correct_selected = len(set(selected_ids) & set(correct_options))
                    incorrect_selected = len(set(selected_ids) - set(correct_options))
                    if question.is_multiple_choice:
                        question_score = max(0, (correct_selected - incorrect_selected)) / len(correct_options) if correct_options else 0
                    else:
                        question_score = 1 if selected_ids and selected_ids[0] in correct_options else 0
                total_score += question_score
            percentage = round((total_score / total_questions_count) * 100) if total_questions_count > 0 else 0
            processed_attempts.append({
                'test__id': attempt['test__id'],
                'test__title': attempt['test__title'],
                'total_score': percentage,
                'max_id': attempt['max_id'],
                'grade': 'Зачёт' if percentage >= 60 else 'Незачёт'
            })
        avg_score = sum(attempt['total_score'] for attempt in processed_attempts) / total_tests if total_tests > 0 else 0
    return render(request, 'main/student_dashboard.html', {
        'test_attempts': processed_attempts,
        'total_tests': total_tests,
        'avg_score': round(avg_score, 2),
    })

@login_required
def toggle_test_active(request, test_id):
    if request.user.profile.role != 'teacher':
        return redirect('index')
    test = get_object_or_404(Test, id=test_id, creator=request.user)
    test.is_active = not test.is_active
    test.save()
    return redirect('teacher_dashboard')


@login_required
def test_results(request, test_id):
    if request.user.profile.role != 'teacher':
        return redirect('index')
    test = get_object_or_404(Test, id=test_id, creator=request.user)
    results = StudentAnswer.objects.filter(test=test).values(
        'user__username'
    ).annotate(
        total_score=Avg('score') * 100,
        attempt_date=Max('id')  # Используем Max('id'), как в student_dashboard
    ).order_by('-attempt_date')
    # Добавляем grade для каждого результата
    results = [
        {
            'user__username': result['user__username'],
            'total_score': result['total_score'],
            'attempt_date': result['attempt_date'],
            'grade': 'Зачёт' if result['total_score'] >= 60 else 'Незачёт'
        }
        for result in results
    ]
    return render(request, 'main/test_results.html', {
        'test': test,
        'results': results,
    })


@login_required
def generate_custom_test(request):
    if request.user.profile.role != 'student':
        return redirect('index')

    # Получаем все последние ответы студента с неправильными ответами
    incorrect_answers = StudentAnswer.objects.filter(
        Q(user=request.user) & (Q(is_correct=False) | Q(score__lt=1))
    ).order_by('-id')[:10]

    # Создаём словарь для хранения уникальных вопросов, выбираем последний ответ по id
    question_ids = {}
    for answer in incorrect_answers:
        question_ids[answer.question_id] = answer

    # Преобразуем в список уникальных вопросов
    incorrect_questions = [answer.question for answer in question_ids.values()]
    num_incorrect = len(incorrect_questions)

    if request.method == 'POST':
        num_questions = int(request.POST.get('num_questions', 5))
        if num_questions < 1 or num_questions > 20:
            return render(request, 'main/generate_custom_test.html', {
                'error': 'Количество вопросов должно быть от 1 до 20.'
            })

        # Проверяем, достаточно ли неправильных вопросов
        if num_incorrect < num_questions:
            return render(request, 'main/generate_custom_test.html', {
                'error': f'Недостаточно неправильных ответов для создания теста. Доступно только {num_incorrect} неправильных вопроса(ов). Пройдите больше тестов или выберите меньшее количество вопросов.'
            })

        # Создаём новый тест
        test = Test.objects.create(
            title=f"Персонализированный тест для {request.user.username}",
            description="Этот тест создан на основе ваших последних неправильных ответов, чтобы помочь вам улучшить слабые места.",
            creator=request.user,
            time_limit=10,
            is_active=True,
            is_personalized=True
        )

        # Копируем вопросы в новый тест
        for question in incorrect_questions[:num_questions]:
            new_question = Question.objects.create(
                test=test,
                text=question.text,
                is_text_answer=question.is_text_answer,
                is_multiple_choice=question.is_multiple_choice,
                correct_text_answer=question.correct_text_answer,
                image=question.image
            )
            if not question.is_text_answer:
                for option in question.options.all():
                    Option.objects.create(
                        question=new_question,
                        text=option.text,
                        is_correct=option.is_correct
                    )

        # Перенаправляем студента на прохождение теста
        return redirect('start_test', test_id=test.id)

    return render(request, 'main/generate_custom_test.html', {})
