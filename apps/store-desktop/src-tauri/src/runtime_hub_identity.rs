use crate::runtime_paths::runtime_home_dir;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};
#[cfg(windows)]
use windows::Win32::Foundation::{HLOCAL, LocalFree};
#[cfg(windows)]
use windows::Win32::Security::Cryptography::{
    CRYPT_INTEGER_BLOB, CRYPTPROTECT_UI_FORBIDDEN, CryptProtectData, CryptUnprotectData,
};

const STORE_RUNTIME_HUB_IDENTITY_FILE_NAME: &str = "store-runtime-hub-identity.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeHubIdentityRecord {
    pub schema_version: u32,
    pub installation_id: String,
    pub tenant_id: String,
    pub branch_id: String,
    pub device_id: String,
    pub device_code: String,
    pub sync_access_secret: String,
    pub issued_at: String,
}

pub fn runtime_hub_identity_path() -> PathBuf {
    runtime_hub_identity_path_for(&runtime_home_dir())
}

pub(crate) fn runtime_hub_identity_path_for(runtime_home: &Path) -> PathBuf {
    runtime_home.join(STORE_RUNTIME_HUB_IDENTITY_FILE_NAME)
}

#[cfg(windows)]
fn to_crypto_blob(bytes: &[u8]) -> CRYPT_INTEGER_BLOB {
    CRYPT_INTEGER_BLOB {
        cbData: bytes.len() as u32,
        pbData: bytes.as_ptr() as *mut u8,
    }
}

#[cfg(windows)]
fn into_vec_and_free(blob: CRYPT_INTEGER_BLOB) -> Result<Vec<u8>, String> {
    if blob.pbData.is_null() || blob.cbData == 0 {
        return Ok(Vec::new());
    }

    let bytes = unsafe { std::slice::from_raw_parts(blob.pbData, blob.cbData as usize).to_vec() };
    unsafe {
        let freed = LocalFree(Some(HLOCAL(blob.pbData as *mut core::ffi::c_void)));
        if !freed.is_invalid() {
            return Err("Failed to release protected runtime hub identity buffer".to_string());
        }
    }
    Ok(bytes)
}

#[cfg(windows)]
fn protect_payload(payload: &[u8]) -> Result<Vec<u8>, String> {
    let input = to_crypto_blob(payload);
    let mut output = CRYPT_INTEGER_BLOB::default();
    unsafe {
        CryptProtectData(
            &input,
            windows::core::PCWSTR::null(),
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            &mut output,
        )
        .map_err(|err| format!("Failed to protect runtime hub identity payload: {err}"))?;
    }
    into_vec_and_free(output)
}

#[cfg(not(windows))]
fn protect_payload(payload: &[u8]) -> Result<Vec<u8>, String> {
    Ok(payload.to_vec())
}

#[cfg(windows)]
fn unprotect_payload(payload: &[u8]) -> Result<Vec<u8>, String> {
    let input = to_crypto_blob(payload);
    let mut output = CRYPT_INTEGER_BLOB::default();
    unsafe {
        CryptUnprotectData(
            &input,
            None,
            None,
            None,
            None,
            CRYPTPROTECT_UI_FORBIDDEN,
            &mut output,
        )
        .map_err(|err| format!("Failed to unprotect runtime hub identity payload: {err}"))?;
    }
    into_vec_and_free(output)
}

#[cfg(not(windows))]
fn unprotect_payload(payload: &[u8]) -> Result<Vec<u8>, String> {
    Ok(payload.to_vec())
}

fn load_raw_json_payload(path: &Path) -> Result<Option<String>, String> {
    if !path.exists() {
        return Ok(None);
    }
    let protected = fs::read(path).map_err(|err| format!("Failed to read {}: {err}", path.display()))?;
    let decrypted = unprotect_payload(&protected)?;
    String::from_utf8(decrypted)
        .map(Some)
        .map_err(|err| format!("Failed to decode {}: {err}", path.display()))
}

