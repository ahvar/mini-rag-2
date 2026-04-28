window.createChatApi = function createChatApi() {
    const CHAT_SOURCES_HEADER = 'X-Chat-Sources';

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

    function parseSourcesHeader(response) {
        const rawSources = response.headers.get(CHAT_SOURCES_HEADER);
        if (!rawSources) {
            return [];
        }

        try {
            const parsed = JSON.parse(rawSources);
            if (!Array.isArray(parsed)) {
                return [];
            }

            return parsed.filter(function(source) {
                return source
                    && typeof source.title === 'string'
                    && typeof source.url === 'string'
                    && /^https?:\/\//i.test(source.url)
                    && (source.score === null || typeof source.score === 'number');
            });
        } catch (error) {
            console.warn('Failed to parse chat sources header', error);
            return [];
        }
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

        return {
            reader: reader,
            sources: parseSourcesHeader(response)
        };
    }

    return {
        selectAgent: selectAgent,
        openChatStream: openChatStream
    };
};
