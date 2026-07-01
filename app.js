/* LLMwiki Frontend Application Logic - Multi-User, Multi-Project Edition */

document.addEventListener("DOMContentLoaded", () => {
    // ==========================================
    // APPLICATION STATE
    // ==========================================
    const state = {
        // Authentication
        user: null,
        token: null,
        
        // Projects
        projects: [],
        selectedProjectId: null,
        
        // Wiki Data
        config: {
            api_key_configured: false,
            masked_key: "",
            default_model: "gemini-1.5-flash"
        },
        rawFiles: [],
        wikiPages: [],
        selectedRawFile: null,
        selectedWikiPage: null,
        isEditing: false,
        activeTab: "reader", // "reader" or "graph"
        activeAgentTab: "ingest", // "ingest", "query", "lint"
        draftedPage: null, // holds response from query agent to be saved
        graphData: { nodes: [], links: [] }
    };

    // DOM Elements
    const elements = {
        // Auth Screens
        authScreen: document.getElementById("auth-screen"),
        appScreen: document.getElementById("app-screen"),
        loginForm: document.getElementById("login-form"),
        registerForm: document.getElementById("register-form"),
        loginUsername: document.getElementById("login-username"),
        loginPassword: document.getElementById("login-password"),
        registerUsername: document.getElementById("register-username"),
        registerEmail: document.getElementById("register-email"),
        registerPassword: document.getElementById("register-password"),
        loginError: document.getElementById("login-error"),
        registerError: document.getElementById("register-error"),
        linkToRegister: document.getElementById("link-to-register"),
        linkToLogin: document.getElementById("link-to-login"),

        // Navigation & Status
        apiStatusBadge: document.getElementById("api-status-badge"),
        btnSettings: document.getElementById("btn-settings"),
        selectModel: document.getElementById("select-model"),
        projectSelect: document.getElementById("project-select"),
        btnNewProject: document.getElementById("btn-new-project"),
        btnUserMenu: document.getElementById("btn-user-menu"),
        userDropdown: document.getElementById("user-dropdown"),
        currentUser: document.getElementById("current-user"),
        currentUserId: document.getElementById("current-user-id"),
        btnLogout: document.getElementById("btn-logout"),
        btnLogoutHeader: document.getElementById("btn-logout-header"),
        
        // Sidebar Lists
        rawFileList: document.getElementById("raw-file-list"),
        uploadProjectBanner: document.getElementById("upload-project-banner"),
        wikiFileList: document.getElementById("wiki-file-list"),
        wikiCountBadge: document.getElementById("wiki-count"),
        fileUploader: document.getElementById("file-uploader"),
        btnUploadTrigger: document.getElementById("btn-upload-trigger"),
        
        // Workspace Tabs
        tabReader: document.getElementById("tab-reader"),
        tabGraph: document.getElementById("tab-graph"),
        readerView: document.getElementById("reader-view"),
        graphView: document.getElementById("graph-view"),
        
        // Reader / Editor Elements
        pageTitle: document.getElementById("page-title"),
        pageMetadata: document.getElementById("page-metadata"),
        metaTags: document.getElementById("meta-tags"),
        metaUpdated: document.getElementById("meta-updated"),
        metaType: document.getElementById("meta-type"),
        headerDivider: document.getElementById("divider"),
        markdownRenderer: document.getElementById("markdown-renderer"),
        editorContainer: document.getElementById("editor-container"),
        markdownEditor: document.getElementById("markdown-editor"),
        btnEditPage: document.getElementById("btn-edit-page"),
        btnSavePage: document.getElementById("btn-save-page"),
        btnCancelEdit: document.getElementById("btn-cancel-edit"),
        
        // Agent Control Tabs
        agentTabIngest: document.getElementById("agent-tab-ingest"),
        agentTabQuery: document.getElementById("agent-tab-query"),
        agentTabLint: document.getElementById("agent-tab-lint"),
        panelIngest: document.getElementById("panel-ingest"),
        panelQuery: document.getElementById("panel-query"),
        panelLint: document.getElementById("panel-lint"),
        
        // Ingest Panel
        selectedRawFileName: document.getElementById("selected-raw-file-name"),
        btnIngestFile: document.getElementById("btn-ingest-file"),
        ingestTerminal: document.getElementById("ingest-terminal"),
        
        // Query Panel
        queryChatHistory: document.getElementById("query-chat-history"),
        queryInput: document.getElementById("query-input"),
        btnSubmitQuery: document.getElementById("btn-submit-query"),
        savePageCard: document.getElementById("save-page-card"),
        draftFilename: document.getElementById("draft-filename"),
        btnSaveDraft: document.getElementById("btn-save-draft"),
        
        // Lint Panel
        btnRunLint: document.getElementById("btn-run-lint"),
        lintTerminal: document.getElementById("lint-terminal"),
        
        // Settings Modal
        settingsModal: document.getElementById("settings-modal"),
        inputApiKey: document.getElementById("input-api-key"),
        btnSaveSettings: document.getElementById("btn-save-settings"),
        btnCloseSettings: document.getElementById("btn-close-settings"),
        configStatusMsg: document.getElementById("config-status-msg"),

        // Project Modal
        newProjectModal: document.getElementById("new-project-modal"),
        btnCloseProjectModal: document.getElementById("btn-close-project-modal"),
        btnCancelProject: document.getElementById("btn-cancel-project"),
        btnCreateProject: document.getElementById("btn-create-project"),
        projectName: document.getElementById("project-name"),
        projectDescription: document.getElementById("project-description"),
        projectModalError: document.getElementById("project-modal-error"),

        // Project Sharing
        btnShareProject: document.getElementById("btn-share-project"),
        btnViewMembers: document.getElementById("btn-view-members"),
        shareModal: document.getElementById("share-modal"),
        btnCloseShareModal: document.getElementById("btn-close-share-modal"),
        btnCancelShare: document.getElementById("btn-cancel-share"),
        btnConfirmShare: document.getElementById("btn-confirm-share"),
        shareUsername: document.getElementById("share-username"),
        sharePermission: document.getElementById("share-permission"),
        shareModalError: document.getElementById("share-modal-error"),

        // Members Modal
        membersModal: document.getElementById("members-modal"),
        btnCloseMembersModal: document.getElementById("btn-close-members-modal"),
        btnCloseMembers: document.getElementById("btn-close-members"),
        membersList: document.getElementById("members-list")
    };

    // Initialize UI Icons
    lucide.createIcons();

    const originalFetch = window.fetch.bind(window);
    window.fetch = async (input, init = {}) => {
        let url = typeof input === "string" ? input : input.url;

        if (typeof url === "string" && url.startsWith("/api/")) {
            const requiresProject = ["/api/files/raw", "/api/files/wiki", "/api/graph", "/api/ingest", "/api/query", "/api/query/save", "/api/lint"];
            const projectScoped = requiresProject.some((p) => url === p || url.startsWith(p + "/"));

            if (projectScoped) {
                if (!state.selectedProjectId) {
                    throw new Error("Please select a project first.");
                }

                if (url === "/api/files/raw") url = `/api/projects/${state.selectedProjectId}/files/raw`;
                else if (url === "/api/files/raw/upload") url = `/api/projects/${state.selectedProjectId}/files/raw/upload`;
                else if (url === "/api/files/wiki") url = `/api/projects/${state.selectedProjectId}/files/wiki`;
                else if (url.startsWith("/api/files/wiki/")) url = `/api/projects/${state.selectedProjectId}/files/wiki/${url.split("/api/files/wiki/")[1]}`;
                else if (url === "/api/graph") url = `/api/projects/${state.selectedProjectId}/graph`;
                else if (url === "/api/ingest") url = `/api/projects/${state.selectedProjectId}/ingest`;
                else if (url === "/api/query") url = `/api/projects/${state.selectedProjectId}/query`;
                else if (url === "/api/query/save") url = `/api/projects/${state.selectedProjectId}/query/save`;
                else if (url === "/api/lint") url = `/api/projects/${state.selectedProjectId}/lint`;
            }

            const isAuthEndpoint = url.startsWith("/api/auth/");
            const headers = new Headers(init.headers || {});
            if (state.token && !isAuthEndpoint && !headers.has("Authorization")) {
                headers.set("Authorization", `Bearer ${state.token}`);
            }
            init.headers = headers;
        }

        return originalFetch(url, init);
    };

    function showError(el, msg) {
        if (!el) return;
        el.textContent = msg;
        el.classList.remove("hidden");
    }

    function clearError(el) {
        if (!el) return;
        el.textContent = "";
        el.classList.add("hidden");
    }

    function showAuthScreen() {
        elements.authScreen.classList.remove("hidden");
        elements.appScreen.classList.add("hidden");
    }

    function showAppScreen() {
        elements.authScreen.classList.add("hidden");
        elements.appScreen.classList.remove("hidden");
        elements.currentUser.textContent = state.user?.username || "User";
        elements.currentUserId.textContent = `ID: ${state.user?.id ?? "-"}`;
    }

    function setSession(authPayload) {
        state.token = authPayload.access_token;
        state.user = authPayload.user;
        localStorage.setItem("llmwiki_token", state.token);
    }

    function clearSession() {
        state.token = null;
        state.user = null;
        state.selectedProjectId = null;
        state.projects = [];
        localStorage.removeItem("llmwiki_token");
    }

    function switchAuthForm(mode) {
        if (mode === "register") {
            elements.loginForm.classList.remove("active");
            elements.registerForm.classList.add("active");
        } else {
            elements.registerForm.classList.remove("active");
            elements.loginForm.classList.add("active");
        }
        clearError(elements.loginError);
        clearError(elements.registerError);
    }

    function renderProjectOptions() {
        const select = elements.projectSelect;
        select.innerHTML = '<option value="">Select Project...</option>';
        state.projects.forEach((p) => {
            const opt = document.createElement("option");
            opt.value = String(p.id);
            opt.textContent = p.name;
            if (String(p.id) === String(state.selectedProjectId)) {
                opt.selected = true;
            }
            select.appendChild(opt);
        });

        elements.btnUploadTrigger.disabled = !state.selectedProjectId;
        elements.uploadProjectBanner.classList.toggle("hidden", !!state.selectedProjectId);
        updateProjectSettingsState();
    }

    function getSelectedProject() {
        if (!state.selectedProjectId) return null;
        return state.projects.find((p) => String(p.id) === String(state.selectedProjectId)) || null;
    }

    function updateProjectSettingsState() {
        const selectedProject = getSelectedProject();
        const hasProject = !!selectedProject;
        const isOwner = !!(selectedProject && selectedProject.is_owner);

        elements.btnShareProject.disabled = !hasProject || !isOwner;
        elements.btnViewMembers.disabled = !hasProject;
    }

    async function fetchProjects() {
        const res = await fetch("/api/projects");
        if (!res.ok) throw new Error("Unable to load projects");
        state.projects = await res.json();
        renderProjectOptions();

        if (!state.selectedProjectId && state.projects.length > 0) {
            state.selectedProjectId = state.projects[0].id;
            renderProjectOptions();
        }

        if (state.selectedProjectId) {
            await Promise.all([fetchRawFiles(), fetchWikiPages()]);
        }
    }

    async function restoreSession() {
        const savedToken = localStorage.getItem("llmwiki_token");
        if (!savedToken) {
            showAuthScreen();
            return;
        }

        try {
            state.token = savedToken;
            const res = await fetch("/api/auth/me", {
                headers: { Authorization: `Bearer ${savedToken}` }
            });
            if (!res.ok) throw new Error("Session expired");
            state.user = await res.json();
            showAppScreen();
            await fetchProjects();
        } catch {
            clearSession();
            showAuthScreen();
        }
    }

    elements.linkToRegister.addEventListener("click", (e) => {
        e.preventDefault();
        switchAuthForm("register");
    });

    elements.linkToLogin.addEventListener("click", (e) => {
        e.preventDefault();
        switchAuthForm("login");
    });

    elements.registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearError(elements.registerError);

        const username = elements.registerUsername.value.trim();
        const email = elements.registerEmail.value.trim();
        const password = elements.registerPassword.value;

        try {
            const res = await fetch("/api/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, password })
            });
            const data = await res.json();
            if (!res.ok) {
                showError(elements.registerError, data.detail || "Registration failed");
                return;
            }

            setSession(data);
            showError(elements.registerError, "Account created successfully. Redirecting...");
            setTimeout(async () => {
                showAppScreen();
                await fetchProjects();
            }, 500);
        } catch {
            showError(elements.registerError, "Unable to register right now. Please retry.");
        }
    });

    elements.loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        clearError(elements.loginError);

        const username = elements.loginUsername.value.trim();
        const password = elements.loginPassword.value;

        try {
            const res = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (!res.ok) {
                showError(elements.loginError, data.detail || "Invalid credentials");
                return;
            }

            setSession(data);
            showAppScreen();
            await fetchProjects();
        } catch {
            showError(elements.loginError, "Unable to login right now. Please retry.");
        }
    });

    elements.btnUserMenu.addEventListener("click", () => {
        elements.userDropdown.classList.toggle("hidden");
    });

    elements.btnLogout.addEventListener("click", (e) => {
        e.preventDefault();
        clearSession();
        showAuthScreen();
    });

    elements.btnLogoutHeader.addEventListener("click", () => {
        clearSession();
        showAuthScreen();
    });

    elements.projectSelect.addEventListener("change", async (e) => {
        const val = Number(e.target.value);
        state.selectedProjectId = Number.isFinite(val) && val > 0 ? val : null;
        elements.btnUploadTrigger.disabled = !state.selectedProjectId;
        elements.uploadProjectBanner.classList.toggle("hidden", !!state.selectedProjectId);
        updateProjectSettingsState();
        state.selectedRawFile = null;
        state.selectedWikiPage = null;
        if (state.selectedProjectId) {
            await Promise.all([fetchRawFiles(), fetchWikiPages()]);
        }
    });

    function openProjectModal() {
        clearError(elements.projectModalError);
        elements.projectName.value = "";
        elements.projectDescription.value = "";
        elements.newProjectModal.classList.remove("hidden");
    }

    function closeProjectModal() {
        elements.newProjectModal.classList.add("hidden");
    }

    elements.btnNewProject.addEventListener("click", openProjectModal);
    elements.btnCloseProjectModal.addEventListener("click", closeProjectModal);
    elements.btnCancelProject.addEventListener("click", closeProjectModal);

    elements.btnCreateProject.addEventListener("click", async () => {
        clearError(elements.projectModalError);
        const name = elements.projectName.value.trim();
        const description = elements.projectDescription.value.trim();
        if (!name) {
            showError(elements.projectModalError, "Project name is required.");
            return;
        }

        try {
            const res = await fetch("/api/projects", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, description })
            });
            const data = await res.json();
            if (!res.ok) {
                showError(elements.projectModalError, data.detail || "Failed to create project.");
                return;
            }

            closeProjectModal();
            state.selectedProjectId = data.id;
            await fetchProjects();
        } catch {
            showError(elements.projectModalError, "Unable to create project right now.");
        }
    });

    function openShareModal() {
        const selectedProject = getSelectedProject();
        if (!selectedProject) {
            return;
        }
        if (!selectedProject.is_owner) {
            showError(elements.shareModalError, "Only the project owner can share access.");
            return;
        }
        clearError(elements.shareModalError);
        elements.shareUsername.value = "";
        elements.sharePermission.value = "read_only";
        elements.shareModal.classList.remove("hidden");
    }

    function closeShareModal() {
        elements.shareModal.classList.add("hidden");
        clearError(elements.shareModalError);
    }

    async function shareSelectedProject() {
        const selectedProject = getSelectedProject();
        if (!selectedProject || !selectedProject.is_owner) {
            showError(elements.shareModalError, "Only the project owner can share access.");
            return;
        }

        const username = elements.shareUsername.value.trim();
        const permission_level = elements.sharePermission.value;
        if (!username) {
            showError(elements.shareModalError, "Username is required.");
            return;
        }

        clearError(elements.shareModalError);
        elements.btnConfirmShare.disabled = true;

        try {
            const res = await fetch(`/api/projects/${selectedProject.id}/share`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, permission_level })
            });
            const data = await res.json();
            if (!res.ok) {
                showError(elements.shareModalError, formatApiError(data.detail, "Failed to share project."));
                return;
            }

            closeShareModal();
            await loadProjectMembers();
            elements.membersModal.classList.remove("hidden");
        } catch (e) {
            showError(elements.shareModalError, "Connection error while sharing project.");
        } finally {
            elements.btnConfirmShare.disabled = false;
        }
    }

    async function loadProjectMembers() {
        const selectedProject = getSelectedProject();
        if (!selectedProject) {
            elements.membersList.innerHTML = '<div class="placeholder-text">No project selected.</div>';
            return;
        }

        elements.membersList.innerHTML = '<div class="placeholder-text">Loading members...</div>';

        try {
            const res = await fetch(`/api/projects/${selectedProject.id}/members`);
            const data = await res.json();
            if (!res.ok) {
                elements.membersList.innerHTML = `<div class="placeholder-text text-error">${escapeHtml(formatApiError(data.detail, "Unable to load members."))}</div>`;
                return;
            }

            if (!Array.isArray(data) || data.length === 0) {
                elements.membersList.innerHTML = '<div class="placeholder-text">No members yet.</div>';
                return;
            }

            const canManage = !!selectedProject.is_owner;
            const memberRows = data.map((member) => {
                const ownerTag = member.is_owner ? ' <span class="text-muted">(Owner)</span>' : "";
                const permission = member.is_owner ? "Owner" : (member.permission_level === "read_write" ? "Read & Write" : "Read Only");
                const removeBtn = canManage && !member.is_owner
                    ? `<button class="secondary-btn small-btn member-remove-btn" data-username="${escapeHtml(member.username)}">Remove</button>`
                    : "";

                return `
                    <div class="member-row" data-username="${escapeHtml(member.username)}">
                        <div class="member-main">
                            <div><strong>${escapeHtml(member.username)}</strong>${ownerTag}</div>
                            <div class="text-muted">${escapeHtml(member.email || "")}</div>
                            <div class="text-muted">Permission: ${permission}</div>
                        </div>
                        <div class="member-actions">${removeBtn}</div>
                    </div>
                `;
            }).join("");

            elements.membersList.innerHTML = memberRows;

            if (canManage) {
                elements.membersList.querySelectorAll(".member-remove-btn").forEach((btn) => {
                    btn.addEventListener("click", async () => {
                        const username = btn.getAttribute("data-username");
                        if (!username) return;
                        await removeMemberAccess(username);
                    });
                });
            }
        } catch (e) {
            elements.membersList.innerHTML = '<div class="placeholder-text text-error">Connection error loading members.</div>';
        }
    }

    async function removeMemberAccess(username) {
        const selectedProject = getSelectedProject();
        if (!selectedProject || !selectedProject.is_owner) {
            return;
        }

        try {
            const res = await fetch(`/api/projects/${selectedProject.id}/share/${encodeURIComponent(username)}`, {
                method: "DELETE"
            });
            const data = await res.json();
            if (!res.ok) {
                writeTerminalLine(elements.lintTerminal, `Failed to remove member: ${formatApiError(data.detail, "Unknown error")}`, "error");
                return;
            }
            await loadProjectMembers();
        } catch (e) {
            writeTerminalLine(elements.lintTerminal, "Failed to remove member: connection error", "error");
        }
    }

    function closeMembersModal() {
        elements.membersModal.classList.add("hidden");
    }

    elements.btnShareProject.addEventListener("click", openShareModal);
    elements.btnCloseShareModal.addEventListener("click", closeShareModal);
    elements.btnCancelShare.addEventListener("click", closeShareModal);
    elements.btnConfirmShare.addEventListener("click", shareSelectedProject);

    elements.btnViewMembers.addEventListener("click", async () => {
        const selectedProject = getSelectedProject();
        if (!selectedProject) return;
        elements.membersModal.classList.remove("hidden");
        await loadProjectMembers();
    });
    elements.btnCloseMembersModal.addEventListener("click", closeMembersModal);
    elements.btnCloseMembers.addEventListener("click", closeMembersModal);

    // ==========================================
    // 1. CONFIGURATION & SETTINGS
    // ==========================================
    async function loadConfig() {
        try {
            const res = await fetch("/api/config");
            const data = await res.json();
            state.config = data;
            updateConfigUI();
        } catch (e) {
            console.error("Error loading config:", e);
        }
    }

    function updateConfigUI() {
        if (state.config.api_key_configured) {
            elements.apiStatusBadge.className = "status-badge connected";
            elements.apiStatusBadge.querySelector(".status-text").textContent = `Gemini: ${state.config.masked_key}`;
            elements.inputApiKey.value = "";
            elements.inputApiKey.placeholder = "API Key Configured";
        } else {
            elements.apiStatusBadge.className = "status-badge disconnected";
            elements.apiStatusBadge.querySelector(".status-text").textContent = "Gemini API Key Required";
            elements.inputApiKey.placeholder = "AIzaSy...";
        }
    }

    elements.btnSettings.addEventListener("click", () => {
        elements.settingsModal.classList.remove("hidden");
        elements.configStatusMsg.classList.add("hidden");
    });

    elements.btnCloseSettings.addEventListener("click", () => {
        elements.settingsModal.classList.add("hidden");
    });

    elements.btnSaveSettings.addEventListener("click", async () => {
        const key = elements.inputApiKey.value.trim();
        if (!key) {
            showConfigMsg("API key cannot be empty", "error");
            return;
        }

        try {
            const res = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ api_key: key })
            });
            const data = await res.json();
            if (res.ok) {
                showConfigMsg("API key configured successfully!", "success");
                setTimeout(() => {
                    elements.settingsModal.classList.add("hidden");
                }, 1000);
                loadConfig();
            } else {
                showConfigMsg(data.detail || "Failed to configure key", "error");
            }
        } catch (e) {
            showConfigMsg("Server error connection failed", "error");
        }
    });

    function showConfigMsg(text, type) {
        elements.configStatusMsg.textContent = text;
        elements.configStatusMsg.className = `status-msg ${type}`;
        elements.configStatusMsg.classList.remove("hidden");
    }

    // ==========================================
    // 2. FILES LISTING & MANAGEMENT
    // ==========================================
    async function fetchRawFiles() {
        if (!state.selectedProjectId) {
            state.rawFiles = [];
            renderRawFiles();
            return;
        }
        try {
            const res = await fetch("/api/files/raw");
            const files = await res.json();
            state.rawFiles = files;
            renderRawFiles();
        } catch (e) {
            console.error("Error fetching raw files:", e);
        }
    }

    function renderRawFiles() {
        elements.rawFileList.innerHTML = "";
        if (state.rawFiles.length === 0) {
            elements.rawFileList.classList.add("empty");
            elements.rawFileList.innerHTML = `<div class="placeholder-text">No raw sources added.</div>`;
            return;
        }

        elements.rawFileList.classList.remove("empty");
        state.rawFiles.forEach(file => {
            const fileItem = document.createElement("div");
            fileItem.className = "file-item";
            if (state.selectedRawFile === file.name) {
                fileItem.classList.add("active");
            }

            fileItem.innerHTML = `
                <div class="file-info">
                    <i data-lucide="file" class="file-icon"></i>
                    <span class="file-name" title="${file.name}">${file.name}</span>
                </div>
                <span class="file-meta">${formatBytes(file.size)}</span>
            `;

            fileItem.addEventListener("click", () => selectRawFile(file.name));
            elements.rawFileList.appendChild(fileItem);
        });
        lucide.createIcons();
    }

    async function fetchWikiPages() {
        if (!state.selectedProjectId) {
            state.wikiPages = [];
            renderWikiPages();
            return;
        }
        try {
            const res = await fetch("/api/files/wiki");
            const pages = await res.json();
            state.wikiPages = pages;
            elements.wikiCountBadge.textContent = `${pages.length} pages`;
            renderWikiPages();
        } catch (e) {
            console.error("Error fetching wiki pages:", e);
        }
    }

    function renderWikiPages() {
        elements.wikiFileList.innerHTML = "";
        if (state.wikiPages.length === 0) {
            elements.wikiFileList.classList.add("empty");
            elements.wikiFileList.innerHTML = `<div class="placeholder-text">Wiki is empty.</div>`;
            return;
        }

        elements.wikiFileList.classList.remove("empty");
        state.wikiPages.forEach(page => {
            const isSpecial = page.name === "index.md" || page.name === "log.md";
            const fileItem = document.createElement("div");
            fileItem.className = `file-item ${isSpecial ? 'special-file' : ''}`;
            if (state.selectedWikiPage === page.name) {
                fileItem.classList.add("active");
            }

            const icon = page.name === "index.md" ? "book-open" : (page.name === "log.md" ? "activity" : "file-text");
            const cleanName = page.name.replace(".md", "");

            fileItem.innerHTML = `
                <div class="file-info">
                    <i data-lucide="${icon}" class="file-icon"></i>
                    <span class="file-name" title="${page.name}">${cleanName}</span>
                </div>
            `;

            fileItem.addEventListener("click", () => viewWikiPage(page.name));
            elements.wikiFileList.appendChild(fileItem);
        });
        lucide.createIcons();
    }

    // Select Raw File for Ingestion
    function selectRawFile(name) {
        state.selectedRawFile = name;
        elements.selectedRawFileName.textContent = name;
        elements.selectedRawFileName.classList.remove("text-muted");
        elements.btnIngestFile.disabled = false;
        
        // Highlighting in Raw File List
        Array.from(elements.rawFileList.children).forEach(el => {
            const nameEl = el.querySelector(".file-name");
            if (nameEl && nameEl.textContent === name) {
                el.classList.add("active");
            } else {
                el.classList.remove("active");
            }
        });
    }

    // Trigger local file upload
    elements.btnUploadTrigger.addEventListener("click", () => {
        if (!state.selectedProjectId) {
            writeTerminalLine(elements.ingestTerminal, "Please create/select a project before uploading files.", "warning");
            return;
        }
        elements.fileUploader.click();
    });

    elements.fileUploader.addEventListener("change", async (e) => {
        if (!state.selectedProjectId) {
            writeTerminalLine(elements.ingestTerminal, "Upload blocked: no project selected.", "error");
            elements.fileUploader.value = "";
            return;
        }

        const files = e.target.files;
        if (!files.length) return;

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const formData = new FormData();
            formData.append("file", file);

            try {
                const res = await fetch("/api/files/raw/upload", {
                    method: "POST",
                    body: formData
                });
                if (res.ok) {
                    const data = await res.json();
                    writeTerminalLine(elements.ingestTerminal, `Uploaded file: ${file.name} (${formatBytes(file.size)})`, "success");
                } else {
                    writeTerminalLine(elements.ingestTerminal, `Failed to upload: ${file.name}`, "error");
                }
            } catch (err) {
                const msg = err && err.message ? err.message : "Unknown upload error";
                writeTerminalLine(elements.ingestTerminal, `Upload failed for ${file.name}: ${msg}`, "error");
            }
        }
        
        fetchRawFiles();
        // Clear uploader value
        elements.fileUploader.value = "";
    });

    // ==========================================
    // 3. MARKDOWN RENDERER & MANUAL EDITING
    // ==========================================
    // Global function to route wiki double bracket link clicks
    window.app = {
        viewWikiPage: function(filename) {
            // Check if user is editing, confirm discard
            if (state.isEditing) {
                if (!confirm("You have unsaved changes. Discard them to navigate?")) {
                    return;
                }
                toggleEditMode(false);
            }
            viewWikiPage(filename);
            // Switch tabs if in graph view
            switchTab("reader");
        }
    };

    function parseWikiLinks(markdownText) {
        if (!markdownText) return "";
        // Parse [[link-target|Display text]] or [[link-target#anchor|Display text]]
        let processed = markdownText.replace(/\[\[([^\]|#\n]+)(?:#([^\]|#\n]+))?\|([^\]\n]+)\]\]/g, (match, page, anchor, text) => {
            const cleanLink = page.trim().toLowerCase().replace(/\s+/g, '-');
            return `<a class="wiki-link" href="#" onclick="event.preventDefault(); window.app.viewWikiPage('${cleanLink}.md')">${text}</a>`;
        });
        // Parse [[link-target]] or [[link-target#anchor]]
        processed = processed.replace(/\[\[([^\]|#\n]+)(?:#([^\]|#\n]+))?\]\]/g, (match, page, anchor) => {
            const cleanLink = page.trim().toLowerCase().replace(/\s+/g, '-');
            return `<a class="wiki-link" href="#" onclick="event.preventDefault(); window.app.viewWikiPage('${cleanLink}.md')">${page}</a>`;
        });
        return processed;
    }

    async function viewWikiPage(filename) {
        state.selectedWikiPage = filename;
        
        // Clear active states in wiki list
        Array.from(elements.wikiFileList.children).forEach(el => {
            const nameEl = el.querySelector(".file-name");
            const cleanName = filename.replace(".md", "");
            if (nameEl && nameEl.textContent === cleanName) {
                el.classList.add("active");
            } else {
                el.classList.remove("active");
            }
        });

        try {
            const res = await fetch(`/api/files/wiki/${filename}`);
            if (!res.ok) {
                if (res.status === 404) {
                    showWikiNotFoundError(filename);
                    return;
                }
                throw new Error("Failed to load page");
            }
            const data = await res.json();
            renderWikiContent(data.filename, data.content);
        } catch (e) {
            elements.pageTitle.textContent = "Error Loading Page";
            elements.markdownRenderer.innerHTML = `<div class="text-error">Error loading file ${filename}: ${e.message}</div>`;
        }
    }

    function showWikiNotFoundError(filename) {
        const cleanName = filename.replace(".md", "");
        elements.pageTitle.textContent = cleanName;
        elements.pageMetadata.classList.add("hidden");
        elements.headerDivider.classList.add("hidden");
        elements.btnEditPage.classList.add("hidden");
        
        elements.markdownRenderer.innerHTML = `
            <div class="intro-screen">
                <div class="intro-logo" style="border-color: var(--accent-gold); color: var(--accent-gold); box-shadow: 0 0 10px rgba(245, 158, 11, 0.2);">
                    <i data-lucide="file-warning"></i>
                </div>
                <h2>Wiki Page Not Found</h2>
                <p>The page <strong>${cleanName}</strong> does not exist yet. You can create it manually, or trigger the Agent to query/compile data into it.</p>
                <button id="btn-create-page-missing" class="primary-btn">
                    <i data-lucide="file-plus"></i> Create "${cleanName}" Manually
                </button>
            </div>
        `;
        lucide.createIcons();

        document.getElementById("btn-create-page-missing").addEventListener("click", () => {
            const defaultTemplate = `---\ntype: concept\ntitle: "${cleanName.replace(/-/g, ' ')}"\nsources: []\ntags: []\nlast_updated: ${new Date().toISOString().split('T')[0]}\n---\n\n# ${cleanName.replace(/-/g, ' ')}\n\n**Summary**: \n\n---\n\nExplanation goes here.`;
            elements.markdownEditor.value = defaultTemplate;
            toggleEditMode(true);
        });
    }

    function renderWikiContent(filename, rawContent) {
        elements.pageMetadata.classList.remove("hidden");
        elements.headerDivider.classList.remove("hidden");
        elements.btnEditPage.classList.remove("hidden");

        // Parse YAML Frontmatter
        let parsedContent = rawContent;
        let metadata = { title: filename.replace(".md", ""), tags: [], updated: "N/A", type: "concept" };

        if (rawContent.trim().startsWith("---")) {
            const endFmIndex = rawContent.indexOf("---", 3);
            if (endFmIndex !== -1) {
                const fmText = rawContent.substring(3, endFmIndex);
                parsedContent = rawContent.substring(endFmIndex + 3);

                // Quick regex YAML parsing
                const typeMatch = fmText.match(/type:\s*(\S+)/);
                const titleMatch = fmText.match(/title:\s*(.+)/);
                const updatedMatch = fmText.match(/last_updated:\s*(\S+)/);
                const tagsMatch = fmText.match(/tags:\s*\[(.*?)\]/);

                if (typeMatch) metadata.type = typeMatch[1].replace(/['"]/g, "");
                if (titleMatch) metadata.title = titleMatch[1].replace(/['"]/g, "");
                if (updatedMatch) metadata.updated = updatedMatch[1];
                if (tagsMatch) {
                    metadata.tags = tagsMatch[1].split(",").map(t => t.trim().replace(/['"]/g, "")).filter(t => t);
                }
            }
        }

        elements.pageTitle.textContent = metadata.title;
        elements.metaType.textContent = metadata.type;
        elements.metaUpdated.textContent = metadata.updated;
        elements.metaTags.textContent = metadata.tags.length > 0 ? metadata.tags.join(", ") : "None";

        // Render Markdown content
        const linkProcessedMarkdown = parseWikiLinks(parsedContent);
        elements.markdownRenderer.innerHTML = marked.parse(linkProcessedMarkdown);
        elements.markdownEditor.value = rawContent;

        lucide.createIcons();
    }

    function toggleEditMode(editing) {
        state.isEditing = editing;
        if (editing) {
            elements.markdownRenderer.classList.add("hidden");
            elements.editorContainer.classList.remove("hidden");
            elements.btnEditPage.classList.add("hidden");
            elements.btnSavePage.classList.remove("hidden");
            elements.btnCancelEdit.classList.remove("hidden");
        } else {
            elements.markdownRenderer.classList.remove("hidden");
            elements.editorContainer.classList.add("hidden");
            elements.btnEditPage.classList.remove("hidden");
            elements.btnSavePage.classList.add("hidden");
            elements.btnCancelEdit.classList.add("hidden");
        }
    }

    elements.btnEditPage.addEventListener("click", () => toggleEditMode(true));
    
    elements.btnCancelEdit.addEventListener("click", () => {
        toggleEditMode(false);
        // Reload content
        if (state.selectedWikiPage) viewWikiPage(state.selectedWikiPage);
    });

    elements.btnSavePage.addEventListener("click", async () => {
        if (!state.selectedWikiPage) return;
        const val = elements.markdownEditor.value;

        try {
            const formData = new FormData();
            formData.append("content", val);
            const res = await fetch(`/api/files/wiki/${state.selectedWikiPage}`, {
                method: "POST",
                body: formData
            });
            if (res.ok) {
                toggleEditMode(false);
                viewWikiPage(state.selectedWikiPage);
                fetchWikiPages(); // Refresh sidebar list
                if (state.activeTab === "graph") loadGraph(); // Reload graph visualization
            } else {
                alert("Failed to save changes.");
            }
        } catch (err) {
            alert("Connection error saving changes.");
        }
    });

    // ==========================================
    // 4. INTERACTIVE FORCE DIRECTED GRAPH (D3)
    // ==========================================
    async function loadGraph() {
        try {
            const res = await fetch("/api/graph");
            const data = await res.json();
            state.graphData = data;
            drawGraph();
        } catch (e) {
            console.error("Error fetching graph data:", e);
        }
    }

    function drawGraph() {
        const svg = d3.select("#graph-svg");
        svg.selectAll("*").remove();

        const container = document.getElementById("graph-view");
        const width = container.clientWidth;
        const height = container.clientHeight;

        const nodes = state.graphData.nodes;
        const links = state.graphData.links;

        // Force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-150))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(25));

        // Draw Links
        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link-line");

        // Color mapper based on node type
        const typeColors = {
            "source-summary": "var(--accent-blue)",
            "concept": "var(--accent-purple)",
            "core": "var(--accent-gold)",
            "analysis": "var(--accent-teal)"
        };

        // Draw Nodes
        const node = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .enter().append("g")
            .call(drag(simulation));

        // Node Circle
        node.append("circle")
            .attr("r", d => d.type === "core" ? 10 : 8)
            .attr("class", "node-circle")
            .attr("fill", d => typeColors[d.type] || "var(--accent-purple)")
            .style("color", d => typeColors[d.type] || "var(--accent-purple)")
            .on("click", (event, d) => {
                viewWikiPage(`${d.id}.md`);
                switchTab("reader");
            });

        // Node Labels
        node.append("text")
            .attr("dy", -12)
            .attr("class", "node-label")
            .text(d => d.title);

        // Simulation tick updater
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("transform", d => `translate(${d.x}, ${d.y})`);
        });

        // Drag behaviors
        function drag(sim) {
            function dragstarted(event) {
                if (!event.active) sim.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }
            
            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }
            
            function dragended(event) {
                if (!event.active) sim.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }
            
            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }

        // Handle window resizing
        window.addEventListener("resize", () => {
            const w = container.clientWidth;
            const h = container.clientHeight;
            simulation.force("center", d3.forceCenter(w / 2, h / 2));
            simulation.alpha(0.3).restart();
        });
    }

    // ==========================================
    // 5. AGENT OPERATIONS (INGEST, QUERY, LINT)
    // ==========================================
    
    // Switch tabs between Reader & Graph
    function switchTab(viewName) {
        state.activeTab = viewName;
        if (viewName === "reader") {
            elements.tabReader.classList.add("active");
            elements.tabGraph.classList.remove("active");
            elements.readerView.classList.add("active");
            elements.graphView.classList.remove("active");
        } else {
            elements.tabReader.classList.remove("active");
            elements.tabGraph.classList.add("active");
            elements.readerView.classList.remove("active");
            elements.graphView.classList.add("active");
            loadGraph(); // Load network graph representation
        }
    }

    elements.tabReader.addEventListener("click", () => switchTab("reader"));
    elements.tabGraph.addEventListener("click", () => switchTab("graph"));

    // Switch Agent Tabs
    function switchAgentTab(tabName) {
        state.activeAgentTab = tabName;
        const tabs = [elements.agentTabIngest, elements.agentTabQuery, elements.agentTabLint];
        const panels = [elements.panelIngest, elements.panelQuery, elements.panelLint];

        tabs.forEach(t => t.classList.remove("active"));
        panels.forEach(p => p.classList.remove("active"));

        if (tabName === "ingest") {
            elements.agentTabIngest.classList.add("active");
            elements.panelIngest.classList.add("active");
        } else if (tabName === "query") {
            elements.agentTabQuery.classList.add("active");
            elements.panelQuery.classList.add("active");
        } else {
            elements.agentTabLint.classList.add("active");
            elements.panelLint.classList.add("active");
        }
    }

    elements.agentTabIngest.addEventListener("click", () => switchAgentTab("ingest"));
    elements.agentTabQuery.addEventListener("click", () => switchAgentTab("query"));
    elements.agentTabLint.addEventListener("click", () => switchAgentTab("lint"));

    // Ingest operation
    elements.btnIngestFile.addEventListener("click", async () => {
        if (!state.selectedRawFile) return;

        const filename = state.selectedRawFile;
        const model = elements.selectModel.value;

        writeTerminalLine(elements.ingestTerminal, `\n[Ingesting]: ${filename}...`, "info");
        writeTerminalLine(elements.ingestTerminal, `Reading content and planning compilation layout...`, "muted");
        
        elements.btnIngestFile.disabled = true;

        try {
            const res = await fetch("/api/ingest", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename, model })
            });
            const data = await res.json();
            if (res.ok) {
                writeTerminalLine(elements.ingestTerminal, `Successfully ingested ${filename}!`, "success");
                writeTerminalLine(elements.ingestTerminal, `Summary page created: [[${data.filename.replace('.md', '')}]]`, "success");
                
                data.modified_files.forEach(f => {
                    writeTerminalLine(elements.ingestTerminal, ` - ${f.action.toUpperCase()}: ${f.filename} (${f.type})`, "info");
                });
                
                // Re-fetch files & view index
                fetchWikiPages();
                viewWikiPage(data.filename);
            } else {
                writeTerminalLine(elements.ingestTerminal, `Failed: ${formatApiError(data.detail, "Unknown error")}`, "error");
            }
        } catch (err) {
            writeTerminalLine(elements.ingestTerminal, `Server connection failure during ingestion.`, "error");
        } finally {
            elements.btnIngestFile.disabled = false;
        }
    });

    // Query operation
    elements.btnSubmitQuery.addEventListener("click", submitQuery);
    elements.queryInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") submitQuery();
    });

    async function submitQuery() {
        const val = elements.queryInput.value.trim();
        if (!val) return;

        elements.queryInput.value = "";
        elements.savePageCard.classList.add("hidden");
        state.draftedPage = null;

        // User bubble
        appendChatMessage("User", val, "user-msg");
        
        // Agent loading bubble
        const loadingMsgId = appendChatMessage("Agent", `<span class="text-muted"><i data-lucide="loader" class="loader-anim"></i> Searching index and synthesizing...</span>`, "agent-msg");
        lucide.createIcons();

        try {
            const model = elements.selectModel.value;
            const res = await fetch("/api/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: val, model })
            });
            const data = await res.json();
            
            // Remove loading
            document.getElementById(loadingMsgId).remove();

            if (res.ok) {
                // Parse citations to render as links in chat body
                const answerHTML = marked.parse(parseWikiLinks(data.answer));
                appendChatMessage("Agent", answerHTML, "agent-msg");
                
                // Show draft save card if suggested by the agent
                if (data.save_as_new_page && data.new_page) {
                    state.draftedPage = data.new_page;
                    elements.draftFilename.textContent = data.new_page.filename;
                    elements.savePageCard.classList.remove("hidden");
                }
            } else {
                appendChatMessage("Agent", `<span class="text-error">Error: ${formatApiError(data.detail, "Query synthesis failed")}</span>`, "agent-msg");
            }
        } catch (e) {
            document.getElementById(loadingMsgId).remove();
            appendChatMessage("Agent", `<span class="text-error">Connection failure to server</span>`, "agent-msg");
        }
    }

    elements.btnSaveDraft.addEventListener("click", async () => {
        if (!state.draftedPage) return;
        const page = state.draftedPage;
        try {
            const res = await fetch("/api/query/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    filename: page.filename,
                    title: page.title,
                    content: page.content
                })
            });
            const data = await res.json();
            if (res.ok) {
                elements.savePageCard.classList.add("hidden");
                appendChatMessage("System", `Compounding page saved successfully! Opening [[${page.filename.replace('.md', '')}]]`, "agent-msg");
                fetchWikiPages();
                viewWikiPage(page.filename);
                state.draftedPage = null;
            } else {
                alert(`Failed to save compounding page: ${formatApiError(data.detail, "Unknown error")}`);
            }
        } catch (e) {
            alert("Error sending request to server.");
        }
    });

    // Lint operation
    elements.btnRunLint.addEventListener("click", async () => {
        if (!state.selectedProjectId) {
            elements.lintTerminal.innerHTML = "";
            writeTerminalLine(elements.lintTerminal, "Please select a project before running lint.", "warning");
            return;
        }

        const model = elements.selectModel.value;
        elements.lintTerminal.innerHTML = "";
        writeTerminalLine(elements.lintTerminal, `Starting wiki health audit...`, "info");
        writeTerminalLine(elements.lintTerminal, `Submitting request to server (model: ${model})...`, "muted");

        elements.btnRunLint.disabled = true;
        const originalLintBtnHtml = elements.btnRunLint.innerHTML;
        elements.btnRunLint.innerHTML = '<i data-lucide="loader"></i> Running Audit...';
        lucide.createIcons();

        const slowAuditTimer = setTimeout(() => {
            writeTerminalLine(elements.lintTerminal, "Audit is still running... analyzing wiki content.", "info");
        }, 5000);

        const verySlowAuditTimer = setTimeout(() => {
            writeTerminalLine(elements.lintTerminal, "Still working. Large projects can take longer.", "muted");
        }, 15000);

        try {
            const res = await fetch("/api/lint", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ model })
            });
            const data = await res.json();

            clearTimeout(slowAuditTimer);
            clearTimeout(verySlowAuditTimer);

            if (res.ok) {
                writeTerminalLine(elements.lintTerminal, `Audit completed. Summarizing structural metrics:`, "success");
                
                const struct = data.structural_issues;
                writeTerminalLine(elements.lintTerminal, ` - Broken wiki links: ${struct.broken_links.length}`, struct.broken_links.length > 0 ? "error" : "success");
                struct.broken_links.forEach(bl => {
                    writeTerminalLine(elements.lintTerminal, `   [Broken Link] ${bl.source_file} -> [[${bl.broken_target}]]`, "error");
                });
                
                writeTerminalLine(elements.lintTerminal, ` - Orphan pages: ${struct.orphans.length}`, struct.orphans.length > 0 ? "warning" : "success");
                struct.orphans.forEach(o => {
                    writeTerminalLine(elements.lintTerminal, `   [Orphan Page] [[${o}]] is not linked from any page`, "warning");
                });

                writeTerminalLine(elements.lintTerminal, ` - YAML frontmatter errors: ${struct.yaml_errors.length}`, struct.yaml_errors.length > 0 ? "error" : "success");
                struct.yaml_errors.forEach(e => {
                    writeTerminalLine(elements.lintTerminal, `   [YAML Error] ${e}`, "error");
                });

                writeTerminalLine(elements.lintTerminal, `\nSemantic Audits (Contradictions & Insights):`, "info");
                data.semantic_audits.forEach(audit => {
                    const color = audit.severity === "critical" ? "error" : "warning";
                    writeTerminalLine(elements.lintTerminal, `[${audit.issue_type.toUpperCase()}] (${audit.severity}): ${audit.description}`, color);
                });

                writeTerminalLine(elements.lintTerminal, `\nSuggested Actions Checklist:`, "info");
                data.suggested_actions.forEach(action => {
                    writeTerminalLine(elements.lintTerminal, ` [ ] ${action}`, "muted");
                });

                fetchWikiPages(); // Refresh index since log.md was updated
            } else {
                writeTerminalLine(elements.lintTerminal, `Failed: ${formatApiError(data.detail, "Audit execution crashed")}`, "error");
            }
        } catch (e) {
            clearTimeout(slowAuditTimer);
            clearTimeout(verySlowAuditTimer);
            const msg = e && e.message ? e.message : "Connection error running lint audit.";
            writeTerminalLine(elements.lintTerminal, `Failed: ${msg}`, "error");
        } finally {
            elements.btnRunLint.disabled = false;
            elements.btnRunLint.innerHTML = originalLintBtnHtml;
            lucide.createIcons();
        }
    });

    // ==========================================
    // 6. UTILITY FUNCTIONS
    // ==========================================
    function formatBytes(bytes, decimals = 1) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function writeTerminalLine(terminalElement, text, className = "") {
        const line = document.createElement("div");
        line.className = `terminal-line ${className}`;
        line.innerHTML = text;
        terminalElement.appendChild(line);
        terminalElement.scrollTop = terminalElement.scrollHeight;
    }

    function appendChatMessage(sender, htmlContent, className) {
        const id = "msg-" + Date.now() + "-" + Math.floor(Math.random()*1000);
        const msg = document.createElement("div");
        msg.id = id;
        msg.className = `chat-message ${className}`;
        
        msg.innerHTML = `
            <div class="msg-header">${sender}</div>
            <div class="msg-body">${htmlContent}</div>
        `;
        
        elements.queryChatHistory.appendChild(msg);
        elements.queryChatHistory.scrollTop = elements.queryChatHistory.scrollHeight;
        return id;
    }

    function formatApiError(detail, fallback = "Unknown error") {
        if (!detail) return fallback;
        if (typeof detail === "string") return detail;
        if (Array.isArray(detail)) {
            return detail.map((d) => {
                if (typeof d === "string") return d;
                const loc = Array.isArray(d.loc) ? d.loc.join(".") : "field";
                const msg = d.msg || JSON.stringify(d);
                return `${loc}: ${msg}`;
            }).join(" | ");
        }
        if (typeof detail === "object") {
            if (detail.msg) return detail.msg;
            return JSON.stringify(detail);
        }
        return String(detail);
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/\"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Initialize Startup
    loadConfig();
    restoreSession();
});
