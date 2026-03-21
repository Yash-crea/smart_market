// Basic interactivity for logo, search and login dropdown
document.addEventListener('DOMContentLoaded', function(){
	// PWA Installation
	initPWA();
	
	const logo = document.getElementById('logo');
	const searchForm = document.getElementById('searchForm');
	const searchInput = document.getElementById('searchInput');
	const loginBtn = document.getElementById('loginBtn');
	const loginMenu = document.getElementById('loginMenu');
	const dropdownLi = loginBtn && loginBtn.parentElement;

	if(logo){
		logo.addEventListener('click', ()=>{
			logo.classList.add('pulse');
			setTimeout(()=> logo.classList.remove('pulse'), 500);
			window.scrollTo({ top:0, behavior:'smooth'});
		});
	}

	if(searchForm){
		searchForm.addEventListener('submit', function(e){
			const q = searchInput.value.trim();
			if(!q) {
				e.preventDefault();
				searchInput.focus();
				return;
			}
			// Form will submit normally to shop page with search param
		});
	}

	// Hamburger menu toggle for mobile
	const menuToggle = document.getElementById('menuToggle');
	const navLinks = document.getElementById('navLinks');
	if(menuToggle && navLinks){
		menuToggle.addEventListener('click', function(){
			const isOpen = navLinks.classList.toggle('open');
			menuToggle.setAttribute('aria-expanded', String(isOpen));
		});
		// Close menu when clicking a link
		navLinks.querySelectorAll('a').forEach(function(link){
			link.addEventListener('click', function(){
				navLinks.classList.remove('open');
				menuToggle.setAttribute('aria-expanded', 'false');
			});
		});
	}

	if(loginBtn && loginMenu && dropdownLi){
		loginBtn.addEventListener('click', function(e){
			e.stopPropagation();
			const open = dropdownLi.classList.toggle('open');
			loginMenu.setAttribute('aria-hidden', String(!open));
		});

		// close when clicking outside
		document.addEventListener('click', function(){
			dropdownLi.classList.remove('open');
			loginMenu.setAttribute('aria-hidden','true');
		});
	}
	// smooth in-page scrolling for anchor links
	document.querySelectorAll('a[href^="#"]').forEach(function(a){
		a.addEventListener('click', function(e){
			const href = a.getAttribute('href');
			if(href.length>1){
				const target = document.querySelector(href);
				if(target){
					e.preventDefault();
					target.scrollIntoView({ behavior: 'smooth', block: 'start' });
				}
			}
		});
	});

	// About editor (frontend-only, persists to localStorage)
	(function(){
		const aboutImage = document.getElementById('aboutImage');
		const aboutImageInput = document.getElementById('aboutImageInput');
		const chooseImageBtn = document.getElementById('chooseImageBtn');
		const editBtn = document.getElementById('editAboutBtn');
		const aboutView = document.getElementById('aboutView');
		const aboutDesc = document.getElementById('aboutDesc');
		const aboutEditForm = document.getElementById('aboutEditForm');
		const aboutDescInput = document.getElementById('aboutDescInput');
		const saveBtn = document.getElementById('saveAboutBtn');
		const cancelBtn = document.getElementById('cancelAboutBtn');

		if(!aboutImage) return;

		// load saved data
		const savedDesc = localStorage.getItem('about_description');
		const savedImage = localStorage.getItem('about_image');
		if(savedDesc) aboutDesc.textContent = savedDesc;
		if(savedImage) aboutImage.src = savedImage;

		let currentImageData = savedImage || aboutImage.src;

		editBtn.addEventListener('click', function(){
			aboutEditForm.style.display = '';
			aboutView.style.display = 'none';
			aboutDescInput.value = aboutDesc.textContent.trim();
		});

		chooseImageBtn.addEventListener('click', function(){
			aboutImageInput.click();
		});

		aboutImageInput.addEventListener('change', function(e){
			const file = e.target.files && e.target.files[0];
			if(!file) return;
			const reader = new FileReader();
			reader.onload = function(ev){
				aboutImage.src = ev.target.result;
				currentImageData = ev.target.result; // data URL
			};
			reader.readAsDataURL(file);
		});

		saveBtn.addEventListener('click', function(e){
			e.preventDefault();
			const newDesc = aboutDescInput.value.trim();
			aboutDesc.textContent = newDesc || 'No description provided.';
			// persist
			localStorage.setItem('about_description', aboutDesc.textContent);
			if(currentImageData) localStorage.setItem('about_image', currentImageData);
			aboutEditForm.style.display = 'none';
			aboutView.style.display = '';
		});

		cancelBtn.addEventListener('click', function(){
			// revert preview to saved
			const saved = localStorage.getItem('about_image');
			aboutImage.src = saved || currentImageData;
			aboutEditForm.style.display = 'none';
			aboutView.style.display = '';
		});

	})();
});

