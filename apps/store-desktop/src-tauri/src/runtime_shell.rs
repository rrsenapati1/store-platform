use crate::runtime_hub_identity::{load_hub_identity, runtime_hub_identity_path_for};
use crate::runtime_hub_service::{clear_runtime_hub_service, ensure_runtime_hub_service};
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
    pub hub_service_state: Option<String>,
    pub hub_service_url: Option<String>,
    pub hub_manifest_url: Option<String>,
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
    let hub_identity = load_hub_identity(&runtime_hub_identity_path_for(&runtime_home))?;
    let hub_service_status = hub_identity
        .filter(|identity| identity.installation_id == installation_id)
        .map(|identity| ensure_runtime_hub_service(&identity))
        .transpose()?;
    if hub_service_status.is_none() {
        clear_runtime_hub_service();
    }

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
        hub_service_state: hub_service_status.as_ref().map(|status| status.state.clone()),
        hub_service_url: hub_service_status.as_ref().map(|status| status.base_url.clone()),
        hub_manifest_url: hub_service_status.map(|status| status.manifest_url),
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
    use crate::runtime_hub_identity::{
        runtime_hub_identity_path_for, save_hub_identity, StoreRuntimeHubIdentityRecord,
    };
    use crate::runtime_hub_service::clear_runtime_hub_service;
    use tempfile::tempdir;
    use std::io::{Read, Write};
    use std::net::TcpStream;

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
        assert_eq!(first.hub_service_state, None);
        assert_eq!(first.hub_service_url, None);
        assert_eq!(first.hub_manifest_url, None);
    }

    #[test]
    fn runtime_shell_status_exposes_loopback_hub_service_for_hub_identities() {
        let temp = tempdir().expect("create temp dir");
        let runtime_home = temp.path().to_path_buf();
        let cache_db_path = runtime_home.join("store-runtime-cache.sqlite3");
        std::fs::create_dir_all(&runtime_home).expect("create runtime home");

        save_hub_identity(&runtime_hub_identity_path_for(&runtime_home), &StoreRuntimeHubIdentityRecord {
            schema_version: 1,
            installation_id: "store-runtime-abcd1234efgh5678".to_string(),
            tenant_id: "tenant-acme".to_string(),
            branch_id: "branch-1".to_string(),
            device_id: "device-hub-1".to_string(),
            device_code: "BLR-HUB-01".to_string(),
            sync_access_secret: "hub-secret-1".to_string(),
            issued_at: "2026-04-14T08:00:00.000Z".to_string(),
        }).expect("save hub identity");
        std::fs::write(
            runtime_home.join(INSTALLATION_ID_FILE_NAME),
            "store-runtime-abcd1234efgh5678",
        ).expect("seed installation id");

        let status = resolve_runtime_shell_status("0.1.0".to_string(), runtime_home, cache_db_path)
            .expect("resolve shell status");

        assert_eq!(status.hub_service_state.as_deref(), Some("ready"));
        let health_response = http_get(
            status.hub_service_url.as_deref().expect("hub service url"),
            "/healthz",
        );
        assert!(health_response.contains("\"status\":\"ready\""));
        let manifest_response = http_get(
            status.hub_service_url.as_deref().expect("hub service url"),
            "/v1/spoke-manifest",
        );
        assert!(manifest_response.contains("\"hub_device_id\":\"device-hub-1\""));
        assert!(manifest_response.contains("\"auth_mode\":\"spoke_runtime_token_pending\""));

        clear_runtime_hub_service();
    }

    fn http_get(base_url: &str, path: &str) -> String {
        let host = base_url.trim_start_matches("http://");
        let mut stream = TcpStream::connect(host).expect("connect to hub service");
        let request = format!("GET {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n", path, host);
        stream.write_all(request.as_bytes()).expect("write request");
        let mut response = String::new();
        stream.read_to_string(&mut response).expect("read response");
        response
    }
}
