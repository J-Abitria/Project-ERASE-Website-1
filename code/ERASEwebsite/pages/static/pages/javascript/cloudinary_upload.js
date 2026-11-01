document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('form[data-cloudinary-upload]').forEach((form) => {
        const fileInput = form.querySelector(
            'input[type="file"][name="image"], input[type="file"][name="logo"], input[type="file"][name="featured_image"]'
        );
        const status = form.querySelector('[data-cloudinary-upload-status]');
        const publicIdInput = form.elements.direct_upload_public_id;
        const versionInput = form.elements.direct_upload_version;
        const signatureInput = form.elements.direct_upload_signature;

        if (!(fileInput instanceof HTMLInputElement) || !status) {
            return;
        }

        fileInput.addEventListener('change', () => {
            publicIdInput.value = '';
            versionInput.value = '';
            signatureInput.value = '';
            form.dataset.cloudinaryUploaded = 'false';
        });

        form.addEventListener('submit', async (event) => {
            const file = fileInput.files?.[0];
            if (!file || form.dataset.cloudinaryUploaded === 'true') {
                return;
            }

            event.preventDefault();
            if (
                form.dataset.cloudinaryUpload !== 'blog_image'
                && !/\.(jpe?g|png)$/i.test(file.name)
            ) {
                status.hidden = false;
                status.textContent = 'Choose a JPG or PNG image.';
                return;
            }
            if (form.dataset.cloudinaryUploading === 'true') {
                return;
            }
            form.dataset.cloudinaryUploading = 'true';
            const submitButton = event.submitter;
            if (submitButton instanceof HTMLButtonElement) {
                submitButton.disabled = true;
            }
            fileInput.disabled = true;
            status.hidden = false;
            status.textContent = 'Uploading image…';

            try {
                const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]')?.value;
                const signingResponse = await fetch(form.dataset.signatureUrl, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken,
                    },
                    body: new URLSearchParams({ purpose: form.dataset.cloudinaryUpload }),
                });
                const signingResult = await signingResponse.json();
                if (!signingResponse.ok) {
                    throw new Error(signingResult.error || 'Could not authorize the image upload.');
                }

                const uploadData = new FormData();
                uploadData.append('file', file);
                Object.entries(signingResult.params).forEach(([key, value]) => {
                    uploadData.append(key, String(value));
                });

                const uploadResponse = await fetch(signingResult.upload_url, {
                    method: 'POST',
                    body: uploadData,
                });
                const asset = await uploadResponse.json();
                if (!uploadResponse.ok) {
                    if (uploadResponse.status === 401) {
                        throw new Error(
                            'Cloudinary authorization failed. Verify the Vercel Production CLOUDINARY_URL and upload permissions.'
                        );
                    }
                    throw new Error(asset.error?.message || 'Cloudinary rejected the image upload.');
                }

                publicIdInput.value = asset.public_id;
                versionInput.value = String(asset.version);
                signatureInput.value = asset.signature;
                form.dataset.cloudinaryUploaded = 'true';
                form.dataset.cloudinaryUploading = 'false';
                fileInput.disabled = true;
                status.textContent = 'Image uploaded. Saving…';

                if (submitButton instanceof HTMLButtonElement) {
                    submitButton.disabled = false;
                    form.requestSubmit(submitButton);
                } else {
                    form.requestSubmit();
                }
            } catch (error) {
                form.dataset.cloudinaryUploading = 'false';
                fileInput.disabled = false;
                if (submitButton instanceof HTMLButtonElement) {
                    submitButton.disabled = false;
                }
                status.textContent = error instanceof Error
                    ? error.message
                    : 'Image upload failed. Check Cloudinary configuration and try again.';
            }
        });
    });
});
