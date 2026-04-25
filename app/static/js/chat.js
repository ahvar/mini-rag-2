document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesArea = document.getElementById('messages-area');
    const chatContainer = document.getElementById('chat-container');
    const loadingIndicator = document.getElementById('loading');
    const sendButton = document.getElementById('send-button');
    const statusPill = document.getElementById('chat-status');

    if (!chatForm || !messageInput || !messagesArea || !chatContainer || !loadingIndicator || !sendButton || !statusPill) {
        return;
    }

    const messages = [];
    const chatApi = window.createChatApi();
    const renderer = window.createChatRenderer({
        messagesArea: messagesArea,
        scrollToBottom: scrollToBottom
    });

    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function autoResizeInput() {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 192) + 'px';
    }

    function setLoading(show) {
        loadingIndicator.style.display = show ? 'flex' : 'none';
        sendButton.disabled = show;
        messageInput.disabled = show;
    }

    function setStatus(state, label) {
        statusPill.dataset.state = state;
        statusPill.textContent = label;
    }

    async function streamChat(selectorData, assistantMessage) {
        const agentLabel = selectorData.agent === 'linkedin' ? 'LinkedIn Agent' : 'RAG Agent';
        const reader = await chatApi.openChatStream({
            messages: messages,
            agent: selectorData.agent,
            query: selectorData.query
        });

        const decoder = new TextDecoder();
        let assistantText = '';
        setStatus('streaming', 'Streaming');

        while (true) {
            const chunk = await reader.read();
            if (chunk.done) {
                break;
            }

            assistantText += decoder.decode(chunk.value, { stream: true });
            renderer.updateMessage(assistantMessage, assistantText || 'Thinking...', {
                label: agentLabel,
                state: 'streaming',
                stateLabel: 'Streaming'
            });
        }

        assistantText += decoder.decode();
        renderer.updateMessage(assistantMessage, assistantText, {
            label: agentLabel,
            state: 'complete',
            stateLabel: 'Complete'
        });
        messages.push({ role: 'assistant', content: assistantText });
        setStatus('ready', 'Ready');
    }

    chatForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const text = messageInput.value.trim();
        if (!text) {
            return;
        }

        const pendingInput = text;
        renderer.createMessageElement(text, { isUser: true, state: 'complete' });
        messages.push({ role: 'user', content: text });
        messageInput.value = '';
        autoResizeInput();
        setLoading(true);
        setStatus('thinking', 'Selecting agent');

        let assistantMessage = null;

        try {
            const selectorData = await chatApi.selectAgent(messages);
            const agentLabel = selectorData.agent === 'linkedin' ? 'LinkedIn Agent' : 'RAG Agent';
            assistantMessage = renderer.createMessageElement('Thinking...', {
                label: agentLabel,
                state: 'thinking',
                stateLabel: 'Thinking'
            });
            await streamChat(selectorData, assistantMessage);
        } catch (error) {
            console.error(error);
            setStatus('error', 'Needs attention');
            messageInput.value = pendingInput;
            autoResizeInput();

            if (assistantMessage) {
                renderer.updateMessage(assistantMessage, 'Error: ' + error.message, {
                    label: assistantMessage.label.textContent,
                    state: 'error',
                    stateLabel: 'Error'
                });
            } else {
                renderer.createMessageElement('Error: ' + error.message, {
                    label: 'Assistant',
                    state: 'error',
                    stateLabel: 'Error'
                });
            }
        } finally {
            setLoading(false);
            if (statusPill.dataset.state !== 'error') {
                setStatus('ready', 'Ready');
            }
            messageInput.focus();
        }
    });

    messageInput.addEventListener('input', autoResizeInput);
    messageInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (!sendButton.disabled) {
                chatForm.requestSubmit();
            }
        }
    });

    messageInput.focus();
    autoResizeInput();
    setStatus('ready', 'Ready');
});