/**
 * WhatsApp Gateway Service — GA System
 *
 * Self-hosted WhatsApp sender using Baileys.
 * Native Node.js http server (no Express).
 *
 * Endpoints:
 *   GET  /api/status        — connection health check
 *   POST /api/send-message  — send a WhatsApp text message
 */

'use strict';

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

// ── Load .env (simple, no dotenv dependency) ─────────────────────
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
    fs.readFileSync(envPath, 'utf-8')
        .split('\n')
        .filter((l) => l.trim() && !l.startsWith('#'))
        .forEach((l) => {
            const idx = l.indexOf('=');
            if (idx > 0) {
                process.env[l.slice(0, idx).trim()] = l.slice(idx + 1).trim();
            }
        });
}

const PORT = Number(process.env.PORT) || 3001;
const API_KEY = process.env.API_KEY || '';

// ── Baileys ──────────────────────────────────────────────────────
const {
    default: makeWASocket,
    useMultiFileAuthState,
    DisconnectReason,
    fetchLatestBaileysVersion,
} = require('@whiskeysockets/baileys');
const pino = require('pino');
const qrTerminal = require('qrcode-terminal');

let sock = null;
let isConnected = false;
let qrCode = null; // store latest QR string

async function connectWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(
        path.join(__dirname, 'auth_info'),
    );
    const { version } = await fetchLatestBaileysVersion();

    sock = makeWASocket({
        version,
        auth: state,
        logger: pino({ level: 'silent' }),
        browser: ['GA System', 'Server', '1.0.0'],
    });

    // Persist credentials when updated
    sock.ev.on('creds.update', saveCreds);

    // Connection lifecycle
    sock.ev.on('connection.update', ({ connection, lastDisconnect, qr }) => {
        if (qr) {
            qrCode = qr;
            console.log('\n' + '='.repeat(50));
            console.log('📱 SCAN QR CODE BERIKUT DENGAN WHATSAPP:');
            console.log('   Buka WhatsApp → Menu (⋮) → Linked Devices → Link a Device');
            console.log('='.repeat(50));
            qrTerminal.generate(qr, { small: true });
            console.log('='.repeat(50));
            console.log('💡 Atau buka di browser: http://localhost:' + PORT + '/api/qr');
            console.log('='.repeat(50) + '\n');
        }

        if (connection === 'close') {
            isConnected = false;
            qrCode = null;
            const statusCode =
                lastDisconnect?.error?.output?.statusCode ?? 0;
            const loggedOut = statusCode === DisconnectReason.loggedOut;

            if (loggedOut) {
                console.log('❌ Logged out — hapus folder auth_info/ lalu restart.');
            } else {
                console.log('🔄 Reconnecting...');
                setTimeout(connectWhatsApp, 3000);
            }
        } else if (connection === 'open') {
            isConnected = true;
            qrCode = null;
            console.log('✅ WhatsApp connected!');
        }
    });
}

// ── HTTP helpers ─────────────────────────────────────────────────

/** Read full request body as string. */
function readBody(req) {
    return new Promise((resolve, reject) => {
        const chunks = [];
        req.on('data', (c) => chunks.push(c));
        req.on('end', () => resolve(Buffer.concat(chunks).toString()));
        req.on('error', reject);
    });
}

/** Send JSON response. */
function jsonResponse(res, statusCode, data) {
    const body = JSON.stringify(data);
    res.writeHead(statusCode, {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
    });
    res.end(body);
}

/** Send HTML response. */
function htmlResponse(res, statusCode, html) {
    res.writeHead(statusCode, {
        'Content-Type': 'text/html; charset=utf-8',
        'Content-Length': Buffer.byteLength(html),
    });
    res.end(html);
}

/** Validate Authorization header. */
function isAuthorized(req) {
    if (!API_KEY) return true; // no key = open (dev only)
    const header = req.headers['authorization'] || '';
    return header === `Bearer ${API_KEY}`;
}

// ── Routes ───────────────────────────────────────────────────────

async function handleStatus(_req, res) {
    jsonResponse(res, 200, {
        connected: isConnected,
        qrPending: qrCode !== null,
    });
}

