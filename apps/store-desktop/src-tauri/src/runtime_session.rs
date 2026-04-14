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

const STORE_RUNTIME_SESSION_FILE_NAME: &str = "store-runtime-session.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeSessionRecord {
    pub access_token: String,
    pub expires_at: String,
}

fn runtime_session_path() -> PathBuf {
    runtime_home_dir().join(STORE_RUNTIME_SESSION_FILE_NAME)
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
            return Err("Failed to release protected runtime session buffer".to_string());
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
        .map_err(|err| format!("Failed to protect runtime session payload: {err}"))?;
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
        .map_err(|err| format!("Failed to unprotect runtime session payload: {err}"))?;
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
        serde_json::from_str(payload).map_err(|err| format!("Invalid runtime session JSON payload: {err}"))?;
    let encoded = serde_json::to_string_pretty(&value)
        .map_err(|err| format!("Failed to encode runtime session JSON payload: {err}"))?;
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
pub fn cmd_load_store_runtime_session() -> Result<Option<StoreRuntimeSessionRecord>, String> {
    load_session(&runtime_session_path())
}

#[tauri::command]
pub fn cmd_save_store_runtime_session(session: StoreRuntimeSessionRecord) -> Result<(), String> {
    save_session(&runtime_session_path(), &session)
}

#[tauri::command]
pub fn cmd_clear_store_runtime_session() -> Result<(), String> {
    clear_session(&runtime_session_path())
}

fn load_session(path: &Path) -> Result<Option<StoreRuntimeSessionRecord>, String> {
    let Some(raw) = load_raw_json_payload(path)? else {
        return Ok(None);
    };
    match serde_json::from_str::<StoreRuntimeSessionRecord>(&raw) {
        Ok(session) => Ok(Some(session)),
        Err(_) => {
            clear_session(path)?;
            Ok(None)
        }
    }
}

fn save_session(path: &Path, session: &StoreRuntimeSessionRecord) -> Result<(), String> {
    let encoded = serde_json::to_string_pretty(session)
        .map_err(|err| format!("Failed to encode runtime session {}: {err}", path.display()))?;
    save_raw_json_payload(path, &encoded)
}

fn clear_session(path: &Path) -> Result<(), String> {
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

    #[test]
    fn runtime_session_round_trips_through_native_store() {
        let _guard = runtime_home_test_guard()
            .lock()
            .expect("lock runtime-home guard");
        let previous_runtime_home = env::var("STORE_RUNTIME_HOME").ok();
        let runtime_home = env::temp_dir().join(format!(
            "store-runtime-session-store-{}",
            Uuid::new_v4()
        ));
        fs::create_dir_all(&runtime_home).expect("create runtime home");
        env::set_var(
            "STORE_RUNTIME_HOME",
            runtime_home.to_string_lossy().to_string(),
        );

        let session = StoreRuntimeSessionRecord {
            access_token: "session-cashier-token".to_string(),
            expires_at: "2026-04-14T18:00:00.000Z".to_string(),
        };

        save_session(&runtime_session_path(), &session).expect("persist session");
        let loaded = load_session(&runtime_session_path())
            .expect("load session")
            .expect("session should exist");
        clear_session(&runtime_session_path()).expect("clear session");
        let missing = load_session(&runtime_session_path()).expect("load cleared session");

        assert_eq!(loaded, session);
        assert!(missing.is_none());

        if let Some(value) = previous_runtime_home {
            env::set_var("STORE_RUNTIME_HOME", value);
        } else {
            env::remove_var("STORE_RUNTIME_HOME");
        }
        let _ = fs::remove_dir_all(runtime_home);
    }

    #[test]
    fn runtime_session_is_not_persisted_as_plain_json() {
        let _guard = runtime_home_test_guard()
            .lock()
            .expect("lock runtime-home guard");
        let previous_runtime_home = env::var("STORE_RUNTIME_HOME").ok();
        let runtime_home = env::temp_dir().join(format!(
            "store-runtime-session-store-encrypted-{}",
            Uuid::new_v4()
        ));
        fs::create_dir_all(&runtime_home).expect("create runtime home");
        env::set_var(
            "STORE_RUNTIME_HOME",
            runtime_home.to_string_lossy().to_string(),
        );

        let session = StoreRuntimeSessionRecord {
            access_token: "session-cashier-token".to_string(),
            expires_at: "2026-04-14T18:00:00.000Z".to_string(),
        };

        save_session(&runtime_session_path(), &session).expect("persist session");
        let stored_bytes = fs::read(runtime_session_path()).expect("read protected file");
        clear_session(&runtime_session_path()).expect("clear session");

        #[cfg(windows)]
        {
            assert!(!stored_bytes
                .windows(b"session-cashier-token".len())
                .any(|window| window == b"session-cashier-token"));
            assert_ne!(stored_bytes.first().copied(), Some(b'{'));
        }

        #[cfg(not(windows))]
        {
            assert!(!stored_bytes.is_empty());
        }

        if let Some(value) = previous_runtime_home {
            env::set_var("STORE_RUNTIME_HOME", value);
        } else {
            env::remove_var("STORE_RUNTIME_HOME");
        }
        let _ = fs::remove_dir_all(runtime_home);
    }
}
