document.addEventListener('DOMContentLoaded', () => {
    const slideshow = document.getElementById('event-slideshow');
    if (!slideshow) {
        return;
    }

    const slides = Array.from(slideshow.querySelectorAll('.event-slide'));
    const position = slideshow.querySelector('.event-slide-position');
    const buttons = slideshow.querySelectorAll('[data-slide-direction]');
    if (slides.length < 2) {
        return;
    }

    let activeIndex = 0;
    let rotationTimer;
    let interacted = false;

    const showSlide = (index) => {
        activeIndex = (index + slides.length) % slides.length;
        slides.forEach((slide, slideIndex) => {
            const isActive = slideIndex === activeIndex;
            slide.hidden = !isActive;
            slide.classList.toggle('active', isActive);
        });
        if (position) {
            position.textContent = `${activeIndex + 1} / ${slides.length}`;
        }
    };

    const stopRotation = () => {
        interacted = true;
        window.clearInterval(rotationTimer);
    };

    buttons.forEach((button) => {
        button.addEventListener('click', () => {
            stopRotation();
            showSlide(activeIndex + Number(button.dataset.slideDirection));
        });
    });

    ['pointerdown', 'keydown', 'focusin', 'mouseenter', 'touchstart'].forEach((eventName) => {
        slideshow.addEventListener(eventName, stopRotation, { once: true, passive: true });
    });

    showSlide(activeIndex);
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        rotationTimer = window.setInterval(() => {
            if (!interacted) {
                showSlide(activeIndex + 1);
            }
        }, 6000);
    }
});
