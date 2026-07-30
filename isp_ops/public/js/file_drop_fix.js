document.addEventListener("dragover", function(e) {
    // Required to allow drop in Chrome
    e.preventDefault();
    if (e.dataTransfer) {
        e.dataTransfer.dropEffect = 'copy';
    }
}, false);

document.addEventListener("drop", function(e) {
    // Intercept drops globally to ensure Chrome handles the file list payload
    if (e.target.closest('.file-upload-area') || e.target.closest('.file-uploader')) {
        e.preventDefault();
        e.stopPropagation();

        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            // Locate Frappe's active uploader instance and feed the file directly
            const uploader = cur_frm?.attachments?.uploader || cur_dialog?.fields_dict?.file?.uploader;
            if (uploader && typeof uploader.add_file === 'function') {
                uploader.add_file(files[0]);
            }
        }
    }
}, false);