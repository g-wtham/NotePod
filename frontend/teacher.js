// filename: frontend/teacher.js
document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://127.0.0.1:8000';

    const addVideoForm = document.getElementById('add-video-form');
    const teacherMessage = document.getElementById('teacher-message');
    const progressDashboard = document.getElementById('progress-dashboard');
    const addLessonBtn = document.getElementById('add-lesson-btn');

    const convertToEmbedUrl = (url) => {
        try {
            const urlObj = new URL(url);
            let videoId;
            if (urlObj.hostname === 'youtu.be') {
                videoId = urlObj.pathname.slice(1);
            } else {
                videoId = urlObj.searchParams.get('v');
            }
            return videoId ? `https://www.youtube.com/embed/${videoId}` : null;
        } catch (error) {
            return null;
        }
    };
    
    addVideoForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        addLessonBtn.disabled = true;
        addLessonBtn.textContent = "Adding...";
        teacherMessage.textContent = "";

        const title = document.getElementById('video-title').value;
        const originalUrl = document.getElementById('youtube-url').value;
        const embedUrl = convertToEmbedUrl(originalUrl);

        if (!embedUrl) {
            teacherMessage.textContent = 'Error: Invalid YouTube URL format. Use a standard "watch?v=" or "youtu.be" link.';
            teacherMessage.style.color = 'var(--error-color)';
            addLessonBtn.disabled = false;
            addLessonBtn.textContent = "Add Lesson";
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/api/teacher/videos`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ title: title, youtube_url: embedUrl })
            });

            if (response.ok) {
                teacherMessage.textContent = 'Successfully added new lesson!';
                teacherMessage.style.color = 'var(--success-color)';
                addVideoForm.reset();
            } else {
                const errorData = await response.json();
                teacherMessage.textContent = `Error adding lesson: ${errorData.detail || 'Unknown error'}`;
                teacherMessage.style.color = 'var(--error-color)';
            }
        } catch (error) {
            teacherMessage.textContent = 'A network error occurred.';
            teacherMessage.style.color = 'var(--error-color)';
        } finally {
            addLessonBtn.disabled = false;
            addLessonBtn.textContent = "Add Lesson";
        }
    });

    const loadProgress = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/teacher/progress`);
            const data = await response.json();
            progressDashboard.innerHTML = `
                <p><strong>Student:</strong> ${data.student}</p>
                <p><strong>Progress:</strong> ${data.completed_lessons} / ${data.total_lessons} lessons completed.</p>
            `;
        } catch (error) {
            progressDashboard.innerHTML = `<p style="color: var(--error-color)">Could not load student progress.</p>`;
        }
    };

    loadProgress();
}); 