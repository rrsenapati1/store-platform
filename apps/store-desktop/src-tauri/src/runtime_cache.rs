use rusqlite::{params, Connection, OptionalExtension};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::path::Path;

use crate::runtime_paths::{ensure_dir, runtime_cache_db_path};

const CACHE_KEY: &str = "store.runtime-cache.v1";
const CACHE_SCHEMA_VERSION: u64 = 1;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeCachePersistenceStatus {
    pub backend_kind: String,
    pub backend_label: String,
    pub cached_at: Option<String>,
    pub detail: Option<String>,
    pub location: Option<String>,
    pub snapshot_present: bool,
}

#[tauri::command]
pub fn cmd_load_store_runtime_cache() -> Result<Option<Value>, String> {
    load_snapshot(&runtime_cache_db_path())
}

#[tauri::command]
pub fn cmd_save_store_runtime_cache(snapshot: Value) -> Result<StoreRuntimeCachePersistenceStatus, String> {
    save_snapshot(&runtime_cache_db_path(), &snapshot)
}

#[tauri::command]
pub fn cmd_clear_store_runtime_cache() -> Result<StoreRuntimeCachePersistenceStatus, String> {
    clear_snapshot(&runtime_cache_db_path())
}

#[tauri::command]
pub fn cmd_get_store_runtime_cache_status() -> Result<StoreRuntimeCachePersistenceStatus, String> {
    snapshot_status(&runtime_cache_db_path())
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
            CREATE TABLE IF NOT EXISTS runtime_cache_entries (
              cache_key TEXT PRIMARY KEY,
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
        .ok_or_else(|| "runtime cache snapshot must be a JSON object".to_string())?;
    if object
        .get("schema_version")
        .and_then(Value::as_u64)
        != Some(CACHE_SCHEMA_VERSION)
    {
        return Err("runtime cache snapshot schema_version is invalid".to_string());
    }
    if object
        .get("authority")
        .and_then(Value::as_str)
        != Some("CONTROL_PLANE_ONLY")
    {
        return Err("runtime cache snapshot authority must remain CONTROL_PLANE_ONLY".to_string());
    }

    for field in [
        "branches",
        "branch_catalog_items",
        "inventory_snapshot",
        "sales",
        "runtime_devices",
        "print_jobs",
        "pending_mutations",
    ] {
        if !object.get(field).is_some_and(Value::is_array) {
            return Err(format!("runtime cache snapshot field `{field}` must be an array"));
        }
    }

    Ok(object
        .get("cached_at")
        .and_then(Value::as_str)
        .map(ToOwned::to_owned))
}

fn build_status(db_path: &Path, cached_at: Option<String>, snapshot_present: bool) -> StoreRuntimeCachePersistenceStatus {
    StoreRuntimeCachePersistenceStatus {
        backend_kind: "native_sqlite".to_string(),
        backend_label: "Native SQLite runtime cache".to_string(),
        cached_at,
        detail: None,
        location: Some(db_path.display().to_string()),
        snapshot_present,
    }
}

fn save_snapshot(db_path: &Path, snapshot: &Value) -> Result<StoreRuntimeCachePersistenceStatus, String> {
    let cached_at = validate_snapshot(snapshot)?;
    let connection = open_connection(db_path)?;
    let payload = serde_json::to_string(snapshot).map_err(|err| err.to_string())?;
    connection
        .execute(
            "
            INSERT INTO runtime_cache_entries (cache_key, snapshot_json, cached_at, updated_at)
            VALUES (?1, ?2, ?3, CURRENT_TIMESTAMP)
            ON CONFLICT(cache_key) DO UPDATE SET
              snapshot_json = excluded.snapshot_json,
              cached_at = excluded.cached_at,
              updated_at = CURRENT_TIMESTAMP
            ",
            params![CACHE_KEY, payload, cached_at],
        )
        .map_err(|err| err.to_string())?;

    snapshot_status(db_path)
}

fn load_snapshot(db_path: &Path) -> Result<Option<Value>, String> {
    let connection = open_connection(db_path)?;
    let Some(snapshot_json) = connection
        .query_row(
            "SELECT snapshot_json FROM runtime_cache_entries WHERE cache_key = ?1",
            params![CACHE_KEY],
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

fn clear_snapshot(db_path: &Path) -> Result<StoreRuntimeCachePersistenceStatus, String> {
    let connection = open_connection(db_path)?;
    connection
        .execute(
            "DELETE FROM runtime_cache_entries WHERE cache_key = ?1",
            params![CACHE_KEY],
        )
        .map_err(|err| err.to_string())?;
    Ok(build_status(db_path, None, false))
}

fn snapshot_status(db_path: &Path) -> Result<StoreRuntimeCachePersistenceStatus, String> {
    let connection = open_connection(db_path)?;
    let record = connection
        .query_row(
            "SELECT cached_at FROM runtime_cache_entries WHERE cache_key = ?1",
            params![CACHE_KEY],
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
            "cached_at": "2026-04-14T05:00:00.000Z",
            "authority": "CONTROL_PLANE_ONLY",
            "actor": null,
            "tenant": null,
            "branches": [],
            "branch_catalog_items": [],
            "inventory_snapshot": [],
            "sales": [],
            "runtime_devices": [],
            "selected_runtime_device_id": "",
            "runtime_heartbeat": null,
            "print_jobs": [],
            "latest_print_job": null,
            "latest_sale": null,
            "latest_sale_return": null,
            "latest_exchange": null,
            "pending_mutations": []
        })
    }

    #[test]
    fn runtime_cache_persists_and_clears_snapshot() {
        let temp = tempdir().expect("create temp dir");
        let db_path = temp.path().join("runtime-cache.sqlite3");

        let saved = save_snapshot(&db_path, &sample_snapshot()).expect("save snapshot");
        assert_eq!(saved.backend_kind, "native_sqlite");
        assert!(saved.snapshot_present);

        let loaded = load_snapshot(&db_path).expect("load snapshot");
        assert_eq!(loaded, Some(sample_snapshot()));

        let cleared = clear_snapshot(&db_path).expect("clear snapshot");
        assert!(!cleared.snapshot_present);
        assert_eq!(load_snapshot(&db_path).expect("reload snapshot"), None);
    }

    #[test]
    fn runtime_cache_drops_invalid_snapshot_shape() {
        let temp = tempdir().expect("create temp dir");
        let db_path = temp.path().join("runtime-cache.sqlite3");
        let connection = open_connection(&db_path).expect("open connection");
        connection
            .execute(
                "
                INSERT INTO runtime_cache_entries (cache_key, snapshot_json, cached_at, updated_at)
                VALUES (?1, ?2, ?3, CURRENT_TIMESTAMP)
                ",
                params![
                    CACHE_KEY,
                    serde_json::json!({
                        "schema_version": 99,
                        "authority": "BROKEN",
                        "branches": []
                    })
                    .to_string(),
                    "2026-04-14T05:00:00.000Z"
                ],
            )
            .expect("seed invalid snapshot");

        let loaded = load_snapshot(&db_path).expect("load invalid snapshot");
        assert_eq!(loaded, None);

        let status = snapshot_status(&db_path).expect("status after invalid snapshot cleanup");
        assert!(!status.snapshot_present);
    }
}
