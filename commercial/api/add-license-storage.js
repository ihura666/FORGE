"use strict";

require("dotenv").config();

const Database = require("better-sqlite3");
const path = require("path");

const DATABASE_PATH = path.resolve(
    process.env.DATABASE_PATH || "./data/forge.db"
);

const db = new Database(
    DATABASE_PATH
);

function hasColumn(table, column) {
    return db
        .prepare(
            `PRAGMA table_info(${table})`
        )
        .all()
        .some(
            row => row.name === column
        );
}

try {

    console.log(
        "FORGE license storage migration"
    );

    console.log(
        `Database: ${DATABASE_PATH}`
    );

    if (
        !hasColumn(
            "licenses",
            "encrypted_key"
        )
    ) {

        db.exec(`
            ALTER TABLE licenses
            ADD COLUMN encrypted_key TEXT;
        `);

        console.log(
            "Added licenses.encrypted_key"
        );

    } else {

        console.log(
            "licenses.encrypted_key already exists"
        );
    }

    if (
        !hasColumn(
            "orders",
            "delivery_token_hash"
        )
    ) {

        db.exec(`
            ALTER TABLE orders
            ADD COLUMN delivery_token_hash TEXT;
        `);

        console.log(
            "Added orders.delivery_token_hash"
        );

    } else {

        console.log(
            "orders.delivery_token_hash already exists"
        );
    }

    if (
        !hasColumn(
            "orders",
            "license_delivered_at"
        )
    ) {

        db.exec(`
            ALTER TABLE orders
            ADD COLUMN license_delivered_at TEXT;
        `);

        console.log(
            "Added orders.license_delivered_at"
        );

    } else {

        console.log(
            "orders.license_delivered_at already exists"
        );
    }

    console.log(
        "Migration completed successfully."
    );

} catch (error) {

    console.error(
        "Migration failed:",
        error
    );

    process.exitCode = 1;

} finally {

    db.close();

}
