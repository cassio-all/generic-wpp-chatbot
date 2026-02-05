/**
 * WhatsApp Web Bridge Server
 * Connects WhatsApp Web.js with Python chatbot via WebSocket
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const WebSocket = require('ws');
const express = require('express');

const app = express();
const PORT = 8765;

// WebSocket server for Python communication
const wss = new WebSocket.Server({ port: PORT });
let pythonClient = null;

// WhatsApp client with persistent session
const whatsappClient = new Client({
    authStrategy: new LocalAuth({
        dataPath: './.wwebjs_auth'
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ]
    }
});

// WebSocket connection from Python
wss.on('connection', (ws) => {
    console.log('🐍 Python client connected');
    pythonClient = ws;
    
    // Send ready status
    if (whatsappClient.info) {
        sendToPython({
            type: 'status',
            status: 'ready',
            info: whatsappClient.info
        });
    }

    ws.on('message', async (data) => {
        try {
            const message = JSON.parse(data);
            await handlePythonMessage(message);
        } catch (error) {
            console.error('❌ Error handling Python message:', error);
            ws.send(JSON.stringify({
                type: 'error',
                error: error.message
            }));
        }
    });

    ws.on('close', () => {
        console.log('🐍 Python client disconnected');
        pythonClient = null;
    });
});

// Handle messages from Python
async function handlePythonMessage(message) {
    const { type, data } = message;

    switch (type) {
        case 'send_message':
            await sendWhatsAppMessage(data.to, data.text);
            break;
        
        case 'send_typing':
            await sendTyping(data.to);
            break;
        
        case 'get_chats':
            await getChats();
            break;
        
        case 'get_contact':
            await getContact(data.id);
            break;
        
        default:
            console.log('⚠️ Unknown message type:', type);
    }
}

// Send message via WhatsApp
async function sendWhatsAppMessage(to, text) {
    try {
        const chatId = to.includes('@c.us') ? to : `${to}@c.us`;
        await whatsappClient.sendMessage(chatId, text);
        
        sendToPython({
            type: 'message_sent',
            to: chatId,
            success: true
        });
        
        console.log(`✅ Message sent to ${chatId}`);
    } catch (error) {
        console.error('❌ Error sending message:', error);
        sendToPython({
            type: 'message_sent',
            to: to,
            success: false,
            error: error.message
        });
    }
}

// Send typing indicator
async function sendTyping(to) {
    try {
        const chatId = to.includes('@c.us') ? to : `${to}@c.us`;
        const chat = await whatsappClient.getChatById(chatId);
        await chat.sendStateTyping();
        console.log(`⌨️ Typing sent to ${chatId}`);
    } catch (error) {
        console.error('❌ Error sending typing:', error);
    }
}

// Get all chats
async function getChats() {
    try {
        const chats = await whatsappClient.getChats();
        const chatList = chats.map(chat => ({
            id: chat.id._serialized,
            name: chat.name,
            isGroup: chat.isGroup,
            timestamp: chat.timestamp,
            unreadCount: chat.unreadCount
        }));
        
        sendToPython({
            type: 'chats_list',
            chats: chatList
        });
    } catch (error) {
        console.error('❌ Error getting chats:', error);
    }
}

// Get contact info
async function getContact(contactId) {
    try {
        const contact = await whatsappClient.getContactById(contactId);
        sendToPython({
            type: 'contact_info',
            contact: {
                id: contact.id._serialized,
                name: contact.name || contact.pushname,
                number: contact.number,
                isMyContact: contact.isMyContact
            }
        });
    } catch (error) {
        console.error('❌ Error getting contact:', error);
    }
}

// Send data to Python client
function sendToPython(data) {
    if (pythonClient && pythonClient.readyState === WebSocket.OPEN) {
        pythonClient.send(JSON.stringify(data));
    }
}

// WhatsApp client events
whatsappClient.on('qr', (qr) => {
    console.log('📱 QR Code received! Scan with WhatsApp:');
    qrcode.generate(qr, { small: true });
    
    sendToPython({
        type: 'qr_code',
        qr: qr
    });
});

whatsappClient.on('ready', () => {
    console.log('✅ WhatsApp client is ready!');
    console.log(`📱 Connected as: ${whatsappClient.info.pushname}`);
    console.log(`📞 Number: ${whatsappClient.info.wid.user}`);
    
    sendToPython({
        type: 'status',
        status: 'ready',
        info: {
            pushname: whatsappClient.info.pushname,
            number: whatsappClient.info.wid.user,
            platform: whatsappClient.info.platform
        }
    });
});

whatsappClient.on('authenticated', () => {
    console.log('🔐 WhatsApp authenticated successfully');
    sendToPython({
        type: 'status',
        status: 'authenticated'
    });
});

whatsappClient.on('auth_failure', (msg) => {
    console.error('❌ Authentication failure:', msg);
    sendToPython({
        type: 'status',
        status: 'auth_failure',
        error: msg
    });
});

whatsappClient.on('disconnected', (reason) => {
    console.log('❌ WhatsApp disconnected:', reason);
    sendToPython({
        type: 'status',
        status: 'disconnected',
        reason: reason
    });
});

whatsappClient.on('message', async (message) => {
    // Only process messages from users (not from us)
    if (message.fromMe) return;
    
    console.log(`📨 Message from ${message.from}: ${message.body}`);
    
    // Get contact info
    const contact = await message.getContact();
    
    // Send to Python for processing
    sendToPython({
        type: 'incoming_message',
        message: {
            id: message.id._serialized,
            from: message.from,
            body: message.body,
            timestamp: message.timestamp,
            hasMedia: message.hasMedia,
            isGroup: message.from.includes('@g.us'),
            contact: {
                name: contact.name || contact.pushname || contact.number,
                number: contact.number,
                isMyContact: contact.isMyContact
            }
        }
    });
});

whatsappClient.on('message_create', async (message) => {
    // Track our own sent messages
    if (message.fromMe) {
        console.log(`📤 Sent message to ${message.to}: ${message.body}`);
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    const status = {
        whatsapp: whatsappClient.info ? 'connected' : 'disconnected',
        python: pythonClient ? 'connected' : 'disconnected',
        uptime: process.uptime()
    };
    res.json(status);
});

app.listen(3000, () => {
    console.log('🌐 Health check server running on http://localhost:3000/health');
});

// Initialize WhatsApp client
console.log('🚀 Starting WhatsApp Bridge Server...');
console.log(`🔌 WebSocket server listening on port ${PORT}`);
console.log('⏳ Initializing WhatsApp client...');

whatsappClient.initialize();

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n👋 Shutting down gracefully...');
    await whatsappClient.destroy();
    wss.close();
    process.exit(0);
});
