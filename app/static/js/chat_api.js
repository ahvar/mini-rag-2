window.createChatApi = function createChatApi() {
    async function parseJsonResponse(response, fallbackMessage) {
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || fallbackMessage);
        }
        return data;
    }

    async function selectAgent(messages) {
        const response = await fetch('/api/select-agent', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: messages })
        });

        return parseJsonResponse(response, 'Selector failed');
    }

    async function openChatStream(payload) {
        const response = await fetch('/api/chat-stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Chat failed');
        }

        const reader = response.body && response.body.getReader();
        if (!reader) {
            throw new Error('Streaming is not available in this browser');
        }

        return reader;
    }

    return {
        selectAgent: selectAgent,
        openChatStream: openChatStream
    };
};