// PWA Functions
function initPWA() {
    // Register service worker
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/static/sw.js')
                .then(function(registration) {
                    console.log('ServiceWorker registration successful: ', registration.scope);
                })
                .catch(function(err) {
                    console.log('ServiceWorker registration failed: ', err);
                });
        });
    }

    // PWA Install prompt
    let deferredPrompt;
    let installButton;

    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent the mini-infobar from appearing on mobile
        e.preventDefault();
        // Stash the event so it can be triggered later
        deferredPrompt = e;
        // Show the install button
        showInstallButton();
    });

    function showInstallButton() {
        // Create install button if it doesn't exist
        if (!installButton) {
            installButton = document.createElement('button');
            installButton.id = 'installPWA';
            installButton.innerHTML = `
                <svg viewBox="0 0 24 24" width="20" height="20" style="margin-right: 8px;">
                    <path fill="currentColor" d="M12 2c5.5 0 10 4.5 10 10s-4.5 10-10 10S2 17.5 2 12 6.5 2 12 2zM7 13h3v6h4v-6h3l-5-5-5 5z"/>
                </svg>
                Install App
            `;
            installButton.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #2b8a3e;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 25px;
                cursor: pointer;
                font-family: inherit;
                font-size: 14px;
                font-weight: 600;
                display: flex;
                align-items: center;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                transition: all 0.3s ease;
                z-index: 999;
                animation: slideInRight 0.5s ease;
            `;

            // Add hover effects
            installButton.addEventListener('mouseenter', function() {
                this.style.background = '#37b24d';
                this.style.transform = 'translateY(-2px)';
                this.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.2)';
            });

            installButton.addEventListener('mouseleave', function() {
                this.style.background = '#2b8a3e';
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            });

            // Add click handler
            installButton.addEventListener('click', installPWA);

            // Add animation keyframes
            if (!document.getElementById('pwaAnimations')) {
                const style = document.createElement('style');
                style.id = 'pwaAnimations';
                style.textContent = `
                    @keyframes slideInRight {
                        from {
                            opacity: 0;
                            transform: translateX(100px);
                        }
                        to {
                            opacity: 1;
                            transform: translateX(0);
                        }
                    }
                    
                    @keyframes fadeOut {
                        from {
                            opacity: 1;
                            transform: scale(1);
                        }
                        to {
                            opacity: 0;
                            transform: scale(0.8);
                        }
                    }
                    
                    @media (max-width: 600px) {
                        #installPWA {
                            top: 10px !important;
                            right: 10px !important;
                            font-size: 12px !important;
                            padding: 10px 16px !important;
                        }
                    }
                `;
                document.head.appendChild(style);
            }

            document.body.appendChild(installButton);
        }
    }

    function installPWA() {
        if (deferredPrompt) {
            // Show the install prompt
            deferredPrompt.prompt();

            // Wait for the user to respond to the prompt
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the A2HS prompt');
                    hideInstallButton();
                } else {
                    console.log('User dismissed the A2HS prompt');
                }
                deferredPrompt = null;
            });
        }
    }

    function hideInstallButton() {
        if (installButton) {
            installButton.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                installButton.remove();
                installButton = null;
            }, 300);
        }
    }

    // Hide install button if app is already installed
    window.addEventListener('appinstalled', (evt) => {
        console.log('PWA was installed');
        hideInstallButton();
    });

    // Handle app installation on iOS
    if (window.navigator.standalone) {
        console.log('PWA is running in standalone mode');
    }

    // Add offline indicator
    function updateOnlineStatus() {
        const status = navigator.onLine ? 'online' : 'offline';
        if (status === 'offline') {
            showOfflineIndicator();
        } else {
            hideOfflineIndicator();
        }
    }

    function showOfflineIndicator() {
        let offlineIndicator = document.getElementById('offlineIndicator');
        if (!offlineIndicator) {
            offlineIndicator = document.createElement('div');
            offlineIndicator.id = 'offlineIndicator';
            offlineIndicator.innerHTML = '📱 You are offline - Some features may not work';
            offlineIndicator.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                background: #ff6b6b;
                color: white;
                text-align: center;
                padding: 10px;
                z-index: 10000;
                font-size: 14px;
                font-weight: 600;
            `;
            document.body.appendChild(offlineIndicator);
        }
    }

    function hideOfflineIndicator() {
        const offlineIndicator = document.getElementById('offlineIndicator');
        if (offlineIndicator) {
            offlineIndicator.remove();
        }
    }

    // Listen for online/offline events
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    
    // Check initial status
    updateOnlineStatus();
    
    // Show PWA notification on first visit
    if (!localStorage.getItem('pwaNotificationShown')) {
        setTimeout(showPWANotification, 3000);
    }

    function showPWANotification() {
        const notification = document.createElement('div');
        notification.id = 'pwaNotification';
        notification.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <svg viewBox="0 0 24 24" width="24" height="24" style="margin-right: 12px; fill: #2b8a3e;">
                    <path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 7.5V9M21 17V15L15 15.5V17M9 8L6 8V10L9 10.5V8ZM9 14L6 14V16L9 16.5V14ZM12 7C11.7 7 11.4 7.1 11.2 7.3L9.5 9H7.5C6.67 9 6 9.67 6 10.5V13.5C6 14.33 6.67 15 7.5 15H9.5L11.2 16.7C11.4 16.9 11.7 17 12 17C12.6 17 13 16.6 13 16V8C13 7.4 12.6 7 12 7Z"/>
                </svg>
                <strong>Install Smart Market App!</strong>
            </div>
            <p style="margin: 0 0 16px 0; font-size: 14px; color: #666; line-height: 1.4;">
                Add Smart Market to your home screen for a better shopping experience. 
                Quick access, offline browsing, and app-like performance!
            </p>
            <div style="display: flex; gap: 12px;">
                <button id="installNowBtn" style="background: #2b8a3e; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 13px; font-weight: 600;">
                    Install Now
                </button>
                <button id="laterBtn" style="background: #f8f9fa; color: #666; border: 1px solid #e0e0e0; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 13px;">
                    Maybe Later
                </button>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            max-width: 350px;
            z-index: 1002;
            border: 1px solid #e0e0e0;
            animation: slideInLeft 0.5s ease;
        `;

        // Add animation
        if (!document.getElementById('pwaNotificationStyle')) {
            const style = document.createElement('style');
            style.id = 'pwaNotificationStyle';
            style.textContent = `
                @keyframes slideInLeft {
                    from {
                        opacity: 0;
                        transform: translateX(-100px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                
                @media (max-width: 600px) {
                    #pwaNotification {
                        left: 10px !important;
                        right: 10px !important;
                        max-width: none !important;
                        bottom: 10px !important;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(notification);

        // Handle buttons
        document.getElementById('installNowBtn').onclick = function() {
            if (deferredPrompt) {
                installPWA();
            } else {
                // On iOS or if install prompt not available
                alert('To install on iOS:\n1. Tap the Share button\n2. Select "Add to Home Screen"\n\nOn Android:\n1. Tap the menu (⋮)\n2. Select "Add to Home screen"');
            }
            removePWANotification();
        };

        document.getElementById('laterBtn').onclick = function() {
            removePWANotification();
        };

        // Auto-hide after 15 seconds
        setTimeout(removePWANotification, 15000);
        
        // Mark as shown
        localStorage.setItem('pwaNotificationShown', 'true');
    }

    function removePWANotification() {
        const notification = document.getElementById('pwaNotification');
        if (notification) {
            notification.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }
}

// Accessibility functionality
document.addEventListener('DOMContentLoaded', function() {
    const accessibilityIcon = document.getElementById('accessibilityIcon');
    const accessibilityPanel = document.getElementById('accessibilityPanel');
    const closeAccessibility = document.getElementById('closeAccessibility');
    
    // Button elements
    const decreaseFont = document.getElementById('decreaseFont');
    const resetFont = document.getElementById('resetFont');
    const increaseFont = document.getElementById('increaseFont');
    const toggleContrast = document.getElementById('toggleContrast');
    const toggleGrayscale = document.getElementById('toggleGrayscale');
    const highlightLinks = document.getElementById('highlightLinks');
    const readingGuide = document.getElementById('readingGuide');
    const resetAll = document.getElementById('resetAll');
    
    // State tracking
    let currentFontSize = 0; // -1 = smaller, 0 = normal, 1 = larger, 2 = x-large
    let isHighContrast = false;
    let isGrayscale = false;
    let isLinksHighlighted = false;
    let isReadingGuideActive = false;
    let readingGuideElement = null;
    
    // Load saved settings
    loadAccessibilitySettings();
    
    // Toggle panel visibility
    accessibilityIcon.addEventListener('click', function() {
        const isVisible = accessibilityPanel.style.display === 'block';
        accessibilityPanel.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible) {
            // Animation
            accessibilityPanel.style.opacity = '0';
            accessibilityPanel.style.transform = 'translateY(20px)';
            setTimeout(() => {
                accessibilityPanel.style.opacity = '1';
                accessibilityPanel.style.transform = 'translateY(0)';
            }, 10);
            accessibilityPanel.style.transition = 'all 0.3s ease';
        }
    });
    
    // Close panel
    closeAccessibility.addEventListener('click', function() {
        accessibilityPanel.style.display = 'none';
    });
    
    // Close panel when clicking outside
    document.addEventListener('click', function(e) {
        if (!accessibilityIcon.contains(e.target) && !accessibilityPanel.contains(e.target)) {
            accessibilityPanel.style.display = 'none';
        }
    });
    
    // Font size controls
    decreaseFont.addEventListener('click', function() {
        currentFontSize = Math.max(-1, currentFontSize - 1);
        updateFontSize();
        saveAccessibilitySettings();
    });
    
    resetFont.addEventListener('click', function() {
        currentFontSize = 0;
        updateFontSize();
        saveAccessibilitySettings();
    });
    
    increaseFont.addEventListener('click', function() {
        currentFontSize = Math.min(2, currentFontSize + 1);
        updateFontSize();
        saveAccessibilitySettings();
    });
    
    // High contrast toggle
    toggleContrast.addEventListener('click', function() {
        isHighContrast = !isHighContrast;
        document.body.classList.toggle('high-contrast', isHighContrast);
        toggleContrast.classList.toggle('active', isHighContrast);
        saveAccessibilitySettings();
    });
    
    // Grayscale toggle
    toggleGrayscale.addEventListener('click', function() {
        isGrayscale = !isGrayscale;
        document.body.classList.toggle('grayscale', isGrayscale);
        toggleGrayscale.classList.toggle('active', isGrayscale);
        saveAccessibilitySettings();
    });
    
    // Highlight links toggle
    highlightLinks.addEventListener('click', function() {
        isLinksHighlighted = !isLinksHighlighted;
        document.body.classList.toggle('highlight-links', isLinksHighlighted);
        highlightLinks.classList.toggle('active', isLinksHighlighted);
        saveAccessibilitySettings();
    });
    
    // Reading guide toggle
    readingGuide.addEventListener('click', function() {
        isReadingGuideActive = !isReadingGuideActive;
        readingGuide.classList.toggle('active', isReadingGuideActive);
        
        if (isReadingGuideActive) {
            createReadingGuide();
        } else {
            removeReadingGuide();
        }
        saveAccessibilitySettings();
    });
    
    // Reset all settings
    resetAll.addEventListener('click', function() {
        currentFontSize = 0;
        isHighContrast = false;
        isGrayscale = false;
        isLinksHighlighted = false;
        isReadingGuideActive = false;
        
        // Reset UI
        updateFontSize();
        document.body.classList.remove('high-contrast', 'grayscale', 'highlight-links');
        removeReadingGuide();
        
        // Reset button states
        document.querySelectorAll('.accessibility-content button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        saveAccessibilitySettings();
    });
    
    // Helper functions
    function updateFontSize() {
        document.body.classList.remove('large-text', 'x-large-text');
        if (currentFontSize === 1) {
            document.body.classList.add('large-text');
        } else if (currentFontSize === 2) {
            document.body.classList.add('x-large-text');
        }
        
        // Update button states
        decreaseFont.disabled = currentFontSize <= -1;
        increaseFont.disabled = currentFontSize >= 2;
        resetFont.classList.toggle('active', currentFontSize === 0);
    }
    
    function createReadingGuide() {
        if (readingGuideElement) return;
        
        readingGuideElement = document.createElement('div');
        readingGuideElement.className = 'reading-guide';
        document.body.appendChild(readingGuideElement);
        
        document.addEventListener('mousemove', updateReadingGuide);
    }
    
    function removeReadingGuide() {
        if (readingGuideElement) {
            readingGuideElement.remove();
            readingGuideElement = null;
        }
        document.removeEventListener('mousemove', updateReadingGuide);
    }
    
    function updateReadingGuide(e) {
        if (readingGuideElement) {
            readingGuideElement.style.top = (e.clientY + window.scrollY) + 'px';
        }
    }
    
    function saveAccessibilitySettings() {
        const settings = {
            fontSize: currentFontSize,
            highContrast: isHighContrast,
            grayscale: isGrayscale,
            highlightLinks: isLinksHighlighted,
            readingGuide: isReadingGuideActive
        };
        localStorage.setItem('accessibilitySettings', JSON.stringify(settings));
    }
    
    function loadAccessibilitySettings() {
        const saved = localStorage.getItem('accessibilitySettings');
        if (saved) {
            const settings = JSON.parse(saved);
            currentFontSize = settings.fontSize || 0;
            isHighContrast = settings.highContrast || false;
            isGrayscale = settings.grayscale || false;
            isLinksHighlighted = settings.highlightLinks || false;
            isReadingGuideActive = settings.readingGuide || false;
            
            // Apply settings
            updateFontSize();
            
            if (isHighContrast) {
                document.body.classList.add('high-contrast');
                toggleContrast.classList.add('active');
            }
            
            if (isGrayscale) {
                document.body.classList.add('grayscale');
                toggleGrayscale.classList.add('active');
            }
            
            if (isLinksHighlighted) {
                document.body.classList.add('highlight-links');
                highlightLinks.classList.add('active');
            }
            
            if (isReadingGuideActive) {
                createReadingGuide();
                readingGuide.classList.add('active');
            }
        }
    }
});