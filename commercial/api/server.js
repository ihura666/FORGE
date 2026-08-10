const fs = require("fs");
"use strict";

require("dotenv").config();

const express = require("express");
const cors = require("cors");
const crypto = require("crypto");
const Database = require("better-sqlite3");
const path = require("path");

const app = express();

/* --------------------------------------------------------------------------
   Configuration
   -------------------------------------------------------------------------- */

const PORT = Number(process.env.PORT || 8787);

const LICENSE_SECRET =
    process.env.LICENSE_SECRET || "";

const ADMIN_SECRET =
    process.env.ADMIN_SECRET || "";

const MAX_ACTIVATIONS = Math.max(
    1,
    Number(process.env.MAX_ACTIVATIONS || 2)
);

const DATABASE_PATH = path.resolve(
    process.env.DATABASE_PATH || "./data/forge.db"
);

fs.mkdirSync(
    path.dirname(DATABASE_PATH),
    { recursive: true }
);

const PAYSTACK_PUBLIC_KEY =
    process.env.PAYSTACK_PUBLIC_KEY || "";

const PAYSTACK_SECRET_KEY =
    process.env.PAYSTACK_SECRET_KEY || "";

const PAYSTACK_WEBHOOK_SECRET =
    process.env.PAYSTACK_WEBHOOK_SECRET ||
    PAYSTACK_SECRET_KEY;

const PAYSTACK_CALLBACK_URL =
    process.env.PAYSTACK_CALLBACK_URL ||
    `http://127.0.0.1:${PORT}/payment/callback`;

const PRODUCT =
    process.env.FORGE_PRODUCT || "FORGE";

const PLAN =
    process.env.FORGE_PLAN || "pro";

const PRICE = Number(
    process.env.FORGE_PRICE || 4000
);

const CURRENCY = String(
    process.env.FORGE_CURRENCY || "KES"
).toUpperCase();

const PAYSTACK_AMOUNT = Math.round(
    PRICE * 100
);

/* --------------------------------------------------------------------------
   Configuration validation
   -------------------------------------------------------------------------- */

if (!LICENSE_SECRET) {
    console.warn(
        "WARNING: LICENSE_SECRET is not configured"
    );
}

if (!ADMIN_SECRET) {
    console.warn(
        "WARNING: ADMIN_SECRET is not configured"
    );
}

if (!PAYSTACK_PUBLIC_KEY) {
    console.warn(
        "WARNING: PAYSTACK_PUBLIC_KEY is not configured"
    );
}

if (!PAYSTACK_SECRET_KEY) {
    console.warn(
        "WARNING: PAYSTACK_SECRET_KEY is not configured"
    );
}

if (!Number.isFinite(PRICE) || PRICE <= 0) {
    console.error(
        "ERROR: FORGE_PRICE must be a positive number"
    );

    process.exit(1);
}

if (!CURRENCY) {
    console.error(
        "ERROR: FORGE_CURRENCY is required"
    );

    process.exit(1);
}

/* --------------------------------------------------------------------------
   Middleware
   -------------------------------------------------------------------------- */

app.use(cors());

app.use(
    express.json({
        limit: "1mb",
        verify: (req, res, buffer) => {
            req.rawBody = buffer.toString("utf8");
        }
    })
);

/* --------------------------------------------------------------------------
   Database
   -------------------------------------------------------------------------- */

const db = new Database(DATABASE_PATH);

db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

db.exec(`
    CREATE TABLE IF NOT EXISTS licenses (
        id TEXT PRIMARY KEY,
        key_hash TEXT NOT NULL UNIQUE,
        product TEXT NOT NULL,
        plan TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT
    );

    CREATE TABLE IF NOT EXISTS activations (
        id TEXT PRIMARY KEY,
        license_id TEXT NOT NULL,
        machine_id TEXT NOT NULL,
        activated_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        FOREIGN KEY (license_id)
            REFERENCES licenses(id)
            ON DELETE CASCADE,
        UNIQUE (license_id, machine_id)
    );

    CREATE TABLE IF NOT EXISTS customers (
        id TEXT PRIMARY KEY,
        email TEXT NOT NULL UNIQUE,
        name TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        product TEXT NOT NULL,
        plan TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL,
        tx_ref TEXT NOT NULL UNIQUE,
        license_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        provider TEXT,
        provider_reference TEXT,
        FOREIGN KEY (customer_id)
            REFERENCES customers(id),
        FOREIGN KEY (license_id)
            REFERENCES licenses(id)
    );

    CREATE TABLE IF NOT EXISTS payments (
        id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        provider_transaction_id TEXT,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL,
        raw_event TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (order_id)
            REFERENCES orders(id)
    );
`);

