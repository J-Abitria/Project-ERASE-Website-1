(function () {
    const buttons = document.querySelectorAll('.tab-btn');
    const panes   = document.querySelectorAll('.tab-content');

    function activateTab(tabId) {
        buttons.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tabId));
        panes.forEach(pane => pane.classList.toggle('active', pane.id === 'tab-' + tabId));
    }

    buttons.forEach(btn => {
        btn.addEventListener('click', () => activateTab(btn.dataset.tab));
    });

    // Initial tab is rendered into HTML; static JavaScript is not Django-templated.
    const tabNavigation = document.querySelector('.report-tabs');
    const serverTab = tabNavigation ? tabNavigation.dataset.initialTab : 'fundraising';
    const urlTab    = new URLSearchParams(window.location.search).get('tab');
    const validTabs = new Set(['fundraising', 'workshops', 'students', 'social']);
    const initialTab = validTabs.has(urlTab) ? urlTab : (validTabs.has(serverTab) ? serverTab : 'fundraising');
    activateTab(initialTab);

    const dialog = document.getElementById('workshop-edit-dialog');
    const closeButtons = dialog?.querySelectorAll('[data-close-workshop-dialog]') ?? [];
    const editButtons = document.querySelectorAll('.workshop-edit-trigger');
    const editForm = dialog?.querySelector('form');
    let activeEditTrigger = null;
    const closeDialog = () => {
        dialog?.classList.remove('open');
        activeEditTrigger?.focus();
    };

    editButtons.forEach(button => {
        button.addEventListener('click', () => {
            if (!dialog || !editForm) return;

            editForm.elements.workshop_id.value = button.dataset.workshopId;
            editForm.elements.workshop_name.value = button.dataset.workshopName;
            editForm.elements.date.value = button.dataset.workshopDate;
            editForm.elements.location.value = button.dataset.workshopLocation;
            editForm.elements.attendee_count.value = button.dataset.workshopAttendees;
            editForm.elements.notes.value = button.dataset.workshopNotes;
            activeEditTrigger = button;
            dialog.classList.add('open');
            dialog.querySelector('[data-close-workshop-dialog]')?.focus();
        });
    });

    closeButtons.forEach(button => button.addEventListener('click', closeDialog));
    dialog?.addEventListener('click', event => {
        if (event.target === dialog) closeDialog();
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && dialog?.classList.contains('open')) {
            closeDialog();
        }
    });

    if (dialog?.dataset.openOnLoad === 'true') {
        dialog.classList.add('open');
        dialog.querySelector('[data-close-workshop-dialog]')?.focus();
    }
})();