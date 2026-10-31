document.addEventListener('DOMContentLoaded', () => {
    const dialog = document.getElementById('about-profile-dialog');
    const openButton = document.getElementById('open-profile-dialog');
    const closeButton = document.getElementById('close-profile-dialog');
    const cancelButton = document.getElementById('cancel-profile-dialog');

    if (!dialog) {
        return;
    }

    const closeDialog = () => {
        dialog.classList.remove('open');
        openButton?.focus();
    };

    openButton?.addEventListener('click', () => {
        dialog.classList.add('open');
        closeButton?.focus();
    });
    closeButton?.addEventListener('click', closeDialog);
    cancelButton?.addEventListener('click', closeDialog);
    dialog.addEventListener('click', (event) => {
        if (event.target === dialog) {
            closeDialog();
        }
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && dialog.classList.contains('open')) {
            closeDialog();
        }
    });

    if (dialog.dataset.openOnLoad === 'true') {
        dialog.classList.add('open');
        closeButton?.focus();
    }
});
