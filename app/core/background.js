const ext = typeof browser !== "undefined" ? browser : chrome;

let socket = null;

function connect() {
    socket = new WebSocket("ws://localhost:8765");

    socket.onopen = () => {
        console.log("[Dgarvis] Подключено к Python-ассистенту");
    };

    socket.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        
        // Ищем все открытые вкладки с YouTube в фоне
        const tabs = await ext.tabs.query({ url: "*://*://*" });

        if (data.action === "search") {
            const searchUrl = `https://www://results?search_query=${encodeURIComponent(data.query)}`;
            if (tabs.length > 0) {
                // Меняем ссылку в уже существующей фоновой вкладке YouTube
                await ext.tabs.update(tabs[0].id, { url: searchUrl });
            } else {
                // Если вкладок с YouTube нет, открываем новую
                await ext.tabs.create({ url: searchUrl, active: false });
            }
            return;
        }

        // Для команд управления видео нужна хотя бы одна вкладка с YouTube
        if (tabs.length === 0) return;
        const targetTabId = tabs[0].id;

        if (data.action === "pause") {
            await ext.scripting.executeScript({
                target: { tabId: targetTabId },
                func: () => document.querySelector("video")?.pause()
            });
        } else if (data.action === "play") {
            await ext.scripting.executeScript({
                target: { tabId: targetTabId },
                func: () => document.querySelector("video")?.play()
            });
        } else if (data.action === "toggle") {
            await ext.scripting.executeScript({
                target: { tabId: targetTabId },
                func: () => {
                    const video = document.querySelector("video");
                    if (video) video.paused ? video.play() : video.pause();
                }
            });
        }
    };

    socket.onclose = () => {
        // Если Python-скрипт выключен, пробуем переподключиться каждые 3 секунды
        setTimeout(connect, 3000);
    };

    socket.onerror = () => {
        socket.close();
    };
}

// Запускаем подключение при старте браузера
connect();

// Пинг каждые 20 секунд, чтобы браузер не усыплял фоновый скрипт
setInterval(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ status: "ping" }));
    }
}, 20000);