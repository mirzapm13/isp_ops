console.log("okonstol")

frappe.router.on('change', () => {
    const route = frappe.get_route();
    
    // Check if we are on the List view for your target DocTypes
    if (route && route[0] === 'List' && (route[1] === 'HD Ticket' || route[1] === 'Installation Request')) {
        let targetWorkspace = 'isp-ticketing'; // Your workspace name slug

        // 1. Force Frappe's workspace manager state if available
        if (frappe.workspace_manager) {
            if (typeof frappe.workspace_manager.set_current_workspace === 'function') {
                frappe.workspace_manager.set_current_workspace(targetWorkspace);
            }
            if (frappe.workspace_manager.current_workspace !== targetWorkspace) {
                frappe.workspace_manager.current_workspace = targetWorkspace;
            }
        }

        // 2. Adjust the sidebar active states in the DOM to highlight "ISP Ticketing"
        setTimeout(() => {
            document.querySelectorAll('.standard-sidebar-item, .sidebar-item-container').forEach(el => {
                if (el.getAttribute('data-page-name') === targetWorkspace || el.innerText.includes('ISP Ticketing')) {
                    el.classList.add('active');
                } else {
                    el.classList.remove('active');
                }
            });
        }, 200);
    }
});