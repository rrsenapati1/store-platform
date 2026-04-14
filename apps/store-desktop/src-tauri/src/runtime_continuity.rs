use rusqlite::{params, Connection, OptionalExtension};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::path::Path;

use crate::runtime_paths::{ensure_dir, runtime_continuity_db_path};

const CONTINUITY_KEY: &str = "store.runtime-continuity.v1";
const CONTINUITY_SCHEMA_VERSION: u64 = 1;
const CONTINUITY_AUTHORITY: &str = "BRANCH_HUB_CONTINUITY";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeContinuityPersistenceStatus {
    pub authority: String,
    pub backend_kind: String,
    pub backend_label: String,
    pub cached_at: Option<String>,
    pub detail: Option<String>,
    pub location: Option<String>,
    pub snapshot_present: bool,
}

#[tauri::command]
pub fn cmd_load_store_runtime_continuity() -> Result<Option<Value>, String> {
    load_snapshot(&runtime_continuity_db_path())
}

#[tauri::command]
pub fn cmd_save_store_runtime_continuity(
    snapshot: Value,
) -> Result<StoreRuntimeContinuityPersistenceStatus, String> {
    save_snapshot(&runtime_continuity_db_path(), &snapshot)
}

#[tauri::command]
pub fn cmd_clear_store_runtime_continuity() -> Result<StoreRuntimeContinuityPersistenceStatus, String> {
    clear_snapshot(&runtime_continuity_db_path())
}

#[tauri::command]
pub fn cmd_get_store_runtime_continuity_status() -> Result<StoreRuntimeContinuityPersistenceStatus, String> {
    snapshot_status(&runtime_continuity_db_path())
}

