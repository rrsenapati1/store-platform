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

const STORE_RUNTIME_LOCAL_AUTH_FILE_NAME: &str = "store-runtime-local-auth.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeLocalAuthRecord {
    pub schema_version: u32,
    pub installation_id: String,
    pub device_id: String,
    pub staff_profile_id: String,
    pub local_auth_token: String,
    pub activation_version: u32,
    pub offline_valid_until: String,
    pub pin_attempt_limit: u32,
    pub pin_lockout_seconds: u32,
    pub pin_salt: String,
    pub pin_hash: String,
    pub failed_attempts: u32,
    pub locked_until: Option<String>,
    pub enrolled_at: String,
    pub last_unlocked_at: Option<String>,
}

fn runtime_local_auth_path() -> PathBuf {
    runtime_home_dir().join(STORE_RUNTIME_LOCAL_AUTH_FILE_NAME)
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
            return Err("Failed to release protected runtime local auth buffer".to_string());
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
        .map_err(|err| format!("Failed to protect runtime local auth payload: {err}"))?;
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
        .map_err(|err| format!("Failed to unprotect runtime local auth payload: {err}"))?;
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
        serde_json::from_str(payload).map_err(|err| format!("Invalid runtime local auth JSON payload: {err}"))?;
    let encoded = serde_json::to_string_pretty(&value)
        .map_err(|err| format!("Failed to encode runtime local auth JSON payload: {err}"))?;
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
pub fn cmd_load_store_runtime_local_auth() -> Result<Option<StoreRuntimeLocalAuthRecord>, String> {
    load_local_auth(&runtime_local_auth_path())
}

#[tauri::command]
pub fn cmd_save_store_runtime_local_auth(local_auth: StoreRuntimeLocalAuthRecord) -> Result<(), String> {
    save_local_auth(&runtime_local_auth_path(), &local_auth)
}

#[tauri::command]
pub fn cmd_clear_store_runtime_local_auth() -> Result<(), String> {
    clear_local_auth(&runtime_local_auth_path())
}

fn load_local_auth(path: &Path) -> Result<Option<StoreRuntimeLocalAuthRecord>, String> {
    let Some(raw) = load_raw_json_payload(path)? else {
        return Ok(None);
    };
    match serde_json::from_str::<StoreRuntimeLocalAuthRecord>(&raw) {
        Ok(local_auth) => Ok(Some(local_auth)),
        Err(_) => {
            clear_local_auth(path)?;
            Ok(None)
        }
    }
}

fn save_local_auth(path: &Path, local_auth: &StoreRuntimeLocalAuthRecord) -> Result<(), String> {
    let encoded = serde_json::to_string_pretty(local_auth)
        .map_err(|err| format!("Failed to encode runtime local auth {}: {err}", path.display()))?;
    save_raw_json_payload(path, &encoded)
}

fn clear_local_auth(path: &Path) -> Result<(), String> {
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

    fn sample_local_auth() -> StoreRuntimeLocalAuthRecord {
        StoreRuntimeLocalAuthRecord {
            schema_version: 1,
            installation_id: "store-runtime-abcd1234efgh5678".to_string(),
            device_id: "device-1".to_string(),
            staff_profile_id: "staff-1".to_string(),
            local_auth_token: "local-auth-seed-1".to_string(),
            activation_version: 1,
            offline_valid_until: "2026-04-15T18:00:00.000Z".to_string(),
            pin_attempt_limit: 5,
            pin_lockout_seconds: 300,
            pin_salt: "salt".to_string(),
            pin_hash: "hash".to_string(),
            failed_attempts: 0,
            locked_until: None,
            enrolled_at: "2026-04-14T07:00:00.000Z".to_string(),
            last_unlocked_at: None,
        }
    }

    #[test]
    fn runtime_local_auth_round_trips_through_native_store() {
        let _guard = runtime_home_test_guard()
            .lock()
            .expect("lock runtime-home guard");
        let previous_runtime_home = env::var("STORE_RUNTIME_HOME").ok();
        let runtime_home = env::temp_dir().join(format!(
            "store-runtime-local-auth-store-{}",
            Uuid::new_v4()
        ));
        fs::create_dir_all(&runtime_home).expect("create runtime home");
        env::set_var(
            "STORE_RUNTIME_HOME",
            runtime_home.to_string_lossy().to_string(),
        );

        let local_auth = sample_local_auth();

        save_local_auth(&runtime_local_auth_path(), &local_auth).expect("persist local auth");
        let loaded = load_local_auth(&runtime_local_auth_path())
            .expect("load local auth")
            .expect("local auth should exist");
        clear_local_auth(&runtime_local_auth_path()).expect("clear local auth");
        let missing = load_local_auth(&runtime_local_auth_path()).expect("load cleared local auth");

        assert_eq!(loaded, local_auth);
        assert!(missing.is_none());

        if let Some(value) = previous_runtime_home {
            env::set_var("STORE_RUNTIME_HOME", value);
        } else {
            env::remove_var("STORE_RUNTIME_HOME");
        }
        let _ = fs::remove_dir_all(runtime_home);
    }
}
