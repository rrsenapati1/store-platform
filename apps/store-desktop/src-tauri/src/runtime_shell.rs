use crate::runtime_paths::{resolve_hostname, runtime_cache_db_path, runtime_home_dir};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use uuid::Uuid;

const INSTALLATION_ID_FILE_NAME: &str = "store-runtime-installation-id";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct StoreRuntimeShellStatus {
    pub runtime_kind: String,
    pub runtime_label: String,
    pub bridge_state: String,
    pub app_version: Option<String>,
    pub hostname: Option<String>,
    pub operating_system: Option<String>,
    pub architecture: Option<String>,
    pub installation_id: Option<String>,
    pub claim_code: Option<String>,
    pub runtime_home: Option<String>,
    pub cache_db_path: Option<String>,
}

#[tauri::command]
pub fn cmd_get_store_runtime_shell_status(app: tauri::AppHandle) -> Result<StoreRuntimeShellStatus, String> {
    let app_version = app.package_info().version.to_string();
    resolve_runtime_shell_status(app_version, runtime_home_dir(), runtime_cache_db_path())
}

fn resolve_runtime_shell_status(
    app_version: String,
    runtime_home: PathBuf,
    cache_db_path: PathBuf,
) -> Result<StoreRuntimeShellStatus, String> {
    let installation_id = load_or_create_installation_id(&runtime_home)?;

    Ok(StoreRuntimeShellStatus {
        runtime_kind: "packaged_desktop".to_string(),
        runtime_label: "Store Desktop packaged runtime".to_string(),
        bridge_state: "ready".to_string(),
        app_version: Some(app_version),
        hostname: resolve_hostname(),
        operating_system: Some(std::env::consts::OS.to_string()),
        architecture: Some(std::env::consts::ARCH.to_string()),
        claim_code: Some(build_claim_code(&installation_id)),
        installation_id: Some(installation_id),
        runtime_home: Some(runtime_home.display().to_string()),
        cache_db_path: Some(cache_db_path.display().to_string()),
    })
}

fn build_claim_code(installation_id: &str) -> String {
    let normalized = installation_id
        .chars()
        .filter(|character| character.is_ascii_alphanumeric())
        .collect::<String>()
        .to_uppercase();
    let suffix = if normalized.len() > 8 {
        normalized[normalized.len() - 8..].to_string()
    } else if normalized.is_empty() {
        "UNBOUND00".to_string()
    } else {
        normalized
    };
    format!("STORE-{}", suffix)
}

fn load_or_create_installation_id(runtime_home: &Path) -> Result<String, String> {
    let installation_id_path = runtime_home.join(INSTALLATION_ID_FILE_NAME);

    if let Ok(existing) = fs::read_to_string(&installation_id_path) {
        let trimmed = existing.trim();
        if !trimmed.is_empty() {
            return Ok(trimmed.to_string());
        }
    }

    let installation_id = format!("store-runtime-{}", Uuid::new_v4().simple());
    fs::write(&installation_id_path, &installation_id).map_err(|err| err.to_string())?;
    Ok(installation_id)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn runtime_shell_status_persists_a_stable_installation_identity() {
        let temp = tempdir().expect("create temp dir");
        let runtime_home = temp.path().to_path_buf();
        let cache_db_path = runtime_home.join("store-runtime-cache.sqlite3");

        let first = resolve_runtime_shell_status("0.1.0".to_string(), runtime_home.clone(), cache_db_path.clone())
            .expect("resolve first shell status");
        let second = resolve_runtime_shell_status("0.1.0".to_string(), runtime_home.clone(), cache_db_path)
            .expect("resolve second shell status");

        assert_eq!(first.runtime_kind, "packaged_desktop");
        assert_eq!(first.runtime_label, "Store Desktop packaged runtime");
        assert_eq!(first.bridge_state, "ready");
        assert_eq!(first.app_version.as_deref(), Some("0.1.0"));
        assert_eq!(first.installation_id, second.installation_id);
        let expected_suffix = first
            .installation_id
            .clone()
            .expect("installation id")
            .chars()
            .filter(|character| character.is_ascii_alphanumeric())
            .collect::<String>()
            .to_uppercase();
        assert_eq!(
            first.claim_code.as_deref(),
            Some(format!("STORE-{}", &expected_suffix[expected_suffix.len() - 8..]).as_str())
        );
        assert!(first.installation_id.as_deref().is_some_and(|value| value.starts_with("store-runtime-")));
        assert_eq!(first.runtime_home.as_deref(), Some(runtime_home.display().to_string().as_str()));
        assert!(first.cache_db_path.as_deref().is_some_and(|value| value.ends_with("store-runtime-cache.sqlite3")));
    }
}
