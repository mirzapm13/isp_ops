// Copyright (c) 2026, Citra Angkasa Lintas Media and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Installation Request", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on("Installation Request", {
    refresh(frm) {

        if (frm.is_new() || frm.doc.status === "Draft") {

            frm.add_custom_button(__("Submit Document"), async () => {

                if (frm.is_new() || frm.is_dirty()) {
                    await frm.save();
                }

                await frappe.call({
                    method: "isp_ops.api.submit_installation_request",
                    args: {
                        installation_request: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __("Creating Helpdesk Ticket...")
                });

                frappe.show_alert({
                    message: __("Installation Request Submitted"),
                    indicator: "green"
                });

                await frm.reload_doc();

            }).addClass("btn-primary");

        }

    }
});