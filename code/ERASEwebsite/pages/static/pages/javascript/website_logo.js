document.addEventListener('DOMContentLoaded', () => {
    const uploadButton = document.getElementById('choose-logo');
    const fileInput = document.getElementById('id_logo');

    if (!uploadButton || !(fileInput instanceof HTMLInputElement)) {
        return;
    }

    uploadButton.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileInput.form.requestSubmit();
        }
    });
});
