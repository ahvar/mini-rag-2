window.createChatRenderer = function createChatRenderer(options) {
    const messagesArea = options.messagesArea;
    const scrollToBottom = options.scrollToBottom;

    const HIGHLIGHT_KEYWORDS = {
        python: new Set(['and', 'as', 'async', 'await', 'class', 'def', 'elif', 'else', 'except', 'False', 'for', 'from', 'if', 'import', 'in', 'lambda', 'None', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True', 'try', 'while', 'with', 'yield']),
        javascript: new Set(['async', 'await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'default', 'else', 'export', 'extends', 'finally', 'for', 'function', 'if', 'import', 'let', 'new', 'return', 'switch', 'throw', 'try', 'var', 'while']),
        typescript: new Set(['as', 'async', 'await', 'break', 'case', 'catch', 'class', 'const', 'continue', 'default', 'else', 'enum', 'export', 'extends', 'finally', 'for', 'function', 'if', 'implements', 'import', 'interface', 'let', 'new', 'private', 'protected', 'public', 'return', 'switch', 'throw', 'try', 'type', 'var', 'while']),
        json: new Set(['true', 'false', 'null']),
        bash: new Set(['case', 'do', 'done', 'echo', 'elif', 'else', 'esac', 'export', 'fi', 'for', 'function', 'if', 'in', 'local', 'then', 'while']),
        default: new Set(['class', 'const', 'def', 'else', 'for', 'function', 'if', 'import', 'let', 'return', 'while'])
    };

    function clearElement(element) {
        while (element.firstChild) {
            element.removeChild(element.firstChild);
        }
    }

    function createInlineNodes(text) {
        const fragment = document.createDocumentFragment();
        const tokenPattern = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^\)]+\))/g;
        let lastIndex = 0;
        let match = tokenPattern.exec(text);

        while (match) {
            if (match.index > lastIndex) {
                fragment.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
            }

            const token = match[0];
            if (token.startsWith('**') && token.endsWith('**')) {
                const strong = document.createElement('strong');
                strong.textContent = token.slice(2, -2);
                fragment.appendChild(strong);
            } else if (token.startsWith('`') && token.endsWith('`')) {
                const code = document.createElement('code');
                code.textContent = token.slice(1, -1);
                fragment.appendChild(code);
            } else {
                const linkMatch = token.match(/^\[([^\]]+)\]\(([^\)]+)\)$/);
                if (linkMatch) {
                    const href = linkMatch[2].trim();
                    if (/^https?:\/\//i.test(href)) {
                        const anchor = document.createElement('a');
                        anchor.href = href;
                        anchor.target = '_blank';
                        anchor.rel = 'noreferrer noopener';
                        anchor.textContent = linkMatch[1];
                        fragment.appendChild(anchor);
                    } else {
                        fragment.appendChild(document.createTextNode(token));
                    }
                }
            }

            lastIndex = tokenPattern.lastIndex;
            match = tokenPattern.exec(text);
        }

        if (lastIndex < text.length) {
            fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
        }

        return fragment;
    }

    function appendHighlightedCode(codeElement, codeText, language) {
        const normalizedLanguage = (language || '').toLowerCase();
        const keywordSet = HIGHLIGHT_KEYWORDS[normalizedLanguage] || HIGHLIGHT_KEYWORDS.default;
        const tokenPattern = /(#[^\n]*|\/\/[^\n]*|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`|\b\d+(?:\.\d+)?\b|\b[A-Za-z_][\w]*\b|\s+|.)/g;
        let match = tokenPattern.exec(codeText);

        while (match) {
            const token = match[0];
            let className = '';

            if (/^(#|\/\/)/.test(token)) {
                className = 'chat-code__comment';
            } else if (/^("|'|`)/.test(token)) {
                className = 'chat-code__string';
            } else if (/^\d/.test(token)) {
                className = 'chat-code__number';
            } else if (keywordSet.has(token)) {
                className = 'chat-code__keyword';
            }

            const nextCharacter = codeText[tokenPattern.lastIndex] || '';
            if (!className && /^[A-Za-z_][\w]*$/.test(token) && nextCharacter === '(') {
                className = 'chat-code__function';
            }

            if (className) {
                const span = document.createElement('span');
                span.className = className;
                span.textContent = token;
                codeElement.appendChild(span);
            } else {
                codeElement.appendChild(document.createTextNode(token));
            }

            match = tokenPattern.exec(codeText);
        }
    }

    function renderMarkdown(text, target) {
        clearElement(target);
        const lines = text.split(/\r?\n/);
        let index = 0;

        function isSpecialLine(line) {
            return /^```/.test(line) || /^#{1,6}\s+/.test(line) || /^[-*]\s+/.test(line) || /^\d+\.\s+/.test(line);
        }

        while (index < lines.length) {
            const line = lines[index];

            if (!line.trim()) {
                index += 1;
                continue;
            }

            const codeFence = line.match(/^```\s*([\w+-]+)?\s*$/);
            if (codeFence) {
                const language = codeFence[1] || '';
                const codeLines = [];
                index += 1;

                while (index < lines.length && !/^```\s*$/.test(lines[index])) {
                    codeLines.push(lines[index]);
                    index += 1;
                }

                if (index < lines.length) {
                    index += 1;
                }

                const pre = document.createElement('pre');
                const code = document.createElement('code');
                if (language) {
                    code.dataset.language = language;
                }
                appendHighlightedCode(code, codeLines.join('\n'), language);
                pre.appendChild(code);
                target.appendChild(pre);
                continue;
            }

            const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
            if (headingMatch) {
                const heading = document.createElement('h' + headingMatch[1].length);
                heading.appendChild(createInlineNodes(headingMatch[2]));
                target.appendChild(heading);
                index += 1;
                continue;
            }

            const listMatch = line.match(/^([-*]|\d+\.)\s+(.+)$/);
            if (listMatch) {
                const isOrdered = /\d+\./.test(listMatch[1]);
                const list = document.createElement(isOrdered ? 'ol' : 'ul');

                while (index < lines.length) {
                    const currentLine = lines[index];
                    const currentMatch = currentLine.match(/^([-*]|\d+\.)\s+(.+)$/);
                    if (!currentMatch) {
                        break;
                    }

                    const item = document.createElement('li');
                    item.appendChild(createInlineNodes(currentMatch[2]));
                    list.appendChild(item);
                    index += 1;
                }

                target.appendChild(list);
                continue;
            }

            const paragraphLines = [line];
            index += 1;
            while (index < lines.length && lines[index].trim() && !isSpecialLine(lines[index])) {
                paragraphLines.push(lines[index]);
                index += 1;
            }

            const paragraph = document.createElement('p');
            paragraph.appendChild(createInlineNodes(paragraphLines.join(' ')));
            target.appendChild(paragraph);
        }
    }

    function updateMessage(messageNode, message, options) {
        const settings = options || {};
        messageNode.wrapper.dataset.state = settings.state || messageNode.wrapper.dataset.state || 'complete';
        messageNode.state.textContent = settings.stateLabel || '';

        if (settings.label) {
            messageNode.label.textContent = settings.label;
        }

        if (settings.isUser || messageNode.isUser) {
            messageNode.content.textContent = message;
        } else {
            renderMarkdown(message, messageNode.content);
        }

        scrollToBottom();
    }

    function createMessageElement(message, options) {
        const settings = options || {};
        const wrapper = document.createElement('article');
        wrapper.className = 'chat-message ' + (settings.isUser ? 'chat-message--user' : 'chat-message--assistant');
        wrapper.dataset.state = settings.state || (settings.isUser ? 'complete' : 'idle');

        const bubble = document.createElement('div');
        bubble.className = 'chat-message__bubble';

        const meta = document.createElement('div');
        meta.className = 'chat-message__meta';

        const author = document.createElement('div');
        author.className = 'chat-message__author';
        author.textContent = settings.isUser ? 'You' : (settings.label || 'Assistant');

        const state = document.createElement('div');
        state.className = 'chat-message__state';
        state.textContent = settings.stateLabel || '';

        meta.appendChild(author);
        meta.appendChild(state);

        const content = document.createElement('div');
        content.className = 'chat-message__content';

        bubble.appendChild(meta);
        bubble.appendChild(content);
        wrapper.appendChild(bubble);
        messagesArea.appendChild(wrapper);

        const messageNode = {
            wrapper: wrapper,
            content: content,
            state: state,
            label: author,
            isUser: Boolean(settings.isUser)
        };

        updateMessage(messageNode, message || '', settings);
        return messageNode;
    }

    return {
        createMessageElement: createMessageElement,
        updateMessage: updateMessage
    };
};