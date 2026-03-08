/* 
   Quant Pattern — Marketing Site Interactivity
   Theme Toggle + Animations + Form Handling
    */

document.addEventListener('DOMContentLoaded', () => {
    //  Generate Stars 
    createStars();

    //  Theme Toggle 
    initThemeToggle();

    //  Navbar Scroll Effect 
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 50);
    });

    //  Mobile Nav Toggle 
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
            const spans = navToggle.querySelectorAll('span');
            if (navLinks.classList.contains('open')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -5px)';
            } else {
                spans[0].style.transform = '';
                spans[1].style.opacity = '';
                spans[2].style.transform = '';
            }
        });

        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('open');
                const spans = navToggle.querySelectorAll('span');
                spans[0].style.transform = '';
                spans[1].style.opacity = '';
                spans[2].style.transform = '';
            });
        });
    }

    //  Intersection Observer for Animations 
    const observerOptions = {
        threshold: 0.12,
        rootMargin: '0px 0px -40px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                const delay = entry.target.dataset.delay || 0;
                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, delay * 120);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right, .scale-in').forEach((el, i) => {
        el.dataset.delay = i % 5;
        observer.observe(el);
    });

    //  Animated Counters 
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('[data-count]').forEach(el => {
        counterObserver.observe(el);
    });

    //  Form Handling 
    const form = document.getElementById('leadForm');
    const formContent = document.getElementById('formContent');
    const formSuccess = document.getElementById('formSuccess');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = form.querySelector('#submit-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Submitting...';

            const formData = {
                email: form.querySelector('#email').value,
                mobile: form.querySelector('#mobile').value,
                idea: form.querySelector('#idea').value,
            };

            const API = window.location.hostname === 'localhost'
                ? 'http://localhost:8000'
                : 'https://app.quant-pattern.com';

            try {
                const res = await fetch(`${API}/api/leads`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                if (!res.ok) throw new Error('API error');
            } catch {
                // Fallback to localStorage if API is unreachable
                const leads = JSON.parse(localStorage.getItem('qp_leads') || '[]');
                leads.push({ ...formData, timestamp: new Date().toISOString() });
                localStorage.setItem('qp_leads', JSON.stringify(leads));
            }

            formContent.style.display = 'none';
            formSuccess.classList.add('show');
            showToast('Your inquiry has been submitted! We\'ll reach out shortly.');
        });
    }

    //  Smooth Scroll for Anchor Links 
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                const offset = 80;
                const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        });
    });

    //  Subtle Parallax on Hero Glows 
    window.addEventListener('scroll', () => {
        const scrolled = window.scrollY;
        document.querySelectorAll('.hero-bg-glow').forEach((glow, i) => {
            const speed = 0.03 + (i * 0.01);
            glow.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });

    //  Tilt effect on hero chart card 
    const chartCard = document.querySelector('.hero-chart-card');
    if (chartCard && window.innerWidth > 1024) {
        chartCard.addEventListener('mousemove', (e) => {
            const rect = chartCard.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            chartCard.style.transform = `perspective(800px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg)`;
        });
        chartCard.addEventListener('mouseleave', () => {
            chartCard.style.transform = 'perspective(800px) rotateY(0) rotateX(0)';
            chartCard.style.transition = 'transform 0.5s ease';
        });
        chartCard.addEventListener('mouseenter', () => {
            chartCard.style.transition = 'transform 0.1s ease';
        });
    }
});


//  Theme Toggle 
function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    if (!toggle) return;

    // Load saved preference
    const savedTheme = localStorage.getItem('qp_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);

    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('qp_theme', next);
        showToast(next === 'light' ? 'Light mode activated' : 'Dark mode activated');
    });
}


//  Helper: Create Stars 
function createStars() {
    const container = document.querySelector('.stars-container');
    if (!container) return;
    const count = 120;

    for (let i = 0; i < count; i++) {
        const star = document.createElement('div');
        star.className = 'star';
        star.style.left = Math.random() * 100 + '%';
        star.style.top = Math.random() * 100 + '%';
        star.style.setProperty('--duration', (2 + Math.random() * 4) + 's');
        star.style.setProperty('--max-opacity', (0.3 + Math.random() * 0.5).toFixed(2));
        star.style.animationDelay = (Math.random() * 5) + 's';
        star.style.width = star.style.height = (1 + Math.random() * 2) + 'px';
        container.appendChild(star);
    }
}

//  Helper: Animate Counter 
function animateCounter(element) {
    const target = parseFloat(element.dataset.count);
    const suffix = element.dataset.suffix || '';
    const prefix = element.dataset.prefix || '';
    const decimal = element.dataset.decimal ? parseInt(element.dataset.decimal) : 0;
    const duration = 2200;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = 1 - Math.pow(1 - progress, 3);
        const current = target * ease;

        element.textContent = prefix + current.toFixed(decimal) + suffix;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

//  Helper: Toast Notification 
function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}
