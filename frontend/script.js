// filename: frontend/script.js
document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIG ---
    const API_BASE_URL = 'http://127.0.0.1:8000';

    // --- STATE ---
    let allLessons = [];
    let currentLessonId = null;
    let uploadedFile = null;

    // --- DOM ELEMENTS ---
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const lessonList = document.getElementById('lesson-list');
    const progressBarFill = document.getElementById('progress-bar-fill');
    const lessonTitle = document.getElementById('lesson-title');
    const videoPlayer = document.getElementById('video-player');
    
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const filePreview = document.getElementById('file-preview');
    
    const quizArea = document.getElementById('quiz-area');
    const quizForm = document.getElementById('quiz-form');
    const feedbackArea = document.getElementById('feedback-area');
    const feedbackContent = document.getElementById('feedback-content');
    const submitButton = document.getElementById('submit-button');

    const prevLessonBtn = document.getElementById('prev-lesson-btn');
    const nextLessonBtn = document.getElementById('next-lesson-btn');
    const lessonStatusFooter = document.getElementById('lesson-status-footer');

    // --- INITIALIZATION ---
    const init = async () => {
        await fetchAndRenderSidebar();
        const firstUncompleted = allLessons.find(l => !l.is_completed && !l.is_locked);
        if (firstUncompleted) {
            loadLesson(firstUncompleted.id);
        } else if (allLessons.length > 0) {
            // If all are complete, load the last one
            loadLesson(allLessons[allLessons.length - 1].id);
        }
    };

    // --- API CALLS ---
    const fetchLessons = () => fetch(`${API_BASE_URL}/api/lessons`).then(res => res.json());

    const fetchLessonDetails = (lessonId) => fetch(`${API_BASE_URL}/api/lessons/${lessonId}`).then(res => res.json());

    const submitForEvaluation = (lessonId, formData) => {
        return fetch(`${API_BASE_URL}/api/lessons/${lessonId}/submit`, {
            method: 'POST',
            body: formData,
        }).then(res => {
            if (!res.ok) {
                // If the response is not ok, parse the JSON to get the error detail
                return res.json().then(err => Promise.reject(err));
            }
            return res.json();
        });
    };

    // --- RENDER FUNCTIONS ---
    const fetchAndRenderSidebar = async () => {
        allLessons = await fetchLessons();
        renderSidebar();
        updateProgressBar();
    };

    const renderSidebar = () => {
        lessonList.innerHTML = '';
        allLessons.forEach(lesson => {
            const li = document.createElement('li');
            li.className = 'lesson-item';
            li.dataset.id = lesson.id;

            let icon = 'lock';
            if (lesson.is_completed) {
                li.classList.add('completed');
                icon = 'check_circle';
            } else if (!lesson.is_locked) {
                li.classList.add('active-topic');
                icon = 'play_circle_outline';
            } else {
                li.classList.add('locked');
            }

            if (lesson.id === currentLessonId) {
                li.classList.add('active');
            }
            
            li.innerHTML = `
                <i class="material-icons icon">${icon}</i>
                <span>${lesson.title}</span>
            `;
            
            if (!lesson.is_locked) {
                li.addEventListener('click', () => loadLesson(lesson.id));
            }

            lessonList.appendChild(li);
        });
    };

    const updateProgressBar = () => {
        const completedCount = allLessons.filter(l => l.is_completed).length;
        const totalCount = allLessons.length;
        const percentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;
        progressBarFill.style.width = `${percentage}%`;
    };

    const renderQuiz = (quizData) => {
        quizForm.innerHTML = '';
        if (!quizData || !Array.isArray(quizData)) {
            quizForm.innerHTML = "<p>Could not load quiz questions.</p>";
            return;
        }
        quizData.forEach((q, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.className = 'quiz-question';
            questionDiv.innerHTML = `<p>${index + 1}. ${q.question}</p>`;

            const optionsDiv = document.createElement('div');
            optionsDiv.className = 'quiz-options';

            q.options.forEach(option => {
                const label = document.createElement('label');
                label.innerHTML = `
                    <input type="radio" name="question-${index}" value="${option}">
                    ${option}
                `;
                optionsDiv.appendChild(label);
            });
            questionDiv.appendChild(optionsDiv);
            quizForm.appendChild(questionDiv);
        });
    };
    
    // --- CORE LOGIC ---
    const loadLesson = async (lessonId) => {
        if (!lessonId) return;
        currentLessonId = lessonId;
        resetUIForNewLesson();
        renderSidebar();
        
        const lessonDetails = await fetchLessonDetails(lessonId);
        lessonTitle.textContent = lessonDetails.title;
        videoPlayer.src = lessonDetails.youtube_url;

        renderQuiz(lessonDetails.quiz);
        updateNavigation();
    };

    const handleFileSelect = (file) => {
        if (file) {
            uploadedFile = file;
            filePreview.textContent = `File selected: ${file.name}`;
            quizArea.classList.remove('hidden');
            submitButton.disabled = false;
        }
    };

    const handleSubmit = async () => {
        if (!uploadedFile) {
            alert("Please upload your notes file first.");
            return;
        }
        const quizAnswers = [];
        const questions = quizForm.querySelectorAll('.quiz-question');
        questions.forEach((q, index) => {
            const questionText = q.querySelector('p').textContent.replace(/^\d+\.\s*/, '');
            const selected = q.querySelector(`input[name="question-${index}"]:checked`);
            quizAnswers.push({
                question: questionText,
                selected_answer: selected ? selected.value : 'Not answered'
            });
        });

        const formData = new FormData();
        formData.append('notes_file', uploadedFile);
        formData.append('quiz_answers_json', JSON.stringify(quizAnswers));

        submitButton.textContent = 'Evaluating...';
        submitButton.disabled = true;

        try {
            const result = await submitForEvaluation(currentLessonId, formData);
            
            console.log("Received evaluation from backend:", result);

            if (result && typeof result.feedback !== 'undefined') {
                displayFeedback(result);
            
                if (result.is_approved) {
                    lessonStatusFooter.innerHTML = `<i class="material-icons icon">check_circle</i> Lesson Complete!`;
                    await fetchAndRenderSidebar();
                    updateNavigation();
                } else {
                    submitButton.textContent = 'Re-submit for Evaluation';
                    submitButton.disabled = false;
                }
            } else {
                throw new Error("The evaluation response from the server was malformed.");
            }
        } catch (error) {
            console.error("Error during submission:", error);
            const errorMessage = error.detail || error.message || "An unknown error occurred.";
            displayFeedback({
                is_approved: false,
                feedback: `A network or server error occurred. Please try again. Details: ${errorMessage}`
            });
            submitButton.textContent = 'Re-submit for Evaluation';
            submitButton.disabled = false;
        }
    };


    const displayFeedback = (result) => {
        feedbackContent.textContent = result.feedback;
        feedbackArea.classList.remove('hidden', 'approved', 'revision');
        feedbackArea.classList.add(result.is_approved ? 'approved' : 'revision');
    };

    const resetUIForNewLesson = () => {
        uploadedFile = null;
        filePreview.textContent = '';
        quizArea.classList.add('hidden');
        feedbackArea.classList.add('hidden');
        submitButton.disabled = true;
        submitButton.textContent = 'Submit for Evaluation';
        lessonStatusFooter.innerHTML = `<span>Lesson Incomplete</span>`;
    };

    const updateNavigation = () => {
        const currentIndex = allLessons.findIndex(l => l.id === currentLessonId);
        
        if (currentIndex > 0) {
            prevLessonBtn.classList.remove('disabled');
            prevLessonBtn.dataset.targetId = allLessons[currentIndex - 1].id;
        } else {
            prevLessonBtn.classList.add('disabled');
        }

        const currentLessonData = allLessons.find(l => l.id === currentLessonId);
        if (currentIndex < allLessons.length - 1 && currentLessonData && currentLessonData.is_completed) {
            nextLessonBtn.classList.remove('disabled');
            nextLessonBtn.dataset.targetId = allLessons[currentIndex + 1].id;
        } else {
            nextLessonBtn.classList.add('disabled');
        }
    };

    // --- EVENT LISTENERS ---
    sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('collapsed'));
    
    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => handleFileSelect(e.target.files[0]));
    
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        handleFileSelect(e.dataTransfer.files[0]);
    });

    submitButton.addEventListener('click', handleSubmit);

    prevLessonBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (!e.currentTarget.classList.contains('disabled')) {
            loadLesson(parseInt(e.currentTarget.dataset.targetId));
        }
    });

    nextLessonBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (!e.currentTarget.classList.contains('disabled')) {
            loadLesson(parseInt(e.currentTarget.dataset.targetId));
        }
    });

    init();
});