fn save_raw_json_payload(path: &Path, payload: &str) -> Result<(), String> {
    let value: Value =
        serde_json::from_str(payload).map_err(|err| format!("Invalid runtime hub identity JSON payload: {err}"))?;
    let encoded = serde_json::to_string_pretty(&value)
        .map_err(|err| format!("Failed to encode runtime hub identity JSON payload: {err}"))?;
    let protected = protect_payload(encoded.as_bytes())?;
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|err| format!("Failed to prepare {}: {err}", parent.display()))?;
    }
    let temp_path = path.with_extension("tmp");
    fs::write(&temp_path, protected)
        .map_err(|err| format!("Failed to write {}: {err}", temp_path.display()))?;
    fs::rename(&temp_path, path)
        .map_err(|err| format!("Failed to finalize {}: {err}", path.display()))
}

#[tauri::command]
pub fn cmd_load_store_runtime_hub_identity() -> Result<Option<StoreRuntimeHubIdentityRecord>, String> {
    load_hub_identity(&runtime_hub_identity_path())
}

#[tauri::command]
pub fn cmd_save_store_runtime_hub_identity(hub_identity: StoreRuntimeHubIdentityRecord) -> Result<(), String> {
    save_hub_identity(&runtime_hub_identity_path(), &hub_identity)
}

#[tauri::command]
pub fn cmd_clear_store_runtime_hub_identity() -> Result<(), String> {
    clear_hub_identity(&runtime_hub_identity_path())
}

pub fn load_hub_identity(path: &Path) -> Result<Option<StoreRuntimeHubIdentityRecord>, String> {
    let Some(raw) = load_raw_json_payload(path)? else {
        return Ok(None);
    };
    match serde_json::from_str::<StoreRuntimeHubIdentityRecord>(&raw) {
        Ok(hub_identity) => Ok(Some(hub_identity)),
        Err(_) => {
            clear_hub_identity(path)?;
            Ok(None)
        }
    }
}

pub(crate) fn save_hub_identity(path: &Path, hub_identity: &StoreRuntimeHubIdentityRecord) -> Result<(), String> {
    let encoded = serde_json::to_string_pretty(hub_identity)
        .map_err(|err| format!("Failed to encode runtime hub identity {}: {err}", path.display()))?;
    save_raw_json_payload(path, &encoded)
}

pub(crate) fn clear_hub_identity(path: &Path) -> Result<(), String> {
    if !path.exists() {
        return Ok(());
    }
    fs::remove_file(path).map_err(|err| format!("Failed to remove {}: {err}", path.display()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime_paths::runtime_home_test_guard;
    use std::env;
    use uuid::Uuid;

    fn sample_hub_identity() -> StoreRuntimeHubIdentityRecord {
        StoreRuntimeHubIdentityRecord {
            schema_version: 1,
            installation_id: "store-runtime-abcd1234efgh5678".to_string(),
            tenant_id: "tenant-acme".to_string(),
            branch_id: "branch-1".to_string(),
            device_id: "device-1".to_string(),
            device_code: "counter-1".to_string(),
            sync_access_secret: "hub-secret-1".to_string(),
            issued_at: "2026-04-14T08:00:00.000Z".to_string(),
        }
    }

    #[test]
    fn runtime_hub_identity_round_trips_through_native_store() {
        let _guard = runtime_home_test_guard()
            .lock()
            .expect("lock runtime-home guard");
        let previous_runtime_home = env::var("STORE_RUNTIME_HOME").ok();
        let runtime_home = env::temp_dir().join(format!(
            "store-runtime-hub-identity-store-{}",
            Uuid::new_v4()
        ));
        fs::create_dir_all(&runtime_home).expect("create runtime home");
        env::set_var(
            "STORE_RUNTIME_HOME",
            runtime_home.to_string_lossy().to_string(),
        );

        let hub_identity = sample_hub_identity();

        save_hub_identity(&runtime_hub_identity_path(), &hub_identity).expect("persist hub identity");
        let loaded = load_hub_identity(&runtime_hub_identity_path())
            .expect("load hub identity")
            .expect("hub identity should exist");
        clear_hub_identity(&runtime_hub_identity_path()).expect("clear hub identity");
        let missing = load_hub_identity(&runtime_hub_identity_path()).expect("load cleared hub identity");

        assert_eq!(loaded, hub_identity);
        assert!(missing.is_none());

        if let Some(value) = previous_runtime_home {
            env::set_var("STORE_RUNTIME_HOME", value);
        } else {
            env::remove_var("STORE_RUNTIME_HOME");
        }
        let _ = fs::remove_dir_all(runtime_home);
    }
}
