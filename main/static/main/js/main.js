// Глобальная функция для настройки чекбоксов вариантов
function setupAnswerSelectors(questionContainer) {
    const selectors = questionContainer.querySelectorAll('.correct-answer-selector');
    console.log(`[setupAnswerSelectors] Found ${selectors.length} correct-answer-selectors in question ${questionContainer.dataset.questionIndex}`);
    if (selectors.length === 0) {
        console.warn('[setupAnswerSelectors] No correct-answer-selectors found in question container:', questionContainer.innerHTML.slice(0, 100));
    }
    selectors.forEach(selector => {
        console.log(`[setupAnswerSelectors] Processing checkbox: ${selector.name}, checked: ${selector.checked}, disabled: ${selector.disabled}`);
        selector.removeEventListener('change', (event) => handleCorrectAnswerChange(event.target, questionContainer));
        selector.addEventListener('change', (event) => handleCorrectAnswerChange(event.target, questionContainer));
        console.log(`[setupAnswerSelectors] Attached handler to checkbox: ${selector.name}`);
    });
}

// Глобальная функция управления правильными ответами
function handleCorrectAnswerChange(clickedCheckbox, questionContainer) {
    const multipleChoiceCheckbox = questionContainer.querySelector('.multiple-choice-checkbox');
    console.log(`[handleCorrectAnswerChange] Checkbox changed: ${clickedCheckbox.name}, checked: ${clickedCheckbox.checked}, Multiple choice: ${multipleChoiceCheckbox.checked}`);
    if (!multipleChoiceCheckbox.checked) {
        const allCheckboxes = questionContainer.querySelectorAll('.correct-answer-selector');
        allCheckboxes.forEach(checkbox => {
            if (checkbox !== clickedCheckbox) {
                console.log(`[handleCorrectAnswerChange] Unchecking ${checkbox.name}`);
                checkbox.checked = false;
            }
        });
        if (clickedCheckbox.checked) {
            console.log(`[handleCorrectAnswerChange] Ensuring ${clickedCheckbox.name} stays checked`);
            clickedCheckbox.checked = true;
        } else {
            if (allCheckboxes.length > 0 && !questionContainer.querySelector('.correct-answer-selector:checked')) {
                console.log('[handleCorrectAnswerChange] No checkboxes selected, checking the first one');
                allCheckboxes[0].checked = true;
            }
        }
    } else {
        console.log('[handleCorrectAnswerChange] Multiple choice enabled, no action needed');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Настройка вопроса
    function setupQuestion(questionContainer) {
        const textAnswerCheckbox = questionContainer.querySelector('.text-answer-checkbox');
        const multipleChoiceCheckbox = questionContainer.querySelector('.multiple-choice-checkbox');
        const correctAnswerContainer = questionContainer.querySelector('.correct-text-answer-container');
        const optionsContainer = questionContainer.querySelector('.options-container');
        const imageCheckbox = questionContainer.querySelector('.image-checkbox');
        const imageContainer = questionContainer.querySelector('.image-container');
        const imageInput = imageContainer?.querySelector('.form-control-file');
        const dragDrop = imageContainer?.querySelector('.drag-drop');
        const preview = imageContainer?.querySelector('.image-preview');
        const removeImageBtn = imageContainer?.querySelector('.remove-image');

        console.log(`[setupQuestion] Setting up question ${questionContainer.dataset.questionIndex}`);
        if (!textAnswerCheckbox || !multipleChoiceCheckbox || !correctAnswerContainer || !optionsContainer ||
            !imageCheckbox || !imageContainer || !imageInput || !dragDrop || !preview || !removeImageBtn) {
            console.error('[setupQuestion] Missing elements in question:', {
                textAnswerCheckbox: !!textAnswerCheckbox,
                multipleChoiceCheckbox: !!multipleChoiceCheckbox,
                correctAnswerContainer: !!correctAnswerContainer,
                optionsContainer: !!optionsContainer,
                imageCheckbox: !!imageCheckbox,
                imageContainer: !!imageContainer,
                imageInput: !!imageInput,
                dragDrop: !!dragDrop,
                preview: !!preview,
                removeImageBtn: !!removeImageBtn
            });
            return;
        }

        // Настройка изображения
        function setupImageHandlers() {
            console.log(`[setupImageHandlers] Setting up for question ${questionContainer.dataset.questionIndex}`);
            dragDrop.addEventListener('click', () => imageInput.click());
            dragDrop.addEventListener('dragover', (e) => {
                e.preventDefault();
                dragDrop.style.borderColor = '#007bff';
            });
            dragDrop.addEventListener('dragleave', () => dragDrop.style.borderColor = '#ccc');
            dragDrop.addEventListener('drop', (e) => {
                e.preventDefault();
                dragDrop.style.borderColor = '#ccc';
                const file = e.dataTransfer.files[0];
                if (file && file.type.startsWith('image/')) {
                    imageInput.files = e.dataTransfer.files;
                    previewImage(file);
                }
            });
            imageInput.addEventListener('change', () => {
                const file = imageInput.files[0];
                if (file) previewImage(file);
            });
            removeImageBtn.addEventListener('click', () => {
                imageInput.value = '';
                preview.style.display = 'none';
                removeImageBtn.style.display = 'none';
            });

            function previewImage(file) {
                const reader = new FileReader();
                reader.onload = () => {
                    preview.src = reader.result;
                    preview.style.display = 'block';
                    removeImageBtn.style.display = 'inline-block';
                };
                reader.readAsDataURL(file);
            }
        }

        // Управление видимостью
        function updateVisibility() {
            console.log(`[updateVisibility] Updating for question ${questionContainer.dataset.questionIndex}`);
            console.log(`[updateVisibility] Text answer: ${textAnswerCheckbox.checked}, Image: ${imageCheckbox.checked}`);

            if (textAnswerCheckbox.checked) {
                correctAnswerContainer.style.display = 'block';
                optionsContainer.style.display = 'none';
                multipleChoiceCheckbox.disabled = true;
                multipleChoiceCheckbox.checked = false;
                optionsContainer.querySelectorAll('[required]').forEach(el => el.removeAttribute('required'));
            } else {
                correctAnswerContainer.style.display = 'none';
                optionsContainer.style.display = 'block';
                multipleChoiceCheckbox.disabled = false;
                optionsContainer.querySelectorAll('.option-text').forEach(el => el.setAttribute('required', ''));
            }

            imageContainer.style.display = imageCheckbox.checked ? 'block' : 'none';
            console.log(`[updateVisibility] Image container display: ${imageContainer.style.display}`);
            setupAnswerSelectors(questionContainer);
        }

        // Привязка событий
        textAnswerCheckbox.addEventListener('change', updateVisibility);
        multipleChoiceCheckbox.addEventListener('change', () => setupAnswerSelectors(questionContainer));
        imageCheckbox.addEventListener('change', updateVisibility);

        // Инициализация
        updateVisibility();
        setupImageHandlers();
        setupAnswerSelectors(questionContainer);
    }

    // Добавление варианта
    function addOption(button) {
        console.log('[addOption] Adding option');
        const questionContainer = button.closest('.question-container');
        const questionIndex = questionContainer.dataset.questionIndex;
        const optionsContainer = button.closest('.options-container');
        const optionCount = optionsContainer.querySelectorAll('.option-item').length;

        const optionHtml = `
            <div class="option-item mb-2">
                <div class="input-group">
                    <input type="text" name="question_${questionIndex}_option_${optionCount}_text"
                           class="form-control option-text" placeholder="Текст варианта" required>
                    <div class="input-group-text">
                        <input type="checkbox"
                               name="question_${questionIndex}_option_${optionCount}_is_correct"
                               class="form-check-input correct-answer-selector">
                        <label class="form-check-label ms-2">Правильный</label>
                    </div>
                    <button type="button" class="btn btn-outline-danger remove-option">×</button>
                </div>
            </div>
        `;
        button.insertAdjacentHTML('beforebegin', optionHtml);
        setupAnswerSelectors(questionContainer);
    }

    // Добавление вопроса
    const addQuestionButton = document.getElementById('add-question');
    if (addQuestionButton) {
        addQuestionButton.addEventListener('click', function() {
            console.log('[addQuestion] Adding question');
            const container = document.getElementById('questions-container');
            const questionCount = container.querySelectorAll('.question-container').length;

            const questionHtml = `
                <div class="question-container card mb-4" data-question-index="${questionCount}">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h4>Вопрос <span class="question-number">${questionCount + 1}</span></h4>
                        <button type="button" class="btn btn-sm btn-danger remove-question">Удалить вопрос</button>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label class="form-label">Текст вопроса:</label>
                            <input type="text" name="question_${questionCount}_text" class="form-control question-text" required>
                        </div>
                        <div class="form-check mb-3">
                            <input type="checkbox" name="question_${questionCount}_is_text_answer"
                                   class="form-check-input text-answer-checkbox" id="q${questionCount}_text_answer">
                            <label class="form-check-label" for="q${questionCount}_text_answer">Текстовый ответ</label>
                        </div>
                        <div class="correct-text-answer-container mb-3" style="display: none;">
                            <label class="form-label">Правильный текстовый ответ:</label>
                            <input type="text" name="question_${questionCount}_correct_text_answer"
                                   class="form-control correct-text-answer-input">
                        </div>
                        <div class="form-check mb-3">
                            <input type="checkbox" name="question_${questionCount}_is_multiple_choice"
                                   class="form-check-input multiple-choice-checkbox" id="q${questionCount}_multiple_choice">
                            <label class="form-check-label" for="q${questionCount}_multiple_choice">Множественный выбор</label>
                        </div>
                        <div class="form-check mb-3">
                            <input type="checkbox" name="question_${questionCount}_has_image"
                                   class="form-check-input image-checkbox" id="q${questionCount}_has_image">
                            <label class="form-check-label" for="q${questionCount}_has_image">Добавить изображение</label>
                        </div>
                        <div class="image-container mb-3" style="display: none;">
                            <label class="form-label">Изображение (опционально):</label>
                            <div class="drag-drop" id="drag-drop-${questionCount}">
                                Перетащите изображение или кликните для выбора
                            </div>
                            <input type="file" name="question_${questionCount}_image" class="form-control-file d-none"
                                   accept="image/*" id="image-${questionCount}">
                            <img id="preview-${questionCount}" class="image-preview mt-2" src="#" alt="Предпросмотр" style="display: none;">
                            <button type="button" class="btn btn-sm btn-danger remove-image mt-2" style="display: none;">Удалить изображение</button>
                        </div>
                        <div class="options-container">
                            <h5>Варианты ответов:</h5>
                            <div class="option-item mb-2">
                                <div class="input-group">
                                    <input type="text" name="question_${questionCount}_option_0_text"
                                           class="form-control option-text" placeholder="Текст варианта" required>
                                    <div class="input-group-text">
                                        <input type="checkbox"
                                               name="question_${questionCount}_option_0_is_correct"
                                               class="form-check-input correct-answer-selector">
                                        <label class="form-check-label ms-2">Правильный</label>
                                    </div>
                                    <button type="button" class="btn btn-outline-danger remove-option">×</button>
                                </div>
                            </div>
                            <button type="button" class="btn btn-sm btn-outline-secondary add-option">+ Добавить вариант</button>
                        </div>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', questionHtml);
            setupQuestion(container.lastElementChild);
        });
    }

    // Делегирование событий
    document.body.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-question')) {
            e.target.closest('.question-container').remove();
            updateQuestionNumbers();
        } else if (e.target.classList.contains('remove-option')) {
            e.target.closest('.option-item').remove();
        } else if (e.target.classList.contains('add-option')) {
            addOption(e.target);
        }
    });

    function updateQuestionNumbers() {
        document.querySelectorAll('.question-container').forEach((container, index) => {
            container.querySelector('.question-number').textContent = index + 1;
        });
    }

    // Инициализация существующих вопросов
    document.querySelectorAll('.question-container').forEach(setupQuestion);

    // Настройка полей оценивания
    const gradingTypeSelect = document.querySelector('select[name="grading_type"]');
    const saveAsTemplateCheckbox = document.querySelector('input[name="save_as_template"]');
    if (gradingTypeSelect && saveAsTemplateCheckbox) {
        gradingTypeSelect.addEventListener('change', function() {
            const gradingType = this.value;
            document.getElementById('differentiated_fields').style.display = gradingType === 'differentiated' ? 'block' : 'none';
            document.getElementById('non_differentiated_fields').style.display = gradingType === 'non_differentiated' ? 'block' : 'none';
            updateExample();
        });

        saveAsTemplateCheckbox.addEventListener('change', function() {
            document.getElementById('template_name_field').style.display = this.checked ? 'block' : 'none';
        });

        function updateExample() {
            const gradingType = gradingTypeSelect.value;
            const exampleScore = 75;  // Примерный процент для демонстрации

            if (gradingType === 'differentiated') {
                const t2 = parseInt(document.querySelector('input[name="threshold_2"]').value) || 40;
                const t3 = parseInt(document.querySelector('input[name="threshold_3"]').value) || 60;
                const t4 = parseInt(document.querySelector('input[name="threshold_4"]').value) || 80;
                const t5 = parseInt(document.querySelector('input[name="threshold_5"]').value) || 90;

                let grade;
                if (exampleScore >= t5) grade = 5;
                else if (exampleScore >= t4) grade = 4;
                else if (exampleScore >= t3) grade = 3;
                else if (exampleScore >= t2) grade = 2;
                else grade = "Незачёт";

                document.getElementById('example_score').textContent = exampleScore;
                document.getElementById('example_grade_differentiated').textContent = grade;
            } else {
                const passThreshold = parseInt(document.querySelector('input[name="pass_threshold"]').value) || 60;
                document.getElementById('example_score_non').textContent = exampleScore;
                document.getElementById('example_grade_non_differentiated').textContent = exampleScore >= passThreshold ? 'Зачёт' : 'Незачёт';
            }
        }

        // Инициализация при загрузке
        gradingTypeSelect.dispatchEvent(new Event('change'));
    }
});