/* --------------------------------------------------------------------------
   Database compatibility
   -------------------------------------------------------------------------- */

function hasColumn(table, column) {
    return db
        .prepare(`PRAGMA table_info(${table})`)
        .all()
        .some(row => row.name === column);
}

if (!hasColumn("licenses", "key_hash")) {
    db.exec(`
        ALTER TABLE licenses
        ADD COLUMN key_hash TEXT;
    `);
}

if (!hasColumn("activations", "last_seen_at")) {
    db.exec(`
        ALTER TABLE activations
        ADD COLUMN last_seen_at TEXT;
    `);

    db.prepare(`
        UPDATE activations
        SET last_seen_at = activated_at
        WHERE last_seen_at IS NULL
    `).run();
}

if (!hasColumn("orders", "tx_ref")) {
    db.exec(`
        ALTER TABLE orders
        ADD COLUMN tx_ref TEXT;
    `);
}

if (!hasColumn("orders", "provider")) {
    db.exec(`
        ALTER TABLE orders
        ADD COLUMN provider TEXT;
    `);
}

if (!hasColumn("orders", "provider_reference")) {
    db.exec(`
        ALTER TABLE orders
        ADD COLUMN provider_reference TEXT;
    `);
}

const ordersWithoutTxRef = db
    .prepare(`
        SELECT id
        FROM orders
        WHERE tx_ref IS NULL
           OR tx_ref = ''
    `)
    .all();

for (const order of ordersWithoutTxRef) {
    db.prepare(`
        UPDATE orders
        SET tx_ref = ?
        WHERE id = ?
    `).run(
        `LEGACY-${order.id}`,
        order.id
    );
}

/* --------------------------------------------------------------------------
   Helpers
   -------------------------------------------------------------------------- */

function now() {
    return new Date().toISOString();
}

function randomId() {
    return crypto
        .randomBytes(32)
        .toString("hex");
}

function hashLicenseKey(key) {
    return crypto
        .createHash("sha256")
        .update(`${LICENSE_SECRET}:${key}`)
        .digest("hex");
}

function createLicenseKey() {
    const groups = [];

    for (let i = 0; i < 6; i++) {
        groups.push(
            crypto
                .randomBytes(3)
                .toString("hex")
                .toUpperCase()
        );
    }

    return groups.join("-");
}

function normalizeMachineId(machineId) {
    return String(machineId || "")
        .trim()
        .slice(0, 255);
}

function normalizeEmail(email) {
    return String(email || "")
        .trim()
        .toLowerCase();
}

function validEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
        email
    );
}

function generateTxRef() {
    return (
        "FORGE-" +
        Date.now()
            .toString(36)
            .toUpperCase() +
        "-" +
        crypto
            .randomBytes(8)
            .toString("hex")
            .toUpperCase()
    );
}

function safeCompare(a, b) {
    const left = Buffer.from(
        String(a || "")
    );

    const right = Buffer.from(
        String(b || "")
    );

    if (left.length !== right.length) {
        return false;
    }

    return crypto.timingSafeEqual(
        left,
        right
    );
}

/* --------------------------------------------------------------------------
   Paystack
   -------------------------------------------------------------------------- */

async function paystackRequest(
    endpoint,
    options = {}
) {
    if (!PAYSTACK_SECRET_KEY) {
        throw new Error(
            "PAYSTACK_SECRET_KEY is not configured"
        );
    }

    const response = await fetch(
        `https://api.paystack.co${endpoint}`,
        {
            ...options,

            headers: {
                Authorization:
                    `Bearer ${PAYSTACK_SECRET_KEY}`,

                "Content-Type":
                    "application/json",

                ...(options.headers || {})
            }
        }
    );

    const text =
        await response.text();

    let data;

    try {
        data = JSON.parse(text);
    } catch {
        throw new Error(
            `Paystack returned invalid JSON (${response.status})`
        );
    }

    if (!response.ok || !data.status) {
        throw new Error(
            data.message ||
            `Paystack request failed with HTTP ${response.status}`
        );
    }

    return data;
}

