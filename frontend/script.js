document.addEventListener('DOMContentLoaded', () => {
    // --- State ---
    let currentThreadId = null;
    let currentAgentId = null;
    
    // --- Elements ---
    const messagesContainer = document.getElementById('messages-container');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const fileInput = document.getElementById('file-input');
    
    const historyList = document.getElementById('history-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    
    const agentSelect = document.getElementById('agent-select');
    // const editAgentBtn = document.getElementById('edit-agent-btn'); // Moved down
    
    const docsList = document.getElementById('docs-list');
    
    const graphContainer = document.getElementById('graph-container');

    // --- Graph Init (Wireframe Mode) ---
    // Modified to look like a technical schematic
    let Graph = ForceGraph()(graphContainer)
        .backgroundColor('rgba(0,0,0,0)')
        .nodeLabel('name')
        .nodeVal('val')
        .nodeColor(() => '#FF4F00') // All nodes Orange
        .nodeRelSize(3) // Smaller, consistent size
        .linkColor(() => '#333333') // Dark Grey Links
        .linkWidth(1)
        .onNodeClick(node => {
            Graph.centerAt(node.x, node.y, 1000);
            Graph.zoom(8, 2000);
        });

    // Custom Node Canvas Object for "Square / Wireframe" look
    Graph.nodeCanvasObject((node, ctx, globalScale) => {
        const size = 3; 
        ctx.fillStyle = '#000000';
        ctx.strokeStyle = '#FF4F00';
        ctx.lineWidth = 1 / globalScale; // Thin sharp lines
        
        ctx.beginPath();
        ctx.rect(node.x - size, node.y - size, size * 2, size * 2);
        ctx.fill();
        ctx.stroke();
    });

    async function loadGraphData() {
        try {
            const res = await fetch('/api/graph');
            const data = await res.json();
            Graph.graphData(data);
        } catch (err) {
            console.error("Graph load error:", err);
        }
    }
    loadGraphData();
    window.addEventListener('resize', () => { Graph.width(window.innerWidth); Graph.height(window.innerHeight); });


    // --- SIDEBAR TABS ---
    const tabAgents = document.getElementById('tab-agents');
    const tabMemory = document.getElementById('tab-memory');
    const tabBtnAgents = document.getElementById('tab-btn-agents');
    const tabBtnMemory = document.getElementById('tab-btn-memory');
    
    function switchTab(tab) {
        if (tab === 'agents') {
            tabAgents.classList.remove('hidden'); tabAgents.classList.add('active');
            tabMemory.classList.add('hidden'); tabMemory.classList.remove('active');
            tabBtnAgents.classList.add('active');
            tabBtnMemory.classList.remove('active');
        } else {
            tabMemory.classList.remove('hidden'); tabMemory.classList.add('active');
            tabAgents.classList.add('hidden'); tabAgents.classList.remove('active');
            tabBtnMemory.classList.add('active');
            tabBtnAgents.classList.remove('active');
        }
    }
    
    tabBtnAgents.addEventListener('click', () => switchTab('agents'));
    tabBtnMemory.addEventListener('click', () => switchTab('memory'));

    // --- HISTORY SIDEBAR (With Delete) ---
    async function loadHistory() {
        try {
            const res = await fetch('/api/threads');
            const threads = await res.json();
            
            historyList.innerHTML = '';
            
            if (threads.length === 0) {
                historyList.innerHTML = '<div class="empty-state">No Active Threads</div>';
                return;
            }
            
            threads.forEach(thread => {
                const div = document.createElement('div');
                div.className = 'history-item';
                
                div.innerHTML = `
                    <span class="thread-title" style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${thread.title || thread.id}</span>
                    <span class="delete-thread-btn" title="Delete Thread">x</span>
                `;
                
                if (thread.id === currentThreadId) div.classList.add('active');
                
                // Click on text to load
                div.querySelector('.thread-title').addEventListener('click', () => loadThread(thread.id));
                
                // Click on X to delete
                div.querySelector('.delete-thread-btn').addEventListener('click', async (e) => {
                    e.stopPropagation();
                    if (confirm("Delete this thread history?")) {
                        await fetch(`/api/threads/${thread.id}`, { method: 'DELETE' });
                        if (currentThreadId === thread.id) {
                            currentThreadId = null;
                            messagesContainer.innerHTML = '';
                        }
                        loadHistory();
                    }
                });
                
                historyList.appendChild(div);
            });
        } catch (err) {
            console.error("History error:", err);
            historyList.innerHTML = '<div class="empty-state">Connection Error</div>';
        }
    }

    // --- AGENT EDITOR (Native) ---
    const agentViewMode = document.getElementById('agent-view-mode');
    const agentEditMode = document.getElementById('agent-edit-mode');
    
    const editAgentBtn = document.getElementById('edit-agent-btn');
    const createAgentBtn = document.getElementById('create-agent-btn');
    const saveAgentBtn = document.getElementById('save-agent-btn');
    const cancelAgentBtn = document.getElementById('cancel-agent-btn');
    
    const nameInput = document.getElementById('agent-name-input');
    const modelSelect = document.getElementById('agent-model-select');
    const promptInput = document.getElementById('agent-prompt-input');
    
    let editingAgentId = null; // null = creating new
    
    function toggleAgentEditor(show) {
        if (show) {
            agentViewMode.classList.add('hidden');
            agentEditMode.classList.remove('hidden');
        } else {
            agentEditMode.classList.add('hidden');
            agentViewMode.classList.remove('hidden');
        }
    }

    // Load available Agents
    async function loadAgents() {
        agentSelect.innerHTML = '<option>Loading Cores...</option>'; // Loading State
        try {
            const res = await fetch('/api/agents');
            const agents = await res.json();
            
            agentSelect.innerHTML = '';
            let activeId = null;
            
            agents.forEach(a => {
                const opt = document.createElement('option');
                opt.value = a.id;
                opt.textContent = a.name + (a.is_active ? ' [ACTIVE]' : '');
                agentSelect.appendChild(opt);
                
                if (a.is_active) activeId = a.id;
            });
            
            if (activeId) {
                agentSelect.value = activeId;
                currentAgentId = activeId;
            } else if (agents.length > 0) {
                // Default to first if none active (shouldn't happen if initialized right)
                currentAgentId = agents[0].id;
            }
        } catch (err) {
            console.error("Agent load error:", err);
            agentSelect.innerHTML = '<option>Connection Failed</option>';
        }
    }

    // Agent Switch Listener
    agentSelect.addEventListener('change', async (e) => {
        const newAgentId = e.target.value;
        try {
            const res = await fetch(`/api/agents/${newAgentId}/select`, { method: 'POST' });
            if (!res.ok) throw new Error("Failed to switch agent");
            
            addMessageToUI('system', `Active Core switched to Agent ID: ${newAgentId.substring(0,8)}...`);
            currentAgentId = newAgentId;
            
            // Reload to update [ACTIVE] label visually
            loadAgents(); 
        } catch (err) {
            console.error(err);
            addMessageToUI('system', `Error switching agent: ${err.message}`);
        }
    });

    // Load available Ollama models
    async function loadModels() {
        modelSelect.innerHTML = '<option>Scanning Models...</option>'; // Loading State
        try {
            const res = await fetch('/api/agents/models');
            const models = await res.json();
            
            modelSelect.innerHTML = '';
            models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m;
                opt.textContent = m;
                modelSelect.appendChild(opt);
            });
        } catch (err) {
            console.error("Model fetch error:", err);
            // Fallback
            modelSelect.innerHTML = '<option value="gemma3:latest">gemma3:latest</option>';
        }
    }
    
    // Fetch Current Agent Details Helper
    async function getAgentDetails(id) {
        const res = await fetch('/api/agents'); // Re-fetch list implementation for now
        const agents = await res.json();
        return agents.find(a => a.id === id);
    }
    editAgentBtn.addEventListener('click', async () => {
        if (!currentAgentId) return;
        const agent = await getAgentDetails(currentAgentId);
        if (agent) {
            editingAgentId = agent.id;
            nameInput.value = agent.name;
            promptInput.value = agent.system_prompt;
            
            // Set model value
            modelSelect.value = agent.model;
            
            // Show Delete Button
            document.getElementById('delete-agent-btn').style.display = 'block';
            
            toggleAgentEditor(true);
        }
    });
    
    createAgentBtn.addEventListener('click', () => {
        editingAgentId = null; // New
        nameInput.value = '';
        promptInput.value = 'You are an AI assistant...';
        // Default first model
        if(modelSelect.options.length > 0) modelSelect.selectedIndex = 0;
        
        // Hide Delete Button
        document.getElementById('delete-agent-btn').style.display = 'none';
        
        toggleAgentEditor(true);
    });
    
    cancelAgentBtn.addEventListener('click', () => toggleAgentEditor(false));
    
    saveAgentBtn.addEventListener('click', async () => {
        const payload = {
            name: nameInput.value,
            model: modelSelect.value,
            system_prompt: promptInput.value
        };
        
        try {
            if (editingAgentId) {
                // UPDATE
                await fetch(`/api/agents/${editingAgentId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                addMessageToUI('system', `Agent '${payload.name}' updated.`);
            } else {
                // CREATE
                const res = await fetch('/api/agents', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const newAgent = await res.json();
                // Select new agent?
            }
            toggleAgentEditor(false);
            loadAgents();
            // Clear form logic
            nameInput.value = '';
            promptInput.value = '';
        } catch (err) {
            alert("Error saving agent: " + err.message);
        }
    });

    const deleteAgentBtn = document.getElementById('delete-agent-btn');
    deleteAgentBtn.addEventListener('click', async () => {
        if (!editingAgentId) {
             alert("Error: No Agent ID found. Please re-select the agent.");
             return;
        }
        
        if (confirm("Permanently delete this Persona? This cannot be undone.")) {
            try {
                // Visual feedback
                deleteAgentBtn.textContent = "DELETING...";
                deleteAgentBtn.disabled = true;

                // Call Standard Endpoint
                const res = await fetch(`/api/agents/${editingAgentId}`, { method: 'DELETE' });
                
                if (res.ok) {
                    alert("✅ Agent Deleted Successfully. Reloding System...");
                    window.location.reload(); // Hard Reset to ensure consistent state
                } else {
                    const errText = await res.text();
                    alert("❌ Delete Failed: " + errText);
                    // Reset button
                    deleteAgentBtn.textContent = "[DELETE_PERSONA]";
                    deleteAgentBtn.disabled = false;
                }
            } catch (err) {
                alert("❌ Network Error: " + err.message);
                deleteAgentBtn.textContent = "[DELETE_PERSONA]";
                deleteAgentBtn.disabled = false;
            }
        }
    });
    
    // --- DOCUMENTS SIDEBAR (Memory Revamp) ---
    async function loadDocs() {
        try {
            const res = await fetch('/api/documents');
            const docs = await res.json();
            
            // Stats Update
            document.getElementById('stat-nodes').textContent = docs.length.toString().padStart(3, '0');
            
            docsList.innerHTML = '';
            if (docs.length === 0) {
                 docsList.innerHTML = '<div class="empty-state">Memory Banks Empty</div>';
            } else {
                docs.forEach(doc => {
                     const div = document.createElement('div');
                    div.className = 'memory-card';
                    div.innerHTML = `
                        <div class="mem-icon">📄</div>
                        <div class="mem-name" title="${doc.filename}">${doc.filename}</div>
                        <div class="mem-delete" title="Purge Engram">×</div>
                    `;
                    
                    div.querySelector('.mem-delete').addEventListener('click', async (e) => {
                        e.stopPropagation();
                        if (confirm(`Delete ${doc.filename}?`)) {
                            await fetch(`/api/documents/${doc.filename}`, { method: 'DELETE' });
                            loadDocs();
                            loadGraphData();
                        }
                    });
                    docsList.appendChild(div);
                });
            }
        } catch (err) {
            console.error(err);
             docsList.innerHTML = '<div class="empty-state">Offline</div>';
        }
    }

    // Drag & Drop Logic
    function setupDragAndDrop() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');

        dropZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', async () => {
             if (fileInput.files.length) handleFiles(fileInput.files);
        });

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(() => dropZone.classList.add('drag-over'));
        ['dragleave', 'drop'].forEach(() => dropZone.classList.remove('drag-over'));

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            handleFiles(files);
        });
    }

    async function handleFiles(files) {
        if (!files.length) return;
        
        // Process each file individually
        for (const file of Array.from(files)) {
            const formData = new FormData();
            formData.append('file', file); // Singular 'file' matches backend

            addMessageToUI('system', `Ingesting packet: ${file.name}...`);
            try {
                const res = await fetch('/api/ingest', {
                    method: 'POST',
                    body: formData
                });
                
                if (!res.ok) {
                    const err = await res.text();
                    throw new Error(err);
                }

                const data = await res.json();
                addMessageToUI('system', `Ingestion Complete. Processed ${data.chunks} chunks.`);
            } catch (err) {
                addMessageToUI('system', `Ingestion Failed for ${file.name}: ${err.message}`);
            }
        }
        
        loadDocs();
        loadGraphData();
    }
    
    // Call setup
    setupDragAndDrop();


    // --- CHAT LOGIC ---
    function addMessageToUI(role, content) {
        const div = document.createElement('div');
        div.className = `log-entry ${role}`;
        
        // Formating
        let prefixText = '';
        if (role === 'user') prefixText = '[USER] >';
        else if (role === 'assistant') prefixText = '[RESPONSE] >';
        else if (role === 'system') prefixText = '[SYSTEM] ::';
        
        let safeContent = content;
        
        // Render Markdown for Assistant
        if (role === 'assistant') {
            safeContent = DOMPurify.sanitize(marked.parse(content));
        } else if (role === 'user') {
            // Simple escape for user
            safeContent = content.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
        }

        if (role === 'assistant') {
             div.innerHTML = `
                <div class="prefix">${prefixText}</div>
                <div class="content markdown-body">${safeContent}</div>
            `;
        } else {
             div.innerHTML = `
                <div class="prefix">${prefixText}</div>
                <div class="content">${safeContent}</div>
            `;
        }
        
        messagesContainer.appendChild(div);
        
        // Highlight Code
        div.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
        const terminalInterface = document.querySelector('.terminal-interface');
        terminalInterface.scrollTop = terminalInterface.scrollHeight;
    }

    async function sendMessage() {
        const query = chatInput.value.trim();
        if (!query) return;

        addMessageToUI('user', query);
        chatInput.value = '';
        chatInput.style.height = 'auto'; // Reset height

        // System "Working" Log
        const loaderDiv = document.createElement('div');
        loaderDiv.className = 'log-entry system';
        loaderDiv.innerHTML = `<div class="prefix">[SYSTEM] ::</div><div class="content">Processing input stream...</div>`;
        messagesContainer.appendChild(loaderDiv);
        
        const terminalInterface = document.querySelector('.terminal-interface');
        terminalInterface.scrollTop = terminalInterface.scrollHeight;

        // Disable UI
        sendBtn.disabled = true;
        chatInput.disabled = true;

        try {
            const payload = { query };
            if (currentThreadId) payload.thread_id = currentThreadId;
            
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            // Set current thread if new
            if (data.thread_id && currentThreadId !== data.thread_id) {
                currentThreadId = data.thread_id;
                loadHistory(); // Refresh sidebar to show new thread
            }
            
            // Remove loader
            loaderDiv.remove();
            
            addMessageToUI('assistant', data.response);
        } catch (err) {
            loaderDiv.remove();
            addMessageToUI('assistant', "Error: Connection lost.");
        } finally {
            // Re-enable UI
            sendBtn.disabled = false;
            chatInput.disabled = false;
            chatInput.focus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    
    // Auto-Expand Textarea Logic
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // --- INITIALIZATION ---
    loadHistory();
    loadAgents(); // This calls the function defined above
    loadDocs();
    loadModels();
});