fn open_connection(db_path: &Path) -> Result<Connection, String> {
    if let Some(parent) = db_path.parent() {
        ensure_dir(parent);
    }
    let connection = Connection::open(db_path).map_err(|err| err.to_string())?;
    connection
        .execute_batch(
            "
            PRAGMA journal_mode = WAL;
            CREATE TABLE IF NOT EXISTS continuity_entries (
              continuity_key TEXT PRIMARY KEY,
              snapshot_json TEXT NOT NULL,
              cached_at TEXT,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            ",
        )
        .map_err(|err| err.to_string())?;
    Ok(connection)
}

fn validate_snapshot(snapshot: &Value) -> Result<Option<String>, String> {
    let object = snapshot
        .as_object()
        .ok_or_else(|| "runtime continuity snapshot must be a JSON object".to_string())?;
    if object
        .get("schema_version")
        .and_then(Value::as_u64)
        != Some(CONTINUITY_SCHEMA_VERSION)
    {
        return Err("runtime continuity snapshot schema_version is invalid".to_string());
    }
    if object
        .get("authority")
        .and_then(Value::as_str)
        != Some(CONTINUITY_AUTHORITY)
    {
        return Err("runtime continuity authority must remain BRANCH_HUB_CONTINUITY".to_string());
    }

    for field in ["inventory_snapshot", "offline_sales", "conflicts"] {
        if !object.get(field).is_some_and(Value::is_array) {
            return Err(format!("runtime continuity snapshot field `{field}` must be an array"));
        }
    }

    if object
        .get("next_continuity_invoice_sequence")
        .and_then(Value::as_u64)
        .is_none()
    {
        return Err("runtime continuity snapshot next_continuity_invoice_sequence is invalid".to_string());
    }

    Ok(object
        .get("cached_at")
        .and_then(Value::as_str)
        .map(ToOwned::to_owned))
}

fn build_status(
    db_path: &Path,
    cached_at: Option<String>,
    snapshot_present: bool,
) -> StoreRuntimeContinuityPersistenceStatus {
    StoreRuntimeContinuityPersistenceStatus {
        authority: CONTINUITY_AUTHORITY.to_string(),
        backend_kind: "native_sqlite".to_string(),
        backend_label: "Native SQLite continuity store".to_string(),
        cached_at,
        detail: None,
        location: Some(db_path.display().to_string()),
        snapshot_present,
    }
}

fn save_snapshot(
    db_path: &Path,
    snapshot: &Value,
) -> Result<StoreRuntimeContinuityPersistenceStatus, String> {
    let cached_at = validate_snapshot(snapshot)?;
    let connection = open_connection(db_path)?;
    let payload = serde_json::to_string(snapshot).map_err(|err| err.to_string())?;
    connection
        .execute(
            "
            INSERT INTO continuity_entries (continuity_key, snapshot_json, cached_at, updated_at)
            VALUES (?1, ?2, ?3, CURRENT_TIMESTAMP)
            ON CONFLICT(continuity_key) DO UPDATE SET
              snapshot_json = excluded.snapshot_json,
              cached_at = excluded.cached_at,
              updated_at = CURRENT_TIMESTAMP
            ",
            params![CONTINUITY_KEY, payload, cached_at],
        )
        .map_err(|err| err.to_string())?;

    snapshot_status(db_path)
}

fn load_snapshot(db_path: &Path) -> Result<Option<Value>, String> {
    let connection = open_connection(db_path)?;
    let Some(snapshot_json) = connection
        .query_row(
            "SELECT snapshot_json FROM continuity_entries WHERE continuity_key = ?1",
            params![CONTINUITY_KEY],
            |row| row.get::<_, String>(0),
        )
        .optional()
        .map_err(|err| err.to_string())?
    else {
        return Ok(None);
    };

    let parsed: Value = match serde_json::from_str(&snapshot_json) {
        Ok(value) => value,
        Err(_) => {
            clear_snapshot(db_path)?;
            return Ok(None);
        }
    };

    if validate_snapshot(&parsed).is_err() {
        clear_snapshot(db_path)?;
        return Ok(None);
    }

    Ok(Some(parsed))
}

fn clear_snapshot(db_path: &Path) -> Result<StoreRuntimeContinuityPersistenceStatus, String> {
    let connection = open_connection(db_path)?;
    connection
        .execute(
            "DELETE FROM continuity_entries WHERE continuity_key = ?1",
            params![CONTINUITY_KEY],
        )
        .map_err(|err| err.to_string())?;
    Ok(build_status(db_path, None, false))
}

fn snapshot_status(db_path: &Path) -> Result<StoreRuntimeContinuityPersistenceStatus, String> {
    let connection = open_connection(db_path)?;
    let record = connection
        .query_row(
            "SELECT cached_at FROM continuity_entries WHERE continuity_key = ?1",
            params![CONTINUITY_KEY],
            |row| row.get::<_, Option<String>>(0),
        )
        .optional()
        .map_err(|err| err.to_string())?;
    let snapshot_present = record.is_some();
    let cached_at = record.flatten();

    Ok(build_status(db_path, cached_at, snapshot_present))
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    fn sample_snapshot() -> Value {
        serde_json::json!({
            "schema_version": 1,
            "authority": "BRANCH_HUB_CONTINUITY",
            "cached_at": "2026-04-14T18:00:00.000Z",
            "tenant_id": "tenant-acme",
            "branch_id": "branch-1",
            "branch_code": "blrflagship",
            "hub_device_id": "device-hub-1",
            "next_continuity_invoice_sequence": 2,
            "inventory_snapshot": [],
            "offline_sales": [
                {
                    "continuity_sale_id": "offline-sale-1",
                    "continuity_invoice_number": "OFF-BLRFLAGSHIP-0001",
                    "customer_name": "Walk-in Customer",
                    "payment_method": "Cash",
                    "grand_total": 388.5,
                    "issued_offline_at": "2026-04-14T18:00:00.000Z",
                    "reconciliation_state": "PENDING_REPLAY",
                    "lines": []
                }
            ],
            "conflicts": [],
            "last_reconciled_at": null
        })
    }

    #[test]
    fn runtime_continuity_persists_and_clears_snapshot() {
        let temp = tempdir().expect("create temp dir");
        let db_path = temp.path().join("runtime-continuity.sqlite3");

        let saved = save_snapshot(&db_path, &sample_snapshot()).expect("save snapshot");
        assert_eq!(saved.backend_kind, "native_sqlite");
        assert_eq!(saved.authority, "BRANCH_HUB_CONTINUITY");
        assert!(saved.snapshot_present);

        let loaded = load_snapshot(&db_path).expect("load snapshot");
        assert_eq!(loaded, Some(sample_snapshot()));

        let cleared = clear_snapshot(&db_path).expect("clear snapshot");
        assert!(!cleared.snapshot_present);
        assert_eq!(load_snapshot(&db_path).expect("reload snapshot"), None);
    }
}