async function verifyPaystackTransaction(
    reference
) {
    const result =
        await paystackRequest(
            `/transaction/verify/${encodeURIComponent(
                reference
            )}`,
            {
                method: "GET"
            }
        );

    return result.data;
}

/* --------------------------------------------------------------------------
   License creation
   -------------------------------------------------------------------------- */

function issueLicenseInternal(
    product = PRODUCT,
    plan = PLAN
) {
    let licenseKey;
    let keyHash;

    do {
        licenseKey =
            createLicenseKey();

        keyHash =
            hashLicenseKey(
                licenseKey
            );

    } while (
        db
            .prepare(`
                SELECT id
                FROM licenses
                WHERE key_hash = ?
            `)
            .get(keyHash)
    );

    const id = keyHash;
    const createdAt = now();

    db.prepare(`
        INSERT INTO licenses (
            id,
            key_hash,
            product,
            plan,
            status,
            created_at,
            expires_at
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            'active',
            ?,
            NULL
        )
    `).run(
        id,
        keyHash,
        product,
        plan,
        createdAt
    );

    return {
        id,
        license_key: licenseKey,
        product,
        plan,
        status: "active",
        created_at: createdAt,
        expires_at: null
    };
}

/* --------------------------------------------------------------------------
   License lookup
   -------------------------------------------------------------------------- */

function findLicense(licenseKey) {
    if (!licenseKey) {
        return null;
    }

    const keyHash =
        hashLicenseKey(
            licenseKey
        );

    return db
        .prepare(`
            SELECT *
            FROM licenses
            WHERE key_hash = ?
        `)
        .get(keyHash);
}

/* --------------------------------------------------------------------------
   Admin authentication
   -------------------------------------------------------------------------- */

function requireAdmin(
    req,
    res,
    next
) {
    if (!ADMIN_SECRET) {
        return res.status(500).json({
            error:
                "admin_secret_not_configured"
        });
    }

    const supplied =
        req.headers["x-admin-secret"] ||
        req.headers["authorization"]
            ?.replace(
                /^Bearer\s+/i,
                ""
            );

    if (
        !supplied ||
        !safeCompare(
            supplied,
            ADMIN_SECRET
        )
    ) {
        return res.status(401).json({
            error: "unauthorized"
        });
    }

    next();
}

/* --------------------------------------------------------------------------
   Health
   -------------------------------------------------------------------------- */

app.get("/", (req, res) => {
    return res.json({
        status: "ok",
        service: "FORGE License API",
        payment_provider: "paystack",
        product: PRODUCT,
        plan: PLAN,
        price: PRICE,
        currency: CURRENCY
    });
});

app.get("/health", (req, res) => {
    return res.json({
        status: "ok",
        service: "FORGE License API",
        database: DATABASE_PATH,
        payment_provider:
            PAYSTACK_SECRET_KEY
                ? "paystack"
                : "not_configured",
        currency: CURRENCY,
        price: PRICE,
        max_activations:
            MAX_ACTIVATIONS
    });
});

/* --------------------------------------------------------------------------
   Admin: issue license
   -------------------------------------------------------------------------- */

