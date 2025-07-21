// OKCourse Web App JavaScript

let currentCourseId = null;
let progressEventSource = null;

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
        
        // Hide form and show progress
        document.querySelector('.form-section').style.display = 'none';
        document.getElementById('progress-section').style.display = 'block';
        
        // Initialize progress tracking
        initializeProgressSteps(courseData);
        
        // Start progress monitoring
        startProgressMonitoring();
        
    } catch (error) {
        console.error('Error creating course:', error);
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
    
    // Note: This is a simplified progress monitoring
    // In a real implementation, you might use Server-Sent Events
    // For now, we'll just enable the first button
    document.getElementById('btn-generate-outline').style.display = 'inline-block';
}

// Generate course outline
async function generateOutline() {
    if (!currentCourseId) return;
    
    setStepStatus('step-outline', 'active', 'Generating...');
    disableButton('btn-generate-outline');
    
    try {
        const response = await fetch(`/api/courses/${currentCourseId}/generate-outline`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        setStepStatus('step-outline', 'completed', 'Completed');
        displayOutline(result.outline);
        
        // Enable next step
        document.getElementById('btn-generate-lectures').style.display = 'inline-block';
        
    } catch (error) {
        console.error('Error generating outline:', error);
        setStepStatus('step-outline', 'error', 'Failed: ' + error.message);
        showError('Failed to generate outline: ' + error.message);
    }
}

// Generate course lectures
async function generateLectures() {
    if (!currentCourseId) return;
    
    setStepStatus('step-lectures', 'active', 'Generating lectures...');
    disableButton('btn-generate-lectures');
    
    try {
        const response = await fetch(`/api/courses/${currentCourseId}/generate-lectures`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        setStepStatus('step-lectures', 'completed', 'Completed');
        displayLectures(result.lectures);
        
        // Enable next steps based on user selections
        const imageStep = document.getElementById('step-image');
        const audioStep = document.getElementById('step-audio');
        
        if (imageStep.style.display !== 'none') {
            document.getElementById('btn-generate-image').style.display = 'inline-block';
        } else if (audioStep.style.display !== 'none') {
            document.getElementById('btn-generate-audio').style.display = 'inline-block';
        } else {
            // If no image or audio, show completion
            showCompletion();
        }
        
    } catch (error) {
        console.error('Error generating lectures:', error);
        setStepStatus('step-lectures', 'error', 'Failed: ' + error.message);
        showError('Failed to generate lectures: ' + error.message);
    }
}

// Generate course image
async function generateImage() {
    if (!currentCourseId) return;
    
    setStepStatus('step-image', 'active', 'Generating image...');
    disableButton('btn-generate-image');
    
    try {
        const response = await fetch(`/api/courses/${currentCourseId}/generate-image`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        setStepStatus('step-image', 'completed', 'Completed');
        displayImage(result);
        
        // Enable audio step or show completion
        const audioStep = document.getElementById('step-audio');
        if (audioStep.style.display !== 'none') {
            document.getElementById('btn-generate-audio').style.display = 'inline-block';
        } else {
            showCompletion();
        }
        
    } catch (error) {
        console.error('Error generating image:', error);
        setStepStatus('step-image', 'error', 'Failed: ' + error.message);
        showError('Failed to generate image: ' + error.message);
    }
}

// Generate course audio
async function generateAudio() {
    if (!currentCourseId) return;
    
    setStepStatus('step-audio', 'active', 'Generating audio...');
    disableButton('btn-generate-audio');
    
    try {
        const response = await fetch(`/api/courses/${currentCourseId}/generate-audio`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        setStepStatus('step-audio', 'completed', 'Completed');
        displayAudio(result);
        
        showCompletion();
        
    } catch (error) {
        console.error('Error generating audio:', error);
        setStepStatus('step-audio', 'error', 'Failed: ' + error.message);
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
}

// Disable button
function disableButton(buttonId) {
    const button = document.getElementById(buttonId);
    button.disabled = true;
    button.style.display = 'none';
}

// Display course outline
function displayOutline(outline) {
    if (!outline) return;
    
    const outlineCard = document.getElementById('outline-result');
    const outlineContent = document.getElementById('outline-content');
    
    let outlineText = `Course Title: ${outline.title}\n\n`;
    outline.topics.forEach(topic => {
        outlineText += `Lecture ${topic.number}: ${topic.title}\n`;
        topic.subtopics.forEach(subtopic => {
            outlineText += `  - ${subtopic}\n`;
        });
        outlineText += '\n';
    });
    
    outlineContent.textContent = outlineText;
    outlineCard.style.display = 'block';
    document.getElementById('results-section').style.display = 'block';
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
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'lecture-title';
        titleDiv.textContent = `Lecture ${lecture.number}: ${lecture.title}`;
        
        const textDiv = document.createElement('div');
        textDiv.className = 'lecture-text';
        textDiv.textContent = lecture.text;
        
        lectureDiv.appendChild(titleDiv);
        lectureDiv.appendChild(textDiv);
        lecturesContent.appendChild(lectureDiv);
    });
    
    lecturesCard.style.display = 'block';
}

// Display course image
function displayImage(imageResult) {
    const imageCard = document.getElementById('image-result');
    const imageContent = document.getElementById('image-content');
    
    if (imageResult.image_exists && imageResult.image_path) {
        imageContent.innerHTML = `
            <p>Cover image generated successfully!</p>
            <p><strong>Location:</strong> ${imageResult.image_path}</p>
        `;
    } else {
        imageContent.innerHTML = '<p>Image generation completed but file not found.</p>';
    }
    
    imageCard.style.display = 'block';
}

// Display course audio
function displayAudio(audioResult) {
    const audioCard = document.getElementById('audio-result');
    const audioContent = document.getElementById('audio-content');
    
    if (audioResult.audio_exists && audioResult.audio_path) {
        audioContent.innerHTML = `
            <p>Course audio generated successfully!</p>
            <p><strong>Location:</strong> ${audioResult.audio_path}</p>
        `;
    } else {
        audioContent.innerHTML = '<p>Audio generation completed but file not found.</p>';
    }
    
    audioCard.style.display = 'block';
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
    document.getElementById('results-section').style.display = 'none';
    document.getElementById('error-section').style.display = 'none';
    
    // Reset form
    document.getElementById('course-form').reset();
    
    // Reset state
    currentCourseId = null;
    
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

// Show error message
function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorContent = document.getElementById('error-content');
    
    errorContent.textContent = message;
    errorSection.style.display = 'block';
    
    // Scroll to error
    errorSection.scrollIntoView({ behavior: 'smooth' });
}