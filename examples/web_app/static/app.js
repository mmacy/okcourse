// OKCourse Web App JavaScript

let currentCourseId = null;
let progressEventSource = null;
let isManualMode = false;
let isAutoScrollEnabled = true;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadDropdownOptions();
    setupEventListeners();
});

// Load dropdown options from API
async function loadDropdownOptions() {
    try {
        // Load models
        const modelsResponse = await fetch('/api/models');
        const modelsData = await modelsResponse.json();
        populateSelect('text_model_outline', modelsData.text_models, 'gpt-4o-mini');
        populateSelect('text_model_lecture', modelsData.text_models, 'gpt-4o-mini');

        // Load voices
        const voicesResponse = await fetch('/api/voices');
        const voicesData = await voicesResponse.json();
        populateSelect('tts_voice', voicesData.voices, 'alloy');

        // Load prompt styles
        const stylesResponse = await fetch('/api/prompt-styles');
        const stylesData = await stylesResponse.json();
        populateSelect('prompt_style', stylesData.styles, 'Academic course');

    } catch (error) {
        console.error('Error loading dropdown options:', error);
        showError('Failed to load dropdown options: ' + error.message);
    }
}

// Populate a select element with options
function populateSelect(selectId, options, defaultValue = null) {
    const select = document.getElementById(selectId);
    select.innerHTML = '';
    
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        if (option === defaultValue) {
            optionElement.selected = true;
        }
        select.appendChild(optionElement);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Form submission
    document.getElementById('course-form').addEventListener('submit', handleFormSubmit);
    
    // Show/hide voice selection based on audio checkbox
    document.getElementById('generate_audio').addEventListener('change', function() {
        const voiceGroup = document.getElementById('voice-group');
        voiceGroup.style.display = this.checked ? 'block' : 'none';
    });
    
    // Autoscroll toggle
    document.addEventListener('change', function(event) {
        if (event.target.id === 'autoscroll-enabled') {
            isAutoScrollEnabled = event.target.checked;
        }
    });
}

// Handle form submission
async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const courseData = {
        title: formData.get('title'),
        num_lectures: parseInt(formData.get('num_lectures')),
        num_subtopics: parseInt(formData.get('num_subtopics')),
        prompt_style: formData.get('prompt_style'),
        text_model_outline: formData.get('text_model_outline'),
        text_model_lecture: formData.get('text_model_lecture'),
        generate_image: formData.has('generate_image'),
        generate_audio: formData.has('generate_audio'),
        tts_voice: formData.get('tts_voice'),
        output_directory: formData.get('output_directory')
    };
    
    // Capture manual mode setting
    isManualMode = formData.has('manual_mode');

    // Add loading state to submit button
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/courses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(courseData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        currentCourseId = result.course_id;
        
        // Remove loading state
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        
        // Hide form and show progress
        document.querySelector('.form-section').style.display = 'none';
        document.getElementById('progress-section').style.display = 'block';
        
        // Debug: Log that progress section is shown
        console.log('Progress section shown, generation-layout should be visible');
        
        // Initialize progress tracking
        initializeProgressSteps(courseData);
        
        // Start progress monitoring
        startProgressMonitoring();
        
    } catch (error) {
        console.error('Error creating course:', error);
        
        // Remove loading state on error
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
        
        showError('Failed to create course: ' + error.message);
    }
}

// Initialize progress steps based on user selections
function initializeProgressSteps(courseData) {
    // Show/hide steps based on user selections
    const imageStep = document.getElementById('step-image');
    const audioStep = document.getElementById('step-audio');
    
    if (!courseData.generate_image) {
        imageStep.style.display = 'none';
    }
    
    if (!courseData.generate_audio) {
        audioStep.style.display = 'none';
    }
    
    // Reset all steps
    resetSteps();
}

// Reset all progress steps
function resetSteps() {
    const steps = document.querySelectorAll('.step');
    steps.forEach(step => {
        step.classList.remove('active', 'completed', 'error');
        const status = step.querySelector('.step-status');
        status.textContent = 'Waiting...';
    });
}

// Start progress monitoring
function startProgressMonitoring() {
    if (progressEventSource) {
        progressEventSource.close();
    }
    
    if (isManualMode) {
        // Manual mode: show first button
        document.getElementById('btn-generate-outline').style.display = 'inline-block';
    } else {
        // Automatic mode: start with outline generation
        setTimeout(() => generateOutline(), 1000);
    }
}

