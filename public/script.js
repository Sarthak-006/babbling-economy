const imageElement = document.getElementById('story-image');
const situationElement = document.getElementById('situation-text');
const translationElement = document.getElementById('translation-text');
const choicesElement = document.getElementById('choices');
const loadingElement = document.getElementById('loading-indicator');
const scoreElement = document.getElementById('score-display');
const endScreenElement = document.getElementById('end-screen');
const mangaImageElement = document.getElementById('manga-image');
const summaryImageElement = document.getElementById('summary-image');
const endTextElement = document.getElementById('end-text');
const vocabularyListElement = document.getElementById('vocabulary-list');
const achievementsListElement = document.getElementById('achievements-list');
const achievementBadgeElement = document.getElementById('achievement-badge');
const languageToggleButton = document.getElementById('language-toggle');

// Add these new elements for the share modal
const shareModalElement = document.getElementById('share-modal');
const shareMangaImageElement = document.getElementById('share-manga-image');
const shareLoadingElement = document.getElementById('share-loading');
const closeModalButton = document.querySelector('.close-modal');
const downloadImageButton = document.getElementById('download-image');
const copyImageButton = document.getElementById('copy-image');
const shareTwitterButton = document.getElementById('share-twitter');
const shareFacebookButton = document.getElementById('share-facebook');

// Language state
let currentLanguage = 'es'; // Default to Spanish
let vocabularyWords = [];
let achievements = [];
let totalWordsLearned = 0;

// Language configurations
const languages = {
    'es': {
        name: 'Español',
        flag: '🇪🇸',
        buttonText: '🇪🇸 Español'
    },
    'fr': {
        name: 'Français',
        flag: '🇫🇷',
        buttonText: '🇫🇷 Français'
    },
    'de': {
        name: 'Deutsch',
        flag: '🇩🇪',
        buttonText: '🇩🇪 Deutsch'
    },
    'it': {
        name: 'Italiano',
        flag: '🇮🇹',
        buttonText: '🇮🇹 Italiano'
    },
    'pt': {
        name: 'Português',
        flag: '🇵🇹',
        buttonText: '🇵🇹 Português'
    },
    'ja': {
        name: '日本語',
        flag: '🇯🇵',
        buttonText: '🇯🇵 日本語'
    },
    'ko': {
        name: '한국어',
        flag: '🇰🇷',
        buttonText: '🇰🇷 한국어'
    },
    'zh': {
        name: '中文',
        flag: '🇨🇳',
        buttonText: '🇨🇳 中文'
    }
};

// Language toggle functionality
languageToggleButton.addEventListener('click', () => {
    const languageKeys = Object.keys(languages);
    const currentIndex = languageKeys.indexOf(currentLanguage);
    const nextIndex = (currentIndex + 1) % languageKeys.length;
    currentLanguage = languageKeys[nextIndex];

    const newLanguage = languages[currentLanguage];
    languageToggleButton.textContent = newLanguage.buttonText;

    // Update the game state with new language
    updateGameState();
});

function showLoading(isLoading) {
    if (isLoading) {
        // Set up the loading indicator with animation
        loadingElement.textContent = 'Loading your language adventure';
        loadingElement.style.opacity = '0';
        loadingElement.style.display = 'block';

        setTimeout(() => {
            loadingElement.style.transition = 'opacity 0.3s ease';
            loadingElement.style.opacity = '1';
        }, 50);

        // Hide choices with fade-out
        if (choicesElement.style.display !== 'none') {
            choicesElement.style.transition = 'opacity 0.3s ease';
            choicesElement.style.opacity = '0';

            setTimeout(() => {
                choicesElement.style.display = 'none';
            }, 300);
        } else {
            choicesElement.style.display = 'none';
        }
    } else {
        // Hide loading with fade-out
        loadingElement.style.transition = 'opacity 0.3s ease';
        loadingElement.style.opacity = '0';

        setTimeout(() => {
            loadingElement.style.display = 'none';

            // Show choices with fade-in if they were hidden
            if (choicesElement.style.display === 'none') {
                choicesElement.style.opacity = '0';
                choicesElement.style.display = 'block';

                setTimeout(() => {
                    choicesElement.style.transition = 'opacity 0.5s ease';
                    choicesElement.style.opacity = '1';
                }, 50);
            }
        }, 300);
    }
}