async function handleQR(_req, res) {
    if (isConnected) {
        return htmlResponse(res, 200, `
            <html><body style="font-family:sans-serif;text-align:center;padding:50px">
                <h2 style="color:green">✅ WhatsApp Sudah Terhubung!</h2>
                <p>Tidak perlu scan QR lagi.</p>
            </body></html>
        `);
    }
    if (!qrCode) {
        return htmlResponse(res, 200, `
            <html><body style="font-family:sans-serif;text-align:center;padding:50px">
                <h2>⏳ Menunggu QR Code...</h2>
                <p>QR belum tersedia. Tunggu beberapa detik lalu refresh.</p>
                <script>setTimeout(()=>location.reload(), 3000)</script>
            </body></html>
        `);
    }
    // Generate QR as an image via a public API (no extra deps)
    const qrImageUrl = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qrCode)}`;
    htmlResponse(res, 200, `
        <html><head><title>WA Login — GA System</title></head>
        <body style="font-family:sans-serif;text-align:center;padding:30px;background:#f0f2f5">
            <div style="background:white;max-width:400px;margin:0 auto;padding:30px;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,.1)">
                <h2 style="color:#128C7E">📱 Scan QR dengan WhatsApp</h2>
                <img src="${qrImageUrl}" alt="QR Code" style="margin:20px 0" />
                <p style="color:#666;font-size:14px">
                    <b>Langkah:</b><br>
                    1. Buka WhatsApp di HP<br>
                    2. Tap <b>Menu (⋮)</b> atau <b>Settings</b><br>
                    3. Tap <b>Linked Devices</b><br>
                    4. Tap <b>Link a Device</b><br>
                    5. Arahkan kamera ke QR di atas
                </p>
            </div>
            <script>setTimeout(()=>location.reload(), 15000)</script>
        </body></html>
    `);
}

async function handleSendMessage(req, res) {
    // Auth check
    if (!isAuthorized(req)) {
        return jsonResponse(res, 401, {
            success: false,
            message: 'Unauthorized — invalid API key',
        });
    }

    // Parse body
    let body;
    try {
        const raw = await readBody(req);
        body = JSON.parse(raw);
    } catch {
        return jsonResponse(res, 400, {
            success: false,
            message: 'Invalid JSON body',
        });
    }

    const { phone, message } = body;

    if (!phone || !message) {
        return jsonResponse(res, 400, {
            success: false,
            message: 'Field "phone" dan "message" wajib diisi',
        });
    }

    if (!isConnected || !sock) {
        return jsonResponse(res, 503, {
            success: false,
            message: 'WhatsApp belum terhubung',
        });
    }

    try {
        // Format: 628xxx → 628xxx@s.whatsapp.net
        const jid = phone.replace(/[^0-9]/g, '') + '@s.whatsapp.net';
        await sock.sendMessage(jid, { text: message });

        console.log(`📤 Pesan terkirim ke ${phone}`);
        jsonResponse(res, 200, { success: true, message: 'Pesan terkirim' });
    } catch (err) {
        console.error(`❌ Gagal kirim ke ${phone}:`, err.message);
        jsonResponse(res, 500, { success: false, message: err.message });
    }
}

// ── Server ───────────────────────────────────────────────────────

const server = http.createServer(async (req, res) => {
    // CORS headers (optional, for dev convenience)
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type');
    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        return res.end();
    }

    const url = req.url?.split('?')[0];

    try {
        if (url === '/api/status' && req.method === 'GET') {
            await handleStatus(req, res);
        } else if (url === '/api/qr' && req.method === 'GET') {
            await handleQR(req, res);
        } else if (url === '/api/send-message' && req.method === 'POST') {
            await handleSendMessage(req, res);
        } else {
            jsonResponse(res, 404, { success: false, message: 'Not found' });
        }
    } catch (err) {
        console.error('Server error:', err);
        jsonResponse(res, 500, { success: false, message: 'Internal server error' });
    }
});

server.listen(PORT, () => {
    console.log(`\n🚀 WA Service running → http://localhost:${PORT}`);
    console.log(`   GET  /api/status       — cek koneksi WA`);
    console.log(`   GET  /api/qr           — scan QR di browser`);
    console.log(`   POST /api/send-message — kirim pesan\n`);
    connectWhatsApp();
});
