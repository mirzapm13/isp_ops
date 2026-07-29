// route_workspace_pin.js
// v16 Desk: Patch the REAL set_workspace_sidebar(router) and preserve the CURRENT workspace/sidebar
// for ANY route (Pages, Reports, Lists, Forms, etc.).
//
// Behavior:
// - When user is on a Workspace route: remember it as "active workspace".
// - When user navigates anywhere else (Page/Report/List/Form/anything):
//     - if the remembered workspace is a valid sidebar option for the current entity_name,
//       force it and STOP ERPNext's module-based resolver (prevents snap-back to Invoicing).
// - Also learns from whatever ERPNext ends up setting as sidebar_title.
//
// Include via hooks.py:
// app_include_js = ["/assets/<your_app>/js/route_workspace_pin.js"]

(function () {
  const LS_KEY = "rs:last_active_workspace";

  // ---------- helpers ----------
  function safe_get_route() {
    try {
      return (window.frappe && frappe.get_route && frappe.get_route()) || [];
    } catch (e) {
      return [];
    }
  }

  function remember_workspace(name) {
    if (!name || typeof name !== "string") return;
    const ws = name.trim();
    if (!ws) return;

    remember_workspace._last = ws;

    try {
      localStorage.setItem(LS_KEY, ws);
    } catch (e) {}
  }

  function get_remembered_workspace() {
    if (remember_workspace._last) return remember_workspace._last;
    try {
      const v = localStorage.getItem(LS_KEY);
      if (v && v.trim()) return v.trim();
    } catch (e) {}
    return null;
  }

  function route_workspace(route) {
    // ['Workspaces', 'Retail Workspace'] OR ['Workspaces','private','Retail Workspace']
    if (!Array.isArray(route) || route.length < 2) return null;
    if (route[0] !== "Workspaces") return null;
    if (route[1] === "private") return route[2] || null;
    return route[1] || null;
  }

  // This is the "entity_name" ERPNext uses inside set_workspace_sidebar():
  // - For List/Form/Report/Page routes, it's typically route[1]
  // - But for some shapes it differs; we mimic the logic you pasted.
  function compute_entity_name(route) {
    if (!Array.isArray(route) || route.length < 2) return null;

    let entity_name;

    switch (route.length) {
      case 1:
        // The original code you posted has a bug (route[1] doesn't exist when length==1),
        // but we'll keep a safe interpretation:
        entity_name = route[0] || null;
        break;

      case 2:
        // Example: ['Workspaces','Retail Workspace'] or ['Page','some-page']
        entity_name = route[1] || null;
        // Handle "workspace item" quick routing the core checks:
        // if (frappe.boot.workspace_sidebar_item[entity_name.toLowerCase()]) ...
        break;

      case 3:
        // Example: ['List','Sales Invoice','List'] -> entity_name = 'Sales Invoice'
        entity_name = route[1] || null;
        if (route[0] === "Workspaces" && route[1] === "private") {
          entity_name = route[2] || null;
        }
        break;

      default:
        entity_name = route[1] || null;
    }

    if (typeof entity_name !== "string") return null;
    entity_name = entity_name.trim();
    return entity_name || null;
  }

  function force_sidebar(ws_ctrl, workspace_name) {
    try {
      if (frappe?.app?.sidebar?.setup) {
        frappe.app.sidebar.setup(workspace_name);
      }
      ws_ctrl.sidebar_title = workspace_name;
      ws_ctrl.preferred_sidebars = [workspace_name];

      if (typeof ws_ctrl.set_active_workspace_item === "function") {
        ws_ctrl.set_active_workspace_item();
      }
    } catch (e) {
      console.log(e);
    }
  }

  // Deep search an object graph to find the controller with set_workspace_sidebar(router)
  function deep_find_controller(root, maxDepth = 7) {
    const seen = new WeakSet();

    function dfs(node, depth) {
      if (!node || typeof node !== "object") return null;
      if (seen.has(node)) return null;
      seen.add(node);

      if (
        typeof node.set_workspace_sidebar === "function" &&
        typeof node.get_workspace_sidebars === "function" &&
        typeof node.set_active_workspace_item === "function"
      ) {
        return node;
      }

      if (depth >= maxDepth) return null;

      for (const k of Object.keys(node)) {
        let v;
        try {
          v = node[k];
        } catch (e) {
          continue;
        }
        const found = dfs(v, depth + 1);
        if (found) return found;
      }

      return null;
    }

    return dfs(root, 0);
  }

  function find_controller() {
    if (!window.frappe) return null;

    const roots = [
      window.frappe,
      frappe.app,
      frappe.router,
      frappe.views,
      frappe.ui,
      frappe.model,
      frappe.breadcrumbs,
    ].filter(Boolean);

    for (const r of roots) {
      const ctrl = deep_find_controller(r, 7);
      if (ctrl) return ctrl;
    }

    // last resort, bounded search in window
    return deep_find_controller(window, 4);
  }

  // ---------- patch ----------
  function try_patch() {
    const ctrl = find_controller();
    if (!ctrl) return false;

    if (ctrl.__rs_workspace_patched) return true;
    ctrl.__rs_workspace_patched = true;

    const original = ctrl.set_workspace_sidebar.bind(ctrl);

    ctrl.set_workspace_sidebar = function (router) {
      try {
        const r = safe_get_route();

        // 1) If user is on a Workspace route, remember it and let core run
        const ws_from_route = route_workspace(r);
        if (ws_from_route) {
          remember_workspace(ws_from_route);
          return original(router);
        }

        // 2) For ANY other route, preserve remembered workspace (if valid for the entity)
        const desired_ws = get_remembered_workspace();
        const entity_name = compute_entity_name(r);

        if (desired_ws && entity_name) {
          // Validate that desired_ws is among available sidebars for this entity
          let sidebars = [];
          try {
            sidebars = this.get_workspace_sidebars(entity_name) || [];
          } catch (e) {}

          if (Array.isArray(sidebars) && sidebars.includes(desired_ws)) {
            force_sidebar(this, desired_ws);
            return; // <--- STOP module-based resolver from changing sidebar
          }
        }

        // 3) Default behavior
        const res = original(router);

        // 4) Learn from whatever core ends up selecting
        if (this.sidebar_title && typeof this.sidebar_title === "string") {
          remember_workspace(this.sidebar_title);
        }

        return res;
      } catch (e) {
        return original(router);
      }
    };

    console.log(
      ` Patched set_workspace_sidebar ✅ (preserve current workspace for all routes)`,
      "color:#4bb853;font-weight:700;",
    );

    return true;
  }

  // ---------- boot / retry ----------
  function boot() {
    let attempts = 0;
    const maxAttempts = 80; // ~8s @ 100ms

    const t = setInterval(() => {
      attempts += 1;
      const ok = try_patch();
      if (ok || attempts >= maxAttempts) clearInterval(t);
    }, 100);

    $(document).on("page-change", () => {
      try_patch();

      // Capture workspace if user navigated to it
      const r = safe_get_route();
      const ws = route_workspace(r);
      if (ws) remember_workspace(ws);
    });

    if (frappe.after_ajax) {
      frappe.after_ajax(() => {
        try_patch();
        const r = safe_get_route();
        const ws = route_workspace(r);
        if (ws) remember_workspace(ws);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