async function updateGameState() {
    showLoading(true);

    // Clear previous state
    endScreenElement.style.display = 'none';
    endTextElement.innerHTML = '';
    situationElement.textContent = '';
    translationElement.textContent = '';
    translationElement.style.display = 'none';
    imageElement.src = '';
    mangaImageElement.src = '';
    summaryImageElement.src = '';
    choicesElement.innerHTML = '';

    // Remove any reset containers from the end screen
    const existingEndScreenResetContainers = endScreenElement.querySelectorAll('.reset-container');
    existingEndScreenResetContainers.forEach(container => container.remove());

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

        const response = await fetch(`/api/state?language=${currentLanguage}`, {
            signal: controller.signal,
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Validate the data received
        if (!data || (typeof data === 'object' && Object.keys(data).length === 0)) {
            throw new Error("Received empty response from server");
        }

        renderState(data);
    } catch (error) {
        console.error("Error fetching game state:", error);
        situationElement.textContent = `Error loading language adventure: ${error.message}. Retrying in 5 seconds...`;

        // Always show the reset button when there's an error
        choicesElement.innerHTML = '';
        const resetContainer = document.createElement('div');
        resetContainer.className = 'reset-container';

        const resetButton = document.createElement('button');
        resetButton.textContent = 'Reset Game';
        resetButton.className = 'reset-button';
        resetButton.addEventListener('click', resetGame);
        resetContainer.appendChild(resetButton);

        const refreshBtn = document.createElement('button');
        refreshBtn.textContent = 'Refresh Page';
        refreshBtn.className = 'reset-button';
        refreshBtn.style.marginLeft = '10px';
        refreshBtn.addEventListener('click', () => window.location.reload());
        resetContainer.appendChild(refreshBtn);

        choicesElement.appendChild(resetContainer);

        // Auto-retry after 5 seconds
        setTimeout(() => {
            situationElement.textContent = "Attempting to reconnect...";
            updateGameState();
        }, 5000);
    } finally {
        showLoading(false);
    }
}

function renderState(data) {
    console.log("Rendering state:", data);

    // Update score - check both current_score and score properties
    const score = data.current_score !== undefined ? data.current_score :
        (data.score !== undefined ? data.score : 0);
    scoreElement.textContent = `Words Learned: ${score}`;

    // Update image with fade-in effect
    imageElement.style.opacity = '0';
    imageElement.src = data.image_url || '';
    imageElement.alt = data.image_prompt || 'Story scene';
    imageElement.onload = () => {
        imageElement.style.transition = 'opacity 0.5s ease';
        imageElement.style.opacity = '1';
    };
    imageElement.style.display = 'block';

    // Animate situation text
    situationElement.style.opacity = '0';
    setTimeout(() => {
        situationElement.textContent = data.situation || 'Loading...';
        situationElement.style.transition = 'opacity 0.8s ease';
        situationElement.style.opacity = '1';
    }, 300);

    // Show translation if available
    if (data.translation) {
        translationElement.style.opacity = '0';
        setTimeout(() => {
            translationElement.textContent = data.translation;
            translationElement.style.transition = 'opacity 0.8s ease';
            translationElement.style.opacity = '1';
            translationElement.style.display = 'block';
        }, 600);
    }

    // Update vocabulary words
    if (data.vocabulary_words) {
        vocabularyWords = data.vocabulary_words;
        totalWordsLearned += data.vocabulary_words.length;
    }

    // Check for achievements
    checkAchievements(score, totalWordsLearned);

    // Clear all content in choices
    choicesElement.innerHTML = '';

    // Add a single reset button at the top
    const resetContainer = document.createElement('div');
    resetContainer.className = 'reset-container';

    const resetButton = document.createElement('button');
    resetButton.textContent = 'Reset Game';
    resetButton.className = 'reset-button';
    resetButton.addEventListener('click', resetGame);
    resetContainer.appendChild(resetButton);

    choicesElement.appendChild(resetContainer);

    if (data.is_end) {
        // Handle End Screen
        displayEndScreen(data);
    } else if (data.choices && data.choices.length > 0) {
        // Create choice buttons with staggered animation
        data.choices.forEach((choice, index) => {
            const button = document.createElement('button');
            button.textContent = choice.text || `Choice ${index + 1}`;
            button.dataset.index = index;
            button.addEventListener('click', handleChoiceClick);
            button.style.opacity = '0';
            button.style.transform = 'translateY(20px)';
            choicesElement.appendChild(button);

            // Staggered animation for buttons
            setTimeout(() => {
                button.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                button.style.opacity = '1';
                button.style.transform = 'translateY(0)';
            }, 500 + (index * 100)); // Stagger by 100ms per button
        });
    } else {
        // No choices, maybe an intermediate state or error
        situationElement.textContent += "\n (No choices available)";
    }
}

async function handleChoiceClick(event) {
    const choiceIndex = parseInt(event.target.dataset.index, 10);
    if (isNaN(choiceIndex)) return;

    showLoading(true);
    choicesElement.innerHTML = ''; // Clear choices immediately

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

        const response = await fetch('/api/choice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                choice_index: choiceIndex,
                language: currentLanguage
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const nextStateData = await response.json();
        renderState(nextStateData); // Render the new state received
    } catch (error) {
        console.error("Error making choice:", error);
        situationElement.textContent = `Error processing choice: ${error.message}`;

        // Always show the reset button when there's an error
        choicesElement.innerHTML = '';
        const resetContainer = document.createElement('div');
        resetContainer.className = 'reset-container';

        const resetButton = document.createElement('button');
        resetButton.textContent = 'Reset Game';
        resetButton.className = 'reset-button';
        resetButton.addEventListener('click', resetGame);
        resetContainer.appendChild(resetButton);

        choicesElement.appendChild(resetContainer);
    } finally {
        showLoading(false);
    }
}

function displayEndScreen(data) {
    // Hide the main choices
    choicesElement.style.display = 'none';

    // Calculate a star rating based on score (1-5 stars)
    const score = data.current_score !== undefined ? data.current_score :
        (data.score !== undefined ? data.score : 0);
    const maxScore = 15; // Assuming maximum possible score is around 15 words
    const starRating = Math.max(1, Math.min(5, Math.ceil(score / 3)));

    // Show the end screen container with a fade in
    endScreenElement.style.display = 'block';
    endScreenElement.style.opacity = '0';

    // Prepare the end text content with score and rating
    const endingCategory = data.ending_category || 'Language Adventure Complete';
    const stars = '★'.repeat(starRating) + '☆'.repeat(5 - starRating);

    let endTextContent = `
        <h2>${endingCategory}</h2>
        <div class="score-display">
            <span class="score-label">Words Learned:</span> 
            <span class="score-value">${score}</span>
            <div class="star-rating">${stars}</div>
        </div>
        <p>${data.situation}</p>
    `;

    // Add a personalized message based on score
    if (score >= 12) {
        endTextContent += `<p class="end-message">Excellent! You're becoming a language expert! 🌟</p>`;
    } else if (score >= 8) {
        endTextContent += `<p class="end-message">Great job! You've learned many new words! 🎉</p>`;
    } else if (score >= 4) {
        endTextContent += `<p class="end-message">Well done! Keep practicing to learn more words! 👍</p>`;
    } else {
        endTextContent += `<p class="end-message">Good start! Try again to learn more words! 💪</p>`;
    }

    endTextElement.innerHTML = endTextContent;

    // Display vocabulary words learned
    if (vocabularyWords && vocabularyWords.length > 0) {
        vocabularyListElement.innerHTML = '';
        vocabularyWords.forEach(word => {
            const wordElement = document.createElement('div');
            wordElement.className = 'vocabulary-item';
            wordElement.textContent = word;
            vocabularyListElement.appendChild(wordElement);
        });
    }

    // Display achievements
    displayAchievements();

    // Load the manga-style image with fade-in effect
    if (data.manga_image_url) {
        mangaImageElement.style.opacity = '0';
        mangaImageElement.src = data.manga_image_url;
        mangaImageElement.onload = () => {
            mangaImageElement.style.transition = 'opacity 0.8s ease';
            mangaImageElement.style.opacity = '1';
        };
    }

    // Load the summary image with fade-in effect
    if (data.summary_image_url) {
        summaryImageElement.style.opacity = '0';
        summaryImageElement.src = data.summary_image_url;
        summaryImageElement.onload = () => {
            summaryImageElement.style.transition = 'opacity 0.8s ease';
            summaryImageElement.style.opacity = '1';
        };
    }

    // Add a reset container with custom styling for the end screen
    const resetContainer = document.createElement('div');
    resetContainer.className = 'reset-container end-reset';

    const resetButton = document.createElement('button');
    resetButton.textContent = 'Learn More Words';
    resetButton.className = 'reset-button end-reset-button';
    resetButton.addEventListener('click', resetGame);

    const shareButton = document.createElement('button');
    shareButton.textContent = 'Share Your Progress';
    shareButton.className = 'reset-button share-button';

    // Update share button click handler to open the modal
    shareButton.addEventListener('click', () => {
        openShareModal(score, endingCategory);
    });

    resetContainer.appendChild(resetButton);
    resetContainer.appendChild(shareButton);
    endScreenElement.appendChild(resetContainer);

    // Fade in the end screen
    setTimeout(() => {
        endScreenElement.style.transition = 'opacity 1s ease';
        endScreenElement.style.opacity = '1';
    }, 500);
}

// New function to open the share modal and generate shareable image
async function openShareModal(score, endingCategory) {
    // Show the modal
    shareModalElement.style.display = 'block';

    // Clear any previous image
    shareMangaImageElement.style.display = 'none';
    shareMangaImageElement.src = '';

    // Show loading indicator
    shareLoadingElement.style.display = 'block';

    try {
        // Fetch the shareable image from our API
        const response = await fetch('/api/share-image');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Hide loading and show the image
        shareLoadingElement.style.display = 'none';
        shareMangaImageElement.style.display = 'block';
        shareMangaImageElement.src = data.share_image_url;

        // Setup share buttons with the appropriate data
        setupShareButtons(data.share_image_url, score, endingCategory);

    } catch (error) {
        console.error("Error generating share image:", error);
        shareLoadingElement.textContent = `Error generating image: ${error.message}. Please try again.`;

        // Add a retry button
        const retryButton = document.createElement('button');
        retryButton.textContent = 'Retry';
        retryButton.className = 'action-button';
        retryButton.style.marginTop = '15px';
        retryButton.addEventListener('click', () => {
            openShareModal(score, endingCategory);
        });

        shareLoadingElement.appendChild(retryButton);
    }
}

// Setup the share buttons with the correct URLs and functionality
function setupShareButtons(imageUrl, score, endingCategory) {
    // Setup download button
    downloadImageButton.onclick = () => {
        downloadImage(imageUrl, 'babbling-economy-progress.jpg');
    };

    // Setup copy button
    copyImageButton.onclick = () => {
        copyImageToClipboard(imageUrl);
    };

    // Setup social share buttons
    const languageName = languages[currentLanguage].name;
    const shareText = `I learned ${score} new words in ${languageName} with Babbling Economy! Can you beat my score?`;
    const shareUrl = window.location.href;

    // Twitter share
    shareTwitterButton.onclick = () => {
        const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;
        window.open(twitterUrl, '_blank');
    };

    // Facebook share
    shareFacebookButton.onclick = () => {
        const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}&quote=${encodeURIComponent(shareText)}`;
        window.open(facebookUrl, '_blank');
    };
}

// Function to download the image
function downloadImage(url, filename) {
    // Create a temporary anchor element
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.style.display = 'none';

    // Add to body, click it to trigger download, and remove
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// Function to copy image to clipboard using Fetch API to get the blob
async function copyImageToClipboard(url) {
    try {
        const response = await fetch(url);
        const blob = await response.blob();

        // Check if the Clipboard API is available and can handle images
        if (navigator.clipboard && navigator.clipboard.write) {
            const item = new ClipboardItem({ [blob.type]: blob });
            await navigator.clipboard.write([item]);
            alert('Image copied to clipboard!');
        } else {
            // Fallback for browsers that don't support copying images
            alert('Your browser doesn\'t support copying images. Please use the Download button instead.');
        }
    } catch (error) {
        console.error('Error copying image to clipboard:', error);
        alert('Failed to copy image. Please try downloading it instead.');
    }
}

// Close the modal when clicking the X
closeModalButton.addEventListener('click', () => {
    shareModalElement.style.display = 'none';
});

// Close the modal when clicking outside the content
window.addEventListener('click', (event) => {
    if (event.target === shareModalElement) {
        shareModalElement.style.display = 'none';
    }
});

// Helper function to copy text to clipboard
function copyToClipboard(text) {
    // Try to use the modern clipboard API first
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                alert('Story copied to clipboard! You can now share it with friends.');
            })
            .catch(err => {
                console.error('Clipboard write failed:', err);
                fallbackCopyToClipboard(text);
            });
    } else {
        fallbackCopyToClipboard(text);
    }
}

// Fallback copy method for older browsers
function fallbackCopyToClipboard(text) {
    // Create a temporary input element
    const input = document.createElement('input');
    input.style.position = 'fixed';
    input.style.opacity = 0;
    input.value = text;
    document.body.appendChild(input);

    // Select and copy
    input.select();
    document.execCommand('copy');

    // Clean up
    document.body.removeChild(input);

    // Notify user
    alert('Story copied to clipboard! You can now share it with friends.');
}

async function resetGame() {
    showLoading(true);

    // Hide end screen
    endScreenElement.style.display = 'none';

    // Clear end screen content to prevent duplicates on subsequent resets
    endTextElement.innerHTML = '';
    mangaImageElement.src = '';
    summaryImageElement.src = '';
    vocabularyListElement.innerHTML = '';

    // Remove any existing reset containers from the end screen
    const existingEndScreenResetContainers = endScreenElement.querySelectorAll('.reset-container');
    existingEndScreenResetContainers.forEach(container => container.remove());

    // Show normal image
    imageElement.style.display = 'block';
    situationElement.textContent = 'Starting new language adventure...';

    // Clear the choices area
    choicesElement.innerHTML = '';

    // Reset vocabulary words and achievements
    vocabularyWords = [];
    achievements = [];
    totalWordsLearned = 0;

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

        const response = await fetch('/api/reset', {
            method: 'POST',
            signal: controller.signal,
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Check if we got a valid game state
        if (!data || (!data.situation && !data.current_score && !data.choices)) {
            console.error("Invalid state received after reset:", data);
            // If we didn't get a valid state, fetch it explicitly
            await updateGameState();
        } else {
            // Render the state we received
            renderState(data);
        }
    } catch (error) {
        console.error("Error resetting game:", error);
        situationElement.textContent = `Error resetting game: ${error.message}. Please refresh the page.`;

        // Always show a refresh button
        choicesElement.innerHTML = '';
        const refreshBtn = document.createElement('button');
        refreshBtn.textContent = 'Refresh Page';
        refreshBtn.addEventListener('click', () => window.location.reload());
        choicesElement.appendChild(refreshBtn);
    } finally {
        showLoading(false);
    }
}

// Achievement checking function
function checkAchievements(score, totalWords) {
    const newAchievements = [];

    // Word count achievements
    if (totalWords >= 5 && !achievements.includes('First Steps')) {
        newAchievements.push({ name: 'First Steps', icon: '👶', description: 'Learned 5 words' });
        achievements.push('First Steps');
    }

    if (totalWords >= 10 && !achievements.includes('Word Collector')) {
        newAchievements.push({ name: 'Word Collector', icon: '📚', description: 'Learned 10 words' });
        achievements.push('Word Collector');
    }

    if (totalWords >= 20 && !achievements.includes('Vocabulary Master')) {
        newAchievements.push({ name: 'Vocabulary Master', icon: '🎓', description: 'Learned 20 words' });
        achievements.push('Vocabulary Master');
    }

    // Score achievements
    if (score >= 5 && !achievements.includes('Language Explorer')) {
        newAchievements.push({ name: 'Language Explorer', icon: '🗺️', description: 'Reached 5 points' });
        achievements.push('Language Explorer');
    }

    if (score >= 10 && !achievements.includes('Babbling Expert')) {
        newAchievements.push({ name: 'Babbling Expert', icon: '🏆', description: 'Reached 10 points' });
        achievements.push('Babbling Expert');
    }

    // Language achievements
    if (currentLanguage !== 'es' && !achievements.includes('Multilingual')) {
        newAchievements.push({ name: 'Multilingual', icon: '🌍', description: 'Tried different languages' });
        achievements.push('Multilingual');
    }

    // Show achievement badge if new achievements unlocked
    if (newAchievements.length > 0) {
        showAchievementBadge(newAchievements);
    }
}

// Show achievement badge
function showAchievementBadge(newAchievements) {
    achievementBadgeElement.style.display = 'block';
    achievementBadgeElement.textContent = newAchievements[0].icon;

    // Hide badge after 3 seconds
    setTimeout(() => {
        achievementBadgeElement.style.display = 'none';
    }, 3000);
}

// Display achievements in end screen
function displayAchievements() {
    if (achievements.length > 0) {
        achievementsListElement.innerHTML = '';
        achievements.forEach(achievementName => {
            const achievement = getAchievementDetails(achievementName);
            const achievementElement = document.createElement('div');
            achievementElement.className = 'achievement-item';
            achievementElement.innerHTML = `${achievement.icon} ${achievement.name}`;
            achievementElement.title = achievement.description;
            achievementsListElement.appendChild(achievementElement);
        });
    }
}

// Get achievement details
function getAchievementDetails(name) {
    const achievementMap = {
        'First Steps': { icon: '👶', description: 'Learned 5 words' },
        'Word Collector': { icon: '📚', description: 'Learned 10 words' },
        'Vocabulary Master': { icon: '🎓', description: 'Learned 20 words' },
        'Language Explorer': { icon: '🗺️', description: 'Reached 5 points' },
        'Babbling Expert': { icon: '🏆', description: 'Reached 10 points' },
        'Multilingual': { icon: '🌍', description: 'Tried different languages' }
    };
    return achievementMap[name] || { icon: '🏅', description: 'Achievement unlocked' };
}

// Initial load when the page loads
document.addEventListener('DOMContentLoaded', updateGameState);