// Generate course outline
async function generateOutline() {
    if (!currentCourseId) return;
    
    setStepStatus('step-outline', 'active', 'Generating...');
    setButtonLoading('btn-generate-outline', true);
    
    try {
        const response = await fetch(`/api/courses/${currentCourseId}/generate-outline`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        setStepStatus('step-outline', 'completed', 'Completed');
        setButtonLoading('btn-generate-outline', false);
        displayOutline(result.outline);
        
        // Progress to next step
        if (isManualMode) {
            document.getElementById('btn-generate-lectures').style.display = 'inline-block';
        } else {
            setTimeout(() => generateLectures(), 1000);
        }
        
    } catch (error) {
        console.error('Error generating outline:', error);
        setStepStatus('step-outline', 'error', 'Failed: ' + error.message);
        setButtonLoading('btn-generate-outline', false);
        showError('Failed to generate outline: ' + error.message);
    }
}

// Generate course lectures
async function generateLectures() {
    if (!currentCourseId) return;
    
    setStepStatus('step-lectures', 'active', 'Generating lectures...');
    setButtonLoading('btn-generate-lectures', true);
    
    try {
        const response = await fetch(`/api/courses/${currentCourseId}/generate-lectures`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        setStepStatus('step-lectures', 'completed', 'Completed');
        setButtonLoading('btn-generate-lectures', false);
        displayLectures(result.lectures);
        
        // Progress to next step
        const imageStep = document.getElementById('step-image');
        const audioStep = document.getElementById('step-audio');
        
        if (imageStep.style.display !== 'none') {
            if (isManualMode) {
                document.getElementById('btn-generate-image').style.display = 'inline-block';
            } else {
                setTimeout(() => generateImage(), 1000);
            }
        } else if (audioStep.style.display !== 'none') {
            if (isManualMode) {
                document.getElementById('btn-generate-audio').style.display = 'inline-block';
            } else {
                setTimeout(() => generateAudio(), 1000);
            }
        } else {
            // If no image or audio, show completion
            showCompletion();
        }
        
    } catch (error) {
        console.error('Error generating lectures:', error);
        setStepStatus('step-lectures', 'error', 'Failed: ' + error.message);
        setButtonLoading('btn-generate-lectures', false);
        showError('Failed to generate lectures: ' + error.message);
    }
}

// Generate course image
async function generateImage() {
    if (!currentCourseId) return;
    
    setStepStatus('step-image', 'active', 'Generating image...');
    setButtonLoading('btn-generate-image', true);
    
    try {
        const response = await fetch(`/api/courses/${currentCourseId}/generate-image`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        setStepStatus('step-image', 'completed', 'Completed');
        setButtonLoading('btn-generate-image', false);
        displayImage(result);
        
        // Progress to audio step or show completion
        const audioStep = document.getElementById('step-audio');
        if (audioStep.style.display !== 'none') {
            if (isManualMode) {
                document.getElementById('btn-generate-audio').style.display = 'inline-block';
            } else {
                setTimeout(() => generateAudio(), 1000);
            }
        } else {
            showCompletion();
        }
        
    } catch (error) {
        console.error('Error generating image:', error);
        setStepStatus('step-image', 'error', 'Failed: ' + error.message);
        setButtonLoading('btn-generate-image', false);
        showError('Failed to generate image: ' + error.message);
    }
}

// Generate course audio
async function generateAudio() {
    if (!currentCourseId) return;
    
    setStepStatus('step-audio', 'active', 'Generating audio...');
    setButtonLoading('btn-generate-audio', true);
    
    try {
        const response = await fetch(`/api/courses/${currentCourseId}/generate-audio`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        setStepStatus('step-audio', 'completed', 'Completed');
        setButtonLoading('btn-generate-audio', false);
        displayAudio(result);
        
        showCompletion();
        
    } catch (error) {
        console.error('Error generating audio:', error);
        setStepStatus('step-audio', 'error', 'Failed: ' + error.message);
        setButtonLoading('btn-generate-audio', false);
        showError('Failed to generate audio: ' + error.message);
    }
}

// Set step status
function setStepStatus(stepId, statusClass, statusText) {
    const step = document.getElementById(stepId);
    step.classList.remove('active', 'completed', 'error');
    step.classList.add(statusClass);
    
    const status = step.querySelector('.step-status');
    status.textContent = statusText;
    
    // Show/hide spinner based on status
    const spinner = step.querySelector('.step-spinner');
    if (statusClass === 'active') {
        spinner.style.display = 'block';
    } else {
        spinner.style.display = 'none';
    }
}

// Set button loading state
function setButtonLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (isLoading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
        button.style.display = 'none'; // Hide after completion
    }
}

// Disable button (legacy function)
function disableButton(buttonId) {
    setButtonLoading(buttonId, false);
    const button = document.getElementById(buttonId);
    button.style.display = 'none';
}

// Display course outline
function displayOutline(outline) {
    if (!outline) return;
    
    const outlineCard = document.getElementById('outline-result');
    const outlineContent = document.getElementById('outline-content');
    
    // Convert outline to markdown
    let markdownText = `# ${outline.title}\n\n`;
    outline.topics.forEach(topic => {
        markdownText += `## Lecture ${topic.number}: ${topic.title}\n\n`;
        if (topic.subtopics && topic.subtopics.length > 0) {
            topic.subtopics.forEach(subtopic => {
                markdownText += `- ${subtopic}\n`;
            });
            markdownText += '\n';
        }
    });
    
    // Render markdown to HTML
    outlineContent.innerHTML = marked.parse(markdownText);
    outlineContent.className = 'markdown-content';
    
    outlineCard.style.display = 'block';
    
    // Hide the placeholder content
    const placeholder = document.querySelector('.content-placeholder');
    if (placeholder) {
        placeholder.style.display = 'none';
    }
    
    // Auto-scroll to the new content
    autoScrollToContent('outline-result');
}

// Display course lectures
function displayLectures(lectures) {
    if (!lectures) return;
    
    const lecturesCard = document.getElementById('lectures-result');
    const lecturesContent = document.getElementById('lectures-content');
    
    lecturesContent.innerHTML = '';
    
    lectures.forEach(lecture => {
        const lectureDiv = document.createElement('div');
        lectureDiv.className = 'lecture-item';
        
        // Convert lecture to markdown
        let markdownText = `## Lecture ${lecture.number}: ${lecture.title}\n\n`;
        markdownText += lecture.text;
        
        // Render markdown to HTML
        lectureDiv.innerHTML = marked.parse(markdownText);
        lectureDiv.className = 'lecture-item markdown-content';
        
        lecturesContent.appendChild(lectureDiv);
    });
    
    lecturesCard.style.display = 'block';
    
    // Auto-scroll to the new content
    autoScrollToContent('lectures-result');
}

// Display course image
function displayImage(imageResult) {
    const imageCard = document.getElementById('image-result');
    const courseImage = document.getElementById('course-image');
    const downloadBtn = document.getElementById('btn-download-image');
    
    if (imageResult.image_exists && imageResult.image_path) {
        // Set image source to API endpoint
        courseImage.src = `/api/courses/${currentCourseId}/image`;
        courseImage.style.display = 'block';
        
        // Setup download button
        downloadBtn.onclick = () => downloadFile(`/api/courses/${currentCourseId}/image`, 'course_cover.png');
        downloadBtn.style.display = 'inline-flex';
        
        // Add status message
        const statusDiv = document.createElement('div');
        statusDiv.innerHTML = `
            <p>✅ Cover image generated successfully!</p>
            <p><strong>Location:</strong> ${imageResult.image_path}</p>
        `;
        statusDiv.style.marginBottom = '1rem';
        
        // Insert status before media container
        const mediaContainer = courseImage.parentElement;
        mediaContainer.parentElement.insertBefore(statusDiv, mediaContainer);
    } else {
        const statusDiv = document.createElement('div');
        statusDiv.innerHTML = '<p>❌ Image generation completed but file not found.</p>';
        courseImage.parentElement.parentElement.appendChild(statusDiv);
    }
    
    imageCard.style.display = 'block';
    
    // Auto-scroll to the new content
    autoScrollToContent('image-result');
}

// Display course audio
function displayAudio(audioResult) {
    const audioCard = document.getElementById('audio-result');
    const courseAudio = document.getElementById('course-audio');
    const downloadBtn = document.getElementById('btn-download-audio');
    
    if (audioResult.audio_exists && audioResult.audio_path) {
        // Set audio source to API endpoint
        courseAudio.src = `/api/courses/${currentCourseId}/audio`;
        courseAudio.style.display = 'block';
        
        // Setup download button
        downloadBtn.onclick = () => downloadFile(`/api/courses/${currentCourseId}/audio`, 'course_audio.mp3');
        downloadBtn.style.display = 'inline-flex';
        
        // Add status message
        const statusDiv = document.createElement('div');
        statusDiv.innerHTML = `
            <p>✅ Course audio generated successfully!</p>
            <p><strong>Location:</strong> ${audioResult.audio_path}</p>
        `;
        statusDiv.style.marginBottom = '1rem';
        
        // Insert status before media container
        const mediaContainer = courseAudio.parentElement;
        mediaContainer.parentElement.insertBefore(statusDiv, mediaContainer);
    } else {
        const statusDiv = document.createElement('div');
        statusDiv.innerHTML = '<p>❌ Audio generation completed but file not found.</p>';
        courseAudio.parentElement.parentElement.appendChild(statusDiv);
    }
    
    audioCard.style.display = 'block';
    
    // Auto-scroll to the new content
    autoScrollToContent('audio-result');
}

// Show completion
async function showCompletion() {
    try {
        // Get final course data
        const response = await fetch(`/api/courses/${currentCourseId}`);
        const courseData = await response.json();
        
        // Display generation info
        if (courseData.generation_info) {
            const infoCard = document.getElementById('generation-info');
            const infoContent = document.getElementById('generation-info-content');
            
            const totalTime = (
                courseData.generation_info.outline_gen_elapsed_seconds +
                courseData.generation_info.lecture_gen_elapsed_seconds +
                courseData.generation_info.image_gen_elapsed_seconds +
                courseData.generation_info.audio_gen_elapsed_seconds
            );
            
            infoContent.innerHTML = `
                <div class="generation-details">
                    Course Generation Complete!
                    
                    Total Time: ${Math.round(totalTime)}s
                    Outline: ${Math.round(courseData.generation_info.outline_gen_elapsed_seconds)}s
                    Lectures: ${Math.round(courseData.generation_info.lecture_gen_elapsed_seconds)}s
                    Image: ${Math.round(courseData.generation_info.image_gen_elapsed_seconds)}s
                    Audio: ${Math.round(courseData.generation_info.audio_gen_elapsed_seconds)}s
                    
                    Output Directory: ${courseData.settings.output_directory}
                </div>
            `;
            
            infoCard.style.display = 'block';
            
            // Auto-scroll to the completion info
            autoScrollToContent('generation-info');
        }
        
    } catch (error) {
        console.error('Error getting final course data:', error);
    }
    
    // Show new course button
    document.getElementById('btn-new-course').style.display = 'inline-block';
}

// Reset form for new course
function resetForm() {
    // Reset all sections
    document.querySelector('.form-section').style.display = 'block';
    document.getElementById('progress-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'none';
    
    // Reset form
    document.getElementById('course-form').reset();
    
    // Reset state
    currentCourseId = null;
    isManualMode = false;
    isAutoScrollEnabled = true;
    
    // Reset autoscroll checkbox
    const autoscrollCheckbox = document.getElementById('autoscroll-enabled');
    if (autoscrollCheckbox) {
        autoscrollCheckbox.checked = true;
    }
    
    // Show placeholder content again
    const placeholder = document.querySelector('.content-placeholder');
    if (placeholder) {
        placeholder.style.display = 'block';
    }
    
    // Close progress monitoring
    if (progressEventSource) {
        progressEventSource.close();
        progressEventSource = null;
    }
    
    // Reset button visibility
    const buttons = ['btn-generate-outline', 'btn-generate-lectures', 'btn-generate-image', 'btn-generate-audio', 'btn-new-course'];
    buttons.forEach(id => {
        const button = document.getElementById(id);
        button.style.display = 'none';
        button.disabled = false;
    });
    
    // Reset steps visibility
    document.getElementById('step-image').style.display = 'block';
    document.getElementById('step-audio').style.display = 'block';
    
    // Hide voice group
    document.getElementById('voice-group').style.display = 'none';
    
    // Reload dropdown options
    loadDropdownOptions();
}

// Download file helper function
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Auto-scroll to new content
function autoScrollToContent(elementId) {
    if (!isAutoScrollEnabled) return;
    
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Add a small delay to allow content to render
    setTimeout(() => {
        const contentColumn = document.getElementById('content-column');
        if (contentColumn) {
            // Calculate the position relative to the content column
            const contentColumnRect = contentColumn.getBoundingClientRect();
            const elementRect = element.getBoundingClientRect();
            const relativeTop = elementRect.top - contentColumnRect.top + contentColumn.scrollTop;
            
            contentColumn.scrollTo({
                top: relativeTop - 20, // Small offset for better visual
                behavior: 'smooth'
            });
        } else {
            // Fallback to regular scroll if content column not found
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 300);
}

// Show error message
function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorContent = document.getElementById('error-content');
    
    errorContent.textContent = message;
    errorSection.style.display = 'block';
    
    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth' });
}