const config = JSON.parse(document.getElementById('calendar-config').textContent);
const rsvpedIds = new Set(JSON.parse(document.getElementById('rsvped-ids-data').textContent));
let modalTrigger = null;

function showCalendarModal(id) {
    modalTrigger = document.activeElement;
    const overlay = document.getElementById(id);
    overlay.classList.add('open');
    overlay.querySelector('.modal-box').focus();
    document.body.classList.add('calendar-modal-open');
}

function hideCalendarModal(id) {
    document.getElementById(id).classList.remove('open');
    document.body.classList.remove('calendar-modal-open');
    modalTrigger?.focus();
}

function openModal() {
    showCalendarModal('event-modal-overlay');
}

function closeModal() {
    hideCalendarModal('event-modal-overlay');
}

document.getElementById('event-modal-overlay')?.addEventListener('click', function(e) {
    if (e.target === this) closeModal();
});

function openEventDetailModal(pill) {
    const eventId = pill.dataset.eventId;
    const title = pill.dataset.title;
    const time = pill.dataset.time;
    const desc = pill.dataset.description;
    const hasRsvp = pill.dataset.hasRsvp === 'true';

    document.getElementById('detail-title').textContent = title;
    document.getElementById('detail-time').textContent = time;
    document.getElementById('detail-description').textContent = desc;

    const rsvpForm = document.getElementById('rsvp-form');
    const rsvpBtn = document.getElementById('rsvp-btn');

    if (hasRsvp && config.isAuthenticated) {
        rsvpForm.action = config.rsvpUrlTemplate.replace('/0/', `/${eventId}/`);
        rsvpForm.style.display = 'block';

        if (rsvpedIds.has(parseInt(eventId))) {
            rsvpBtn.textContent = config.labelCancelRsvp;
            rsvpBtn.classList.add('rsvped');
        } else {
            rsvpBtn.textContent = config.labelRsvp;
            rsvpBtn.classList.remove('rsvped');
        }
    } else {
        rsvpForm.style.display = 'none';
    }

    showCalendarModal('event-detail-overlay');
}

function closeEventDetailModal() {
    hideCalendarModal('event-detail-overlay');
}

document.getElementById('event-detail-overlay')?.addEventListener('click', function(e) {
    if (e.target === this) closeEventDetailModal();
});

document.addEventListener('keydown', event => {
    const overlay = document.querySelector('.modal-overlay.open');
    if (!overlay) return;
    if (event.key === 'Escape') hideCalendarModal(overlay.id);
    if (event.key !== 'Tab') return;
    const controls = [...overlay.querySelectorAll('button, input, textarea, select, a[href]')]
        .filter(control => !control.disabled && control.getClientRects().length);
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && (document.activeElement === first || document.activeElement.classList.contains('modal-box'))) {
        event.preventDefault();
        last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
    }
});
