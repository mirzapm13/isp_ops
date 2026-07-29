console.log("Frappe v16 Custom Web Form Script Loaded");

// Helper function to update the linked ticket in the background
function updateHDTicketStatus(statusValue) {
    // 1. Get the ticket ID from the web form field
    let hdTicketName = frappe.web_form.doc?.hd_ticket || (typeof frappe.web_form.get_value === 'function' ? frappe.web_form.get_value('hd_ticket') : null);
    
    if (!hdTicketName) {
        console.warn("No hd_ticket linked. Skipping status update.");
        return;
    }

    // 2. Call Frappe's native REST API to update the field
    fetch('/api/method/frappe.client.set_value', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Frappe-CSRF-Token': frappe.csrf_token
        },
        body: JSON.stringify({
            doctype: 'HD Ticket', // ⚠️ IMPORTANT: Change this if your actual Doctype name is different (e.g., 'Help Desk Ticket')
            name: hdTicketName,
            fieldname: 'status',
            value: statusValue
        })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.exc) {
            console.log(`✅ Linked HD Ticket updated to: ${statusValue}`);
        } else {
            console.error('Failed to update HD Ticket due to backend error/permissions', data.exc);
        }
    })
    .catch(err => console.error('Failed to update HD Ticket:', err));
}

function setupCustomWebFormUI() {
    if (document.getElementById('multi-photo-input') || document.getElementById('custom-pending-btn')) {
        return; 
    }
    
    let actionsRow = document.querySelector('.web-form-actions');
    let formContainer = document.querySelector('.web-form-page') || document.querySelector('.web-form-wrapper form') || document.querySelector('.web-form-body');

    if (!actionsRow || !formContainer) return;

    // --- SAVE / PENDING LOGIC ---
    let saveBtn = document.querySelector('.web-form-actions .btn-primary');
    window.is_pending_save = false; // Flag to tell the difference between Pending and Normal save

    // 1. Intercept Normal Save Button
    if (saveBtn) {
        // We use 'mousedown' instead of 'click' so our background fetch fires a microsecond BEFORE Frappe native save locks the UI
        saveBtn.addEventListener('mousedown', function() {
            if (window.is_pending_save) {
                // If the flag is true, our popup triggered this save. Reset the flag and do nothing else.
                window.is_pending_save = false;
            } else {
                // Otherwise, the user clicked standard Save/Submit -> Mark HD Ticket Resolved
                updateHDTicketStatus('Resolved');
            }
        });
    }

    // 2. Setup Pending Button
    let btnPending = document.createElement('button');
    btnPending.id = 'custom-pending-btn';
    btnPending.className = 'btn btn-warning btn-sm ml-2'; 
    btnPending.innerText = 'Pending';
    btnPending.style.marginLeft = '10px'; 
    
    btnPending.addEventListener('click', function(e) {
        e.preventDefault();
        
        let d = new frappe.ui.Dialog({
            title: 'Set Status to Pending',
            fields: [{ label: 'Survey Notes', fieldname: 'survey_notes', fieldtype: 'Small Text', reqd: 1 }],
            primary_action_label: 'Confirm & Save',
            primary_action(values) {
                // Update form fields
                frappe.web_form.set_value('installation_result', 'Pending');
                frappe.web_form.set_value('survey_notes', values.survey_notes);
                
                // --- NEW: Update linked HD Ticket via API ---
                updateHDTicketStatus('Pending');
                
                // Set flag to true so the normal save button ignores this click
                window.is_pending_save = true;
                
                d.hide();
                frappe.show_alert({message: "Saving as Pending...", indicator: "orange"});
                
                if (saveBtn) {
                    saveBtn.click();
                } else if (typeof frappe.web_form.save === 'function') {
                    frappe.web_form.save();
                }
            }
        });
        d.show();
    });

    actionsRow.appendChild(btnPending);

    // Hide native delete button
    let nativeDeleteBtn = document.querySelector('.delete-btn');
    if (nativeDeleteBtn) {
        nativeDeleteBtn.style.display = 'none';
    }
    
    // --- UPLOADER LOGIC ---
    let uploaderDiv = document.createElement('div');
    uploaderDiv.innerHTML = `
        <div style="padding: 15px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; margin: 20px 0;">
            <label style="font-weight: bold; margin-bottom: 10px; display: block;">Attach Multiple Photos</label>
            <input type="file" id="multi-photo-input" multiple accept="image/*" style="display: block; margin-bottom: 5px;">
            <div id="upload-status" style="margin-top: 10px; font-size: 13px; color: #16a34a;"></div>
            <div id="image-preview-gallery" style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;"></div>
        </div>
    `;

    formContainer.appendChild(uploaderDiv);

    document.getElementById('multi-photo-input').addEventListener('change', function() {
        let files = this.files;
        let statusDiv = document.getElementById('upload-status');
        let galleryDiv = document.getElementById('image-preview-gallery');
        
        if (files.length === 0) return;

        const pathArray = window.location.pathname.split('/');
        let docnameFromUrl = pathArray.pop() || pathArray.pop(); 
        const docname = frappe.web_form?.doc?.name || docnameFromUrl; 
        const doctype = "Installation Request"; 

        if (!docname || docname === "new") {
            frappe.msgprint("Cannot upload: Missing ticket ID. Please save the form first.");
            this.value = ""; 
            return;
        }

        statusDiv.innerHTML = "Uploading...";

        Array.from(files).forEach(file => {
            let formData = new FormData();
            formData.append("file", file, file.name);
            formData.append("doctype", doctype);
            formData.append("docname", docname);
            formData.append("is_private", 0); 

            fetch('/api/method/upload_file', {
                method: 'POST',
                headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if(data.message && data.message.file_url) {
                    statusDiv.innerHTML += `<br>✅ Uploaded: ${file.name}`;
                    let fileDocName = data.message.name; 
                    
                    let imgWrapper = document.createElement('div');
                    imgWrapper.style.cssText = "position: relative; width: 100px; height: 100px; border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);";
                    
                    let img = document.createElement('img');
                    img.src = data.message.file_url;
                    img.alt = file.name;
                    img.style.cssText = "width: 100%; height: 100%; object-fit: cover;"; 
                    
                    let deleteBtn = document.createElement('button');
                    deleteBtn.innerHTML = "&times;";
                    deleteBtn.title = "Delete Photo";
                    deleteBtn.style.cssText = "position: absolute; top: 4px; right: 4px; background: rgba(220, 38, 38, 0.9); color: white; border: none; border-radius: 50%; width: 20px; height: 20px; font-size: 14px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; padding-bottom: 2px;";
                    
                    deleteBtn.addEventListener('click', function(e) {
                        e.preventDefault(); 
                        if (confirm("Are you sure you want to delete this photo?")) {
                            fetch(`/api/resource/File/${fileDocName}`, {
                                method: 'DELETE',
                                headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token }
                            })
                            .then(res => {
                                if (res.ok) {
                                    imgWrapper.remove();
                                    statusDiv.innerHTML += `<br>🗑️ Deleted: ${file.name}`;
                                }
                            });
                        }
                    });
                    
                    imgWrapper.appendChild(img);
                    imgWrapper.appendChild(deleteBtn);
                    galleryDiv.appendChild(imgWrapper);
                }
            })
            .catch(error => {
                console.error('Upload failed', error);
                statusDiv.innerHTML += `<br>❌ Failed: ${file.name}`;
            });
        });
        
        this.value = "";
    });
}

// 3. The Clean Event-Driven Loader (MutationObserver)
frappe.ready(function() {
    const observer = new MutationObserver((mutations, obs) => {
        let actionsRow = document.querySelector('.web-form-actions');
        let formContainer = document.querySelector('.web-form-page') || document.querySelector('.web-form-wrapper form') || document.querySelector('.web-form-body');

        if (actionsRow && formContainer) {
            setupCustomWebFormUI();
            obs.disconnect();
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});