app.post(
    "/license/issue",
    requireAdmin,
    (req, res) => {
        try {
            const product =
                req.body?.product ||
                PRODUCT;

            const plan =
                req.body?.plan ||
                PLAN;

            const license =
                issueLicenseInternal(
                    product,
                    plan
                );

            return res
                .status(201)
                .json(license);

        } catch (error) {
            console.error(
                "License issue error:",
                error
            );

            return res.status(500).json({
                error:
                    "license_issue_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   License validation
   -------------------------------------------------------------------------- */

app.post(
    "/license/validate",
    (req, res) => {
        try {
            const licenseKey =
                req.body?.license_key;

            const license =
                findLicense(
                    licenseKey
                );

            if (!license) {
                return res.status(404).json({
                    valid: false,
                    error:
                        "license_not_found"
                });
            }

            if (
                license.status !==
                "active"
            ) {
                return res.status(403).json({
                    valid: false,
                    error:
                        "license_inactive",
                    status:
                        license.status
                });
            }

            return res.json({
                valid: true,
                product:
                    license.product,
                plan:
                    license.plan,
                status:
                    license.status,
                expires_at:
                    license.expires_at
            });

        } catch (error) {
            console.error(
                "License validation error:",
                error
            );

            return res.status(500).json({
                error:
                    "license_validation_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   License activation
   -------------------------------------------------------------------------- */

app.post(
    "/license/activate",
    (req, res) => {
        try {
            const licenseKey =
                req.body?.license_key;

            const machineId =
                normalizeMachineId(
                    req.body?.machine_id
                );

            if (
                !licenseKey ||
                !machineId
            ) {
                return res.status(400).json({
                    error:
                        "license_key_and_machine_id_required"
                });
            }

            const license =
                findLicense(
                    licenseKey
                );

            if (!license) {
                return res.status(404).json({
                    error:
                        "license_not_found"
                });
            }

            if (
                license.status !==
                "active"
            ) {
                return res.status(403).json({
                    error:
                        "license_inactive",
                    status:
                        license.status
                });
            }

            const existing =
                db
                    .prepare(`
                        SELECT *
                        FROM activations
                        WHERE license_id = ?
                        AND machine_id = ?
                    `)
                    .get(
                        license.id,
                        machineId
                    );

            if (existing) {
                db.prepare(`
                    UPDATE activations
                    SET last_seen_at = ?
                    WHERE id = ?
                `).run(
                    now(),
                    existing.id
                );

                const count =
                    db
                        .prepare(`
                            SELECT COUNT(*) AS count
                            FROM activations
                            WHERE license_id = ?
                        `)
                        .get(
                            license.id
                        )
                        .count;

                return res.json({
                    valid: true,
                    activated: true,
                    existing: true,
                    product:
                        license.product,
                    plan:
                        license.plan,
                    activation_count:
                        count,
                    activation_limit:
                        MAX_ACTIVATIONS
                });
            }

            const activationCount =
                db
                    .prepare(`
                        SELECT COUNT(*) AS count
                        FROM activations
                        WHERE license_id = ?
                    `)
                    .get(
                        license.id
                    )
                    .count;

            if (
                activationCount >=
                MAX_ACTIVATIONS
            ) {
                return res.status(403).json({
                    valid: true,
                    activated: false,
                    error:
                        "activation_limit_reached",
                    activation_count:
                        activationCount,
                    activation_limit:
                        MAX_ACTIVATIONS
                });
            }

            const timestamp = now();

            db.prepare(`
                INSERT INTO activations (
                    id,
                    license_id,
                    machine_id,
                    activated_at,
                    last_seen_at
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
            `).run(
                randomId(),
                license.id,
                machineId,
                timestamp,
                timestamp
            );

            return res.json({
                valid: true,
                activated: true,
                existing: false,
                product:
                    license.product,
                plan:
                    license.plan,
                activation_count:
                    activationCount + 1,
                activation_limit:
                    MAX_ACTIVATIONS
            });

        } catch (error) {
            console.error(
                "License activation error:",
                error
            );

            return res.status(500).json({
                error:
                    "license_activation_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   Admin: inspect license
   -------------------------------------------------------------------------- */

app.get(
    "/admin/license/:key",
    requireAdmin,
    (req, res) => {
        try {
            const license =
                findLicense(
                    req.params.key
                );

            if (!license) {
                return res.status(404).json({
                    error:
                        "license_not_found"
                });
            }

            const activations =
                db
                    .prepare(`
                        SELECT
                            id,
                            machine_id,
                            activated_at,
                            last_seen_at
                        FROM activations
                        WHERE license_id = ?
                        ORDER BY activated_at ASC
                    `)
                    .all(
                        license.id
                    );

            return res.json({
                id:
                    license.id,

                product:
                    license.product,

                plan:
                    license.plan,

                status:
                    license.status,

                created_at:
                    license.created_at,

                expires_at:
                    license.expires_at,

                activation_count:
                    activations.length,

                activation_limit:
                    MAX_ACTIVATIONS,

                activations
            });

        } catch (error) {
            console.error(
                "Admin license lookup error:",
                error
            );

            return res.status(500).json({
                error:
                    "license_lookup_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   Admin: revoke license
   -------------------------------------------------------------------------- */

app.post(
    "/admin/license/:key/revoke",
    requireAdmin,
    (req, res) => {
        try {
            const license =
                findLicense(
                    req.params.key
                );

            if (!license) {
                return res.status(404).json({
                    error:
                        "license_not_found"
                });
            }

            db.prepare(`
                UPDATE licenses
                SET status = 'revoked'
                WHERE id = ?
            `).run(
                license.id
            );

            return res.json({
                success: true,
                id:
                    license.id,
                status:
                    "revoked"
            });

        } catch (error) {
            console.error(
                "License revoke error:",
                error
            );

            return res.status(500).json({
                error:
                    "license_revoke_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   Customer helper
   -------------------------------------------------------------------------- */

function getOrCreateCustomer(
    email,
    name = null
) {
    const normalized =
        normalizeEmail(email);

    let customer =
        db
            .prepare(`
                SELECT *
                FROM customers
                WHERE email = ?
            `)
            .get(
                normalized
            );

    if (customer) {
        return customer;
    }

    const id =
        randomId();

    const createdAt =
        now();

    db.prepare(`
        INSERT INTO customers (
            id,
            email,
            name,
            created_at
        )
        VALUES (
            ?,
            ?,
            ?,
            ?
        )
    `).run(
        id,
        normalized,
        name,
        createdAt
    );

    return db
        .prepare(`
            SELECT *
            FROM customers
            WHERE id = ?
        `)
        .get(id);
}

/* --------------------------------------------------------------------------
   Checkout creation
   -------------------------------------------------------------------------- */

app.post(
    "/checkout/create",
    async (req, res) => {
        try {
            const email =
                normalizeEmail(
                    req.body?.email
                );

            const name =
                String(
                    req.body?.name || ""
                ).trim();

            if (!validEmail(email)) {
                return res.status(400).json({
                    error:
                        "valid_email_required"
                });
            }

            if (
                !PAYSTACK_PUBLIC_KEY ||
                !PAYSTACK_SECRET_KEY
            ) {
                return res.status(503).json({
                    error:
                        "payment_provider_not_configured"
                });
            }

            const customer =
                getOrCreateCustomer(
                    email,
                    name || null
                );

            const orderId =
                randomId();

            const txRef =
                generateTxRef();

            const createdAt =
                now();

            db.prepare(`
                INSERT INTO orders (
                    id,
                    customer_id,
                    product,
                    plan,
                    amount,
                    currency,
                    status,
                    tx_ref,
                    license_id,
                    created_at,
                    updated_at,
                    provider,
                    provider_reference
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    'pending',
                    ?,
                    NULL,
                    ?,
                    ?,
                    'paystack',
                    ?
                )
            `).run(
                orderId,
                customer.id,
                PRODUCT,
                PLAN,
                PRICE,
                CURRENCY,
                txRef,
                createdAt,
                createdAt,
                txRef
            );

            let payment;

            try {
                const payload = {
                    email,

                    amount:
                        String(
                            PAYSTACK_AMOUNT
                        ),

                    currency:
                        CURRENCY,

                    reference:
                        txRef,

                    metadata: {
                        order_id:
                            orderId,

                        product:
                            PRODUCT,

                        plan:
                            PLAN
                    }
                };

                if (
                    PAYSTACK_CALLBACK_URL
                ) {
                    payload.callback_url =
                        PAYSTACK_CALLBACK_URL;
                }

                payment =
                    await paystackRequest(
                        "/transaction/initialize",
                        {
                            method: "POST",

                            body:
                                JSON.stringify(
                                    payload
                                )
                        }
                    );

            } catch (paymentError) {
                db.prepare(`
                    UPDATE orders
                    SET
                        status =
                            'initialization_failed',
                        updated_at = ?
                    WHERE id = ?
                `).run(
                    now(),
                    orderId
                );

                throw paymentError;
            }

            const paymentData =
                payment.data;

            return res
                .status(201)
                .json({
                    order_id:
                        orderId,

                    tx_ref:
                        txRef,

                    product:
                        PRODUCT,

                    plan:
                        PLAN,

                    amount:
                        PRICE,

                    currency:
                        CURRENCY,

                    public_key:
                        PAYSTACK_PUBLIC_KEY,

                    authorization_url:
                        paymentData.authorization_url,

                    access_code:
                        paymentData.access_code,

                    reference:
                        paymentData.reference
                });

        } catch (error) {
            console.error(
                "Checkout creation error:",
                error
            );

            return res.status(500).json({
                error:
                    "checkout_creation_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   Payment callback
   -------------------------------------------------------------------------- */

app.get(
    "/payment/callback",
    async (req, res) => {
        try {
            const reference =
                String(
                    req.query.reference ||
                    req.query.trxref ||
                    ""
                ).trim();

            if (!reference) {
                return res.status(400).send(`
                    <!doctype html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>FORGE Payment</title>
                    </head>
                    <body>
                        <h1>Payment reference missing</h1>
                        <p>Return to FORGE and check your payment status.</p>
                    </body>
                    </html>
                `);
            }

            const order =
                db
                    .prepare(`
                        SELECT *
                        FROM orders
                        WHERE tx_ref = ?
                    `)
                    .get(reference);

            if (!order) {
                return res.status(404).send(`
                    <!doctype html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>FORGE Payment</title>
                    </head>
                    <body>
                        <h1>Order not found</h1>
                        <p>The payment reference could not be matched to a FORGE order.</p>
                    </body>
                    </html>
                `);
            }

            if (order.status === "paid") {
                return res.send(`
                    <!doctype html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <title>FORGE Payment Complete</title>
                    </head>
                    <body>
                        <h1>Payment received</h1>
                        <p>Your FORGE order has been paid successfully.</p>
                        <p>Your license has been issued.</p>
                    </body>
                    </html>
                `);
            }

            let transaction;

            try {
                transaction =
                    await verifyPaystackTransaction(
                        reference
                    );
            } catch (error) {
                console.error(
                    "Callback verification error:",
                    error
                );

                return res.status(502).send(`
                    <!doctype html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>FORGE Payment</title>
                    </head>
                    <body>
                        <h1>Payment verification pending</h1>
                        <p>We could not verify the transaction yet.</p>
                        <p>Reference: ${reference}</p>
                    </body>
                    </html>
                `);
            }

            if (
                transaction.status !==
                "success"
            ) {
                return res.send(`
                    <!doctype html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>FORGE Payment</title>
                    </head>
                    <body>
                        <h1>Payment not completed</h1>
                        <p>Transaction status: ${transaction.status}</p>
                    </body>
                    </html>
                `);
            }

            if (
                String(
                    transaction.reference || ""
                ) !== reference
            ) {
                return res.status(400).send(`
                    <!doctype html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>FORGE Payment</title>
                    </head>
                    <body>
                        <h1>Payment reference mismatch</h1>
                    </body>
                    </html>
                `);
            }

            if (
                Number(transaction.amount) !==
                PAYSTACK_AMOUNT
            ) {
                return res.status(400).send(`
                    <!doctype html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>FORGE Payment</title>
                    </head>
                    <body>
                        <h1>Payment amount mismatch</h1>
                    </body>
                    </html>
                `);
            }

            if (
                String(
                    transaction.currency || ""
                ).toUpperCase() !==
                CURRENCY
            ) {
                return res.status(400).send(`
                    <!doctype html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>FORGE Payment</title>
                    </head>
                    <body>
                        <h1>Payment currency mismatch</h1>
                    </body>
                    </html>
                `);
            }

            return res.send(`
                <!doctype html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>FORGE Payment Complete</title>
                </head>
                <body>
                    <h1>Payment verified</h1>
                    <p>Your payment has been verified.</p>
                    <p>Your FORGE license is being finalized.</p>
                    <p>Reference: ${reference}</p>
                </body>
                </html>
            `);

        } catch (error) {
            console.error(
                "Payment callback error:",
                error
            );

            return res.status(500).send(`
                <!doctype html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>FORGE Payment</title>
                </head>
                <body>
                    <h1>Payment processing error</h1>
                    <p>Please check your order status.</p>
                </body>
                </html>
            `);
        }
    }
);

/* --------------------------------------------------------------------------
   Paystack webhook
   -------------------------------------------------------------------------- */

app.post(
    "/webhooks/paystack",
    async (req, res) => {
        try {
            if (!PAYSTACK_WEBHOOK_SECRET) {
                return res.status(500).json({
                    error:
                        "webhook_secret_not_configured"
                });
            }

            const suppliedSignature =
                req.headers[
                    "x-paystack-signature"
                ];

            if (!suppliedSignature) {
                return res.status(401).json({
                    error:
                        "missing_paystack_signature"
                });
            }

            const rawBody =
                req.rawBody || "";

            const expectedSignature =
                crypto
                    .createHmac(
                        "sha512",
                        PAYSTACK_WEBHOOK_SECRET
                    )
                    .update(
                        rawBody
                    )
                    .digest("hex");

            if (
                !safeCompare(
                    suppliedSignature,
                    expectedSignature
                )
            ) {
                return res.status(401).json({
                    error:
                        "invalid_paystack_signature"
                });
            }

            const event =
                req.body || {};

            if (
                event.event !==
                "charge.success"
            ) {
                return res.status(200).json({
                    received: true,
                    ignored: true
                });
            }

            const data =
                event.data || {};

            const reference =
                String(
                    data.reference || ""
                );

            if (!reference) {
                return res.status(400).json({
                    error:
                        "missing_transaction_reference"
                });
            }

            const order =
                db
                    .prepare(`
                        SELECT *
                        FROM orders
                        WHERE tx_ref = ?
                    `)
                    .get(
                        reference
                    );

            if (!order) {
                return res.status(404).json({
                    error:
                        "order_not_found"
                });
            }

            if (
                order.status ===
                "paid"
            ) {
                return res.status(200).json({
                    received: true,
                    duplicate: true
                });
            }

            const transaction =
                await verifyPaystackTransaction(
                    reference
                );

            if (
                transaction.status !==
                "success"
            ) {
                return res.status(400).json({
                    error:
                        "payment_not_successful",
                    status:
                        transaction.status
                });
            }

            if (
                String(
                    transaction.reference || ""
                ) !== reference
            ) {
                return res.status(400).json({
                    error:
                        "payment_reference_mismatch"
                });
            }

            if (
                Number(transaction.amount) !==
                PAYSTACK_AMOUNT
            ) {
                db.prepare(`
                    UPDATE orders
                    SET
                        status =
                            'amount_mismatch',
                        updated_at = ?
                    WHERE id = ?
                `).run(
                    now(),
                    order.id
                );

                return res.status(400).json({
                    error:
                        "payment_amount_mismatch"
                });
            }

            const paidCurrency =
                String(
                    transaction.currency || ""
                ).toUpperCase();

            if (
                paidCurrency !==
                String(
                    order.currency
                ).toUpperCase()
            ) {
                db.prepare(`
                    UPDATE orders
                    SET
                        status =
                            'currency_mismatch',
                        updated_at = ?
                    WHERE id = ?
                `).run(
                    now(),
                    order.id
                );

                return res.status(400).json({
                    error:
                        "payment_currency_mismatch"
                });
            }

            const fulfill =
                db.transaction(() => {
                    const existingPayment =
                        db
                            .prepare(`
                                SELECT id
                                FROM payments
                                WHERE provider = 'paystack'
                                AND provider_transaction_id = ?
                            `)
                            .get(
                                String(
                                    transaction.id
                                )
                            );

                    if (
                        existingPayment
                    ) {
                        db.prepare(`
                            UPDATE orders
                            SET
                                status = 'paid',
                                updated_at = ?
                            WHERE id = ?
                        `).run(
                            now(),
                            order.id
                        );

                        return null;
                    }

                    const license =
                        issueLicenseInternal(
                            order.product,
                            order.plan
                        );

                    db.prepare(`
                        INSERT INTO payments (
                            id,
                            order_id,
                            provider,
                            provider_transaction_id,
                            amount,
                            currency,
                            status,
                            raw_event,
                            created_at
                        )
                        VALUES (
                            ?,
                            ?,
                            'paystack',
                            ?,
                            ?,
                            ?,
                            'successful',
                            ?,
                            ?
                        )
                    `).run(
                        randomId(),
                        order.id,
                        String(
                            transaction.id
                        ),
                        PRICE,
                        paidCurrency,
                        JSON.stringify(
                            event
                        ),
                        now()
                    );

                    db.prepare(`
                        UPDATE orders
                        SET
                            status = 'paid',
                            license_id = ?,
                            provider_reference = ?,
                            updated_at = ?
                        WHERE id = ?
                    `).run(
                        license.id,
                        reference,
                        now(),
                        order.id
                    );

                    return license;
                });

            const license =
                fulfill();

            if (!license) {
                return res.status(200).json({
                    received: true,
                    duplicate: true
                });
            }

            console.log(
                `Payment successful: ${reference}`
            );

            console.log(
                `License issued: ${license.id}`
            );

            return res.status(200).json({
                received: true,
                paid: true,
                order_id:
                    order.id
            });

        } catch (error) {
            console.error(
                "Paystack webhook error:",
                error
            );

            return res.status(500).json({
                error:
                    "payment_processing_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   Payment status
   -------------------------------------------------------------------------- */

app.get(
    "/checkout/status/:reference",
    async (req, res) => {
        try {
            const reference =
                String(
                    req.params.reference ||
                    ""
                ).trim();

            if (!reference) {
                return res.status(400).json({
                    error:
                        "reference_required"
                });
            }

            const order =
                db
                    .prepare(`
                        SELECT
                            id,
                            product,
                            plan,
                            amount,
                            currency,
                            status,
                            tx_ref,
                            license_id,
                            created_at,
                            updated_at
                        FROM orders
                        WHERE tx_ref = ?
                    `)
                    .get(
                        reference
                    );

            if (!order) {
                return res.status(404).json({
                    error:
                        "order_not_found"
                });
            }

            return res.json({
                order_id:
                    order.id,

                reference:
                    order.tx_ref,

                status:
                    order.status,

                product:
                    order.product,

                plan:
                    order.plan,

                amount:
                    order.amount,

                currency:
                    order.currency,

                license_issued:
                    Boolean(
                        order.license_id
                    )
            });

        } catch (error) {
            console.error(
                "Checkout status error:",
                error
            );

            return res.status(500).json({
                error:
                    "checkout_status_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   Admin: order lookup
   -------------------------------------------------------------------------- */

app.get(
    "/admin/order/:id",
    requireAdmin,
    (req, res) => {
        try {
            const order =
                db
                    .prepare(`
                        SELECT
                            o.*,
                            c.email,
                            c.name
                        FROM orders o
                        JOIN customers c
                            ON c.id = o.customer_id
                        WHERE o.id = ?
                    `)
                    .get(
                        req.params.id
                    );

            if (!order) {
                return res.status(404).json({
                    error:
                        "order_not_found"
                });
            }

            return res.json(order);

        } catch (error) {
            console.error(
                "Order lookup error:",
                error
            );

            return res.status(500).json({
                error:
                    "order_lookup_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   Admin: payment lookup
   -------------------------------------------------------------------------- */

app.get(
    "/admin/payment/:id",
    requireAdmin,
    (req, res) => {
        try {
            const payment =
                db
                    .prepare(`
                        SELECT *
                        FROM payments
                        WHERE id = ?
                    `)
                    .get(
                        req.params.id
                    );

            if (!payment) {
                return res.status(404).json({
                    error:
                        "payment_not_found"
                });
            }

            return res.json(payment);

        } catch (error) {
            console.error(
                "Payment lookup error:",
                error
            );

            return res.status(500).json({
                error:
                    "payment_lookup_failed"
            });
        }
    }
);

/* --------------------------------------------------------------------------
   404
   -------------------------------------------------------------------------- */

app.use(
    (req, res) => {
        return res.status(404).json({
            error: "not_found"
        });
    }
);

/* --------------------------------------------------------------------------
   Error handler
   -------------------------------------------------------------------------- */

app.use(
    (
        error,
        req,
        res,
        next
    ) => {
        console.error(
            "Unhandled server error:",
            error
        );

        if (res.headersSent) {
            return next(error);
        }

        return res.status(500).json({
            error:
                "internal_server_error"
        });
    }
);

/* --------------------------------------------------------------------------
   Start
   -------------------------------------------------------------------------- */

const server =
    app.listen(
        PORT,
        "0.0.0.0",
        () => {
            console.log(
                `FORGE License API listening on port ${PORT}`
            );

            console.log(
                `Database: ${DATABASE_PATH}`
            );

            console.log(
                `Maximum activations per license: ${MAX_ACTIVATIONS}`
            );

            console.log(
                `Payment provider: ${
                    PAYSTACK_SECRET_KEY
                        ? "Paystack configured"
                        : "not configured"
                }`
            );

            console.log(
                `Product: ${PRODUCT}`
            );

            console.log(
                `Plan: ${PLAN}`
            );

            console.log(
                `Price: ${PRICE} ${CURRENCY}`
            );

            console.log(
                `Paystack amount: ${PAYSTACK_AMOUNT} subunits`
            );

            console.log(
                `Callback URL: ${PAYSTACK_CALLBACK_URL}`
            );
        }
    );
/* --------------------------------------------------------------------------
   Shutdown
   -------------------------------------------------------------------------- */

function shutdown(signal) {
    console.log(
        `${signal} received. Shutting down...`
    );

    server.close(() => {
        db.close();
        process.exit(0);
    });
}

process.on(
    "SIGINT",
    () => shutdown("SIGINT")
);

process.on(
    "SIGTERM",
    () => shutdown("SIGTERM")
);
