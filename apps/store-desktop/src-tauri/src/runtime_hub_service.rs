use crate::runtime_control_plane_origin::resolve_control_plane_base_url;
use crate::runtime_hub_identity::StoreRuntimeHubIdentityRecord;
use crate::runtime_spoke_registry::{RegisteredSpokeSession, RuntimeSpokeRegistry};
use reqwest::blocking::Client;
use serde::{de::DeserializeOwned, Deserialize, Serialize};
use serde_json::json;
use std::collections::HashMap;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex, OnceLock};
use std::thread::{self, JoinHandle};
use std::time::Duration;

const HEARTBEAT_INTERVAL_SECONDS: u32 = 30;
const SUPPORTED_RUNTIME_PROFILES: [&str; 4] = [
    "desktop_spoke",
    "mobile_store_spoke",
    "inventory_tablet_spoke",
    "customer_display",
];
const SUPPORTED_PAIRING_MODES: [&str; 2] = ["approval_code", "qr"];
const ALLOWED_RELAY_OPERATIONS: [&str; 4] = [
    "runtime.status",
    "runtime.print_jobs.submit",
    "runtime.print_jobs.list",
    "runtime.sync_status",
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RuntimeHubServiceStatus {
    pub state: String,
    pub base_url: String,
    pub manifest_url: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct RuntimeHubServiceSnapshot {
    installation_id: String,
    tenant_id: String,
    branch_id: String,
    hub_device_id: String,
    hub_device_code: String,
    issued_at: String,
    sync_access_secret: String,
    control_plane_base_url: String,
}

#[derive(Debug, Deserialize, Serialize)]
struct SpokeActivationRequest {
    runtime_profile: String,
    pairing_mode: String,
}

#[derive(Debug, Deserialize)]
struct SpokeRegistrationRequest {
    activation_code: String,
    installation_id: String,
    runtime_kind: String,
    runtime_profile: String,
    hostname: Option<String>,
    app_version: Option<String>,
}

#[derive(Debug, Deserialize)]
struct SpokeTokenRequest {
    spoke_runtime_token: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ControlPlaneSpokeActivationResponse {
    activation_code: String,
    pairing_mode: String,
    runtime_profile: String,
    hub_device_id: String,
    expires_at: String,
}

#[derive(Debug)]
struct ParsedHttpRequest {
    method: String,
    path: String,
    headers: HashMap<String, String>,
    body: String,
}

struct RuntimeHubServiceHandle {
    snapshot: RuntimeHubServiceSnapshot,
    status: RuntimeHubServiceStatus,
    shutdown: Arc<AtomicBool>,
    thread: Option<JoinHandle<()>>,
}

impl RuntimeHubServiceHandle {
    fn start(identity: &StoreRuntimeHubIdentityRecord) -> Result<Self, String> {
        let snapshot = RuntimeHubServiceSnapshot {
            installation_id: identity.installation_id.clone(),
            tenant_id: identity.tenant_id.clone(),
            branch_id: identity.branch_id.clone(),
            hub_device_id: identity.device_id.clone(),
            hub_device_code: identity.device_code.clone(),
            issued_at: identity.issued_at.clone(),
            sync_access_secret: identity.sync_access_secret.clone(),
            control_plane_base_url: resolve_control_plane_base_url(),
        };
        let listener = TcpListener::bind("127.0.0.1:0")
            .map_err(|err| format!("Failed to bind loopback hub service: {err}"))?;
        listener
            .set_nonblocking(true)
            .map_err(|err| format!("Failed to configure loopback hub service: {err}"))?;
        let port = listener
            .local_addr()
            .map_err(|err| format!("Failed to resolve loopback hub service address: {err}"))?
            .port();
        let status = RuntimeHubServiceStatus {
            state: "ready".to_string(),
            base_url: format!("http://127.0.0.1:{port}"),
            manifest_url: format!("http://127.0.0.1:{port}/v1/spoke-manifest"),
        };
        let registry = Arc::new(Mutex::new(RuntimeSpokeRegistry::default()));
        let shutdown = Arc::new(AtomicBool::new(false));
        let shutdown_flag = Arc::clone(&shutdown);
        let server_snapshot = snapshot.clone();
        let server_status = status.clone();
        let server_registry = Arc::clone(&registry);
        let thread = thread::spawn(move || {
            serve_loopback(
                listener,
                server_snapshot,
                server_status,
                server_registry,
                shutdown_flag,
            )
        });

        Ok(Self {
            snapshot,
            status,
            shutdown,
            thread: Some(thread),
        })
    }

    fn matches(&self, identity: &StoreRuntimeHubIdentityRecord) -> bool {
        self.snapshot.installation_id == identity.installation_id
            && self.snapshot.tenant_id == identity.tenant_id
            && self.snapshot.branch_id == identity.branch_id
            && self.snapshot.hub_device_id == identity.device_id
            && self.snapshot.hub_device_code == identity.device_code
            && self.snapshot.issued_at == identity.issued_at
            && self.snapshot.sync_access_secret == identity.sync_access_secret
    }

    fn stop(&mut self) {
        self.shutdown.store(true, Ordering::Relaxed);
        if let Some(thread) = self.thread.take() {
            let _ = thread.join();
        }
    }
}

impl Drop for RuntimeHubServiceHandle {
    fn drop(&mut self) {
        self.stop();
    }
}

fn runtime_hub_service_slot() -> &'static Mutex<Option<RuntimeHubServiceHandle>> {
    static SLOT: OnceLock<Mutex<Option<RuntimeHubServiceHandle>>> = OnceLock::new();
    SLOT.get_or_init(|| Mutex::new(None))
}

#[cfg(test)]
pub(crate) fn runtime_hub_service_test_guard() -> &'static Mutex<()> {
    static GUARD: OnceLock<Mutex<()>> = OnceLock::new();
    GUARD.get_or_init(|| Mutex::new(()))
}

pub fn ensure_runtime_hub_service(
    identity: &StoreRuntimeHubIdentityRecord,
) -> Result<RuntimeHubServiceStatus, String> {
    let mut slot = runtime_hub_service_slot()
        .lock()
        .map_err(|_| "Failed to lock runtime hub service state".to_string())?;

    if let Some(handle) = slot.as_mut() {
        if handle.matches(identity) {
            return Ok(handle.status.clone());
        }
        handle.stop();
        *slot = None;
    }

    let handle = RuntimeHubServiceHandle::start(identity)?;
    let status = handle.status.clone();
    *slot = Some(handle);
    Ok(status)
}

pub fn clear_runtime_hub_service() {
    if let Ok(mut slot) = runtime_hub_service_slot().lock() {
        if let Some(handle) = slot.as_mut() {
            handle.stop();
        }
        *slot = None;
    }
}

fn serve_loopback(
    listener: TcpListener,
    snapshot: RuntimeHubServiceSnapshot,
    status: RuntimeHubServiceStatus,
    registry: Arc<Mutex<RuntimeSpokeRegistry>>,
    shutdown: Arc<AtomicBool>,
) {
    while !shutdown.load(Ordering::Relaxed) {
        match listener.accept() {
            Ok((stream, _)) => {
                let _ = respond_to_request(stream, &snapshot, &status, &registry);
            }
            Err(err) if err.kind() == std::io::ErrorKind::WouldBlock => {
                thread::sleep(Duration::from_millis(25));
            }
            Err(_) => {
                thread::sleep(Duration::from_millis(25));
            }
        }
    }
}

fn respond_to_request(
    mut stream: TcpStream,
    snapshot: &RuntimeHubServiceSnapshot,
    status: &RuntimeHubServiceStatus,
    registry: &Arc<Mutex<RuntimeSpokeRegistry>>,
) -> Result<(), String> {
    let request = read_http_request(&mut stream)?;
    let registry_guard = registry
        .lock()
        .map_err(|_| "Failed to lock runtime spoke registry".to_string())?;

    match (request.method.as_str(), request.path.as_str()) {
        ("GET", "/healthz") => {
            let response = json!({
                "status": "ready",
                "service": "store-runtime-hub",
                "protocol_version": "cp-017",
                "hub_device_id": snapshot.hub_device_id,
                "branch_id": snapshot.branch_id,
                "tenant_id": snapshot.tenant_id,
                "connected_spoke_count": registry_guard.connected_spoke_count(),
            });
            write_json_response(&mut stream, 200, &response.to_string())
        }
        ("GET", "/v1/spoke-manifest") => {
            let response = json!({
                "installation_id": snapshot.installation_id,
                "tenant_id": snapshot.tenant_id,
                "branch_id": snapshot.branch_id,
                "hub_device_id": snapshot.hub_device_id,
                "hub_device_code": snapshot.hub_device_code,
                "auth_mode": "spoke_runtime_token_pending",
                "issued_at": snapshot.issued_at,
                "supported_runtime_profiles": SUPPORTED_RUNTIME_PROFILES,
                "pairing_modes": SUPPORTED_PAIRING_MODES,
                "register_url": format!("{}/v1/spokes/register", status.base_url),
                "relay_base_url": format!("{}/v1/relay", status.base_url),
                "manifest_version": 1,
            });
            write_json_response(&mut stream, 200, &response.to_string())
        }
        ("POST", "/v1/spokes/activate") => {
            drop(registry_guard);
            let payload: SpokeActivationRequest = parse_json_body(&request.body)?;
            let activation = request_control_plane_spoke_activation(snapshot, &payload)?;
            let mut registry_guard = registry
                .lock()
                .map_err(|_| "Failed to lock runtime spoke registry".to_string())?;
            registry_guard.stage_activation(
                activation.activation_code.clone(),
                activation.pairing_mode.clone(),
                activation.runtime_profile.clone(),
                activation.expires_at.clone(),
            );
            write_json_response(
                &mut stream,
                200,
                &serde_json::to_string(&activation).map_err(|err| err.to_string())?,
            )
        }
        ("POST", "/v1/spokes/register") => {
            drop(registry_guard);
            let payload: SpokeRegistrationRequest = parse_json_body(&request.body)?;
            let mut registry_guard = registry
                .lock()
                .map_err(|_| "Failed to lock runtime spoke registry".to_string())?;
            let session = registry_guard
                .register_spoke(
                    &payload.activation_code,
                    &payload.installation_id,
                    &payload.runtime_kind,
                    &payload.runtime_profile,
                    payload.hostname,
                    payload.app_version,
                )
                .map_err(map_registry_error)?;
            drop(registry_guard);
            notify_spoke_observation(snapshot, &session);
            let response = json!({
                "spoke_device_id": session.spoke_device_id,
                "spoke_runtime_token": session.spoke_runtime_token,
                "expires_at": session.expires_at,
                "relay_base_url": format!("{}/v1/relay", status.base_url),
                "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
            });
            write_json_response(&mut stream, 200, &response.to_string())
        }
        ("POST", "/v1/spokes/heartbeat") => {
            drop(registry_guard);
            let payload: SpokeTokenRequest = parse_json_body(&request.body)?;
            let mut registry_guard = registry
                .lock()
                .map_err(|_| "Failed to lock runtime spoke registry".to_string())?;
            let session = registry_guard
                .heartbeat(&payload.spoke_runtime_token)
                .map_err(map_registry_error)?;
            let connected_spoke_count = registry_guard.connected_spoke_count();
            drop(registry_guard);
            notify_spoke_observation(snapshot, &session);
            let response = json!({
                "status": "connected",
                "spoke_device_id": session.spoke_device_id,
                "connected_spoke_count": connected_spoke_count,
                "expires_at": session.expires_at,
            });
            write_json_response(&mut stream, 200, &response.to_string())
        }
        ("POST", "/v1/spokes/disconnect") => {
            drop(registry_guard);
            let payload: SpokeTokenRequest = parse_json_body(&request.body)?;
            let mut registry_guard = registry
                .lock()
                .map_err(|_| "Failed to lock runtime spoke registry".to_string())?;
            let session = registry_guard
                .disconnect(&payload.spoke_runtime_token)
                .map_err(map_registry_error)?;
            let connected_spoke_count = registry_guard.connected_spoke_count();
            drop(registry_guard);
            notify_spoke_observation(snapshot, &session);
            let response = json!({
                "status": "disconnected",
                "spoke_device_id": session.spoke_device_id,
                "connected_spoke_count": connected_spoke_count,
            });
            write_json_response(&mut stream, 200, &response.to_string())
        }
        ("GET", "/v1/relay/runtime/status") => {
            let session = authorize_spoke_session(&request, &registry_guard)?;
            let response = json!({
                "status": "ready",
                "hub_device_id": snapshot.hub_device_id,
                "spoke_device_id": session.spoke_device_id,
                "runtime_profile": session.runtime_profile,
                "connected_spoke_count": registry_guard.connected_spoke_count(),
                "relay_operations": ALLOWED_RELAY_OPERATIONS.iter().map(|operation| json!({
                    "operation": operation,
                    "allowed": true,
                })).collect::<Vec<_>>(),
            });
            write_json_response(&mut stream, 200, &response.to_string())
        }
        ("GET", "/v1/relay/runtime/sync-status") => {
            let session = authorize_spoke_session(&request, &registry_guard)?;
            let response = json!({
                "status": "ready",
                "hub_device_id": snapshot.hub_device_id,
                "spoke_device_id": session.spoke_device_id,
                "connected_spoke_count": registry_guard.connected_spoke_count(),
                "registered_spoke_count": registry_guard.registered_spoke_count(),
            });
            write_json_response(&mut stream, 200, &response.to_string())
        }
        ("GET", "/v1/relay/runtime/print-jobs") => {
            let session = authorize_spoke_session(&request, &registry_guard)?;
            let response = json!({
                "status": "ready",
                "operation": "runtime.print_jobs.list",
                "spoke_device_id": session.spoke_device_id,
                "records": [],
            });
            write_json_response(&mut stream, 200, &response.to_string())
        }
        ("POST", "/v1/relay/runtime/print-jobs") => {
            let session = authorize_spoke_session(&request, &registry_guard)?;
            let response = json!({
                "status": "accepted",
                "operation": "runtime.print_jobs.submit",
                "spoke_device_id": session.spoke_device_id,
            });
            write_json_response(&mut stream, 202, &response.to_string())
        }
        _ if request.path.starts_with("/v1/relay/runtime/") => write_json_response(
            &mut stream,
            400,
            &json!({ "error": "unsupported_relay_operation" }).to_string(),
        ),
        _ => write_json_response(&mut stream, 404, &json!({ "error": "not_found" }).to_string()),
    }
}

fn read_http_request(stream: &mut TcpStream) -> Result<ParsedHttpRequest, String> {
    stream
        .set_read_timeout(Some(Duration::from_millis(500)))
        .map_err(|err| err.to_string())?;
    let mut bytes = Vec::new();
    loop {
        let mut chunk = [0_u8; 1024];
        match stream.read(&mut chunk) {
            Ok(0) => break,
            Ok(count) => {
                bytes.extend_from_slice(&chunk[..count]);
                if request_complete(&bytes) {
                    break;
                }
            }
            Err(err)
                if err.kind() == std::io::ErrorKind::WouldBlock
                    || err.kind() == std::io::ErrorKind::TimedOut =>
            {
                if !bytes.is_empty() {
                    break;
                }
                return Err(err.to_string());
            }
            Err(err) => return Err(err.to_string()),
        }
    }
    let request = String::from_utf8(bytes).map_err(|err| err.to_string())?;
    parse_http_request(&request)
}

fn request_complete(bytes: &[u8]) -> bool {
    let Some((header_length, headers)) = split_headers(bytes) else {
        return false;
    };
    let content_length = headers
        .lines()
        .find_map(|line| {
            line.split_once(':').and_then(|(name, value)| {
                if name.trim().eq_ignore_ascii_case("content-length") {
                    value.trim().parse::<usize>().ok()
                } else {
                    None
                }
            })
        })
        .unwrap_or(0);
    bytes.len() >= header_length + 4 + content_length
}

fn split_headers(bytes: &[u8]) -> Option<(usize, String)> {
    let separator = b"\r\n\r\n";
    bytes.windows(separator.len())
        .position(|window| window == separator)
        .map(|index| {
            (
                index,
                String::from_utf8_lossy(&bytes[..index]).to_string(),
            )
        })
}

fn parse_http_request(request: &str) -> Result<ParsedHttpRequest, String> {
    let (head, body) = request
        .split_once("\r\n\r\n")
        .ok_or_else(|| "Malformed HTTP request".to_string())?;
    let mut lines = head.lines();
    let request_line = lines.next().unwrap_or_default();
    let mut request_parts = request_line.split_whitespace();
    let method = request_parts
        .next()
        .ok_or_else(|| "Missing HTTP method".to_string())?
        .to_string();
    let path = request_parts
        .next()
        .ok_or_else(|| "Missing HTTP path".to_string())?
        .to_string();
    let headers = lines
        .filter_map(|line| {
            line.split_once(':')
                .map(|(name, value)| (name.trim().to_ascii_lowercase(), value.trim().to_string()))
        })
        .collect::<HashMap<_, _>>();

    Ok(ParsedHttpRequest {
        method,
        path,
        headers,
        body: body.to_string(),
    })
}

fn parse_json_body<T: DeserializeOwned>(body: &str) -> Result<T, String> {
    serde_json::from_str(body).map_err(|err| format!("Invalid JSON request payload: {err}"))
}

fn authorize_spoke_session(
    request: &ParsedHttpRequest,
    registry: &RuntimeSpokeRegistry,
) -> Result<RegisteredSpokeSession, String> {
    let Some(authorization) = request.headers.get("authorization") else {
        return Err("Missing authorization".to_string());
    };
    let Some(token) = authorization.strip_prefix("Bearer ") else {
        return Err("Missing authorization".to_string());
    };
    registry
        .session_for_token(token)
        .ok_or_else(|| "Invalid spoke runtime token".to_string())
}

fn request_control_plane_spoke_activation(
    snapshot: &RuntimeHubServiceSnapshot,
    payload: &SpokeActivationRequest,
) -> Result<ControlPlaneSpokeActivationResponse, String> {
    let client = Client::builder()
        .timeout(Duration::from_secs(2))
        .build()
        .map_err(|err| format!("Failed to prepare control-plane client: {err}"))?;
    let response = client
        .post(format!(
            "{}/v1/sync/spokes/activate",
            snapshot.control_plane_base_url
        ))
        .header("x-store-device-id", snapshot.hub_device_id.clone())
        .header("x-store-device-secret", snapshot.sync_access_secret.clone())
        .json(payload)
        .send()
        .map_err(|err| format!("Failed to issue spoke activation via control plane: {err}"))?;
    if !response.status().is_success() {
        return Err(format!(
            "Control plane rejected spoke activation: {}",
            response.status()
        ));
    }
    response
        .json::<ControlPlaneSpokeActivationResponse>()
        .map_err(|err| format!("Failed to decode spoke activation response: {err}"))
}

fn notify_spoke_observation(snapshot: &RuntimeHubServiceSnapshot, session: &RegisteredSpokeSession) {
    let client = match Client::builder().timeout(Duration::from_secs(2)).build() {
        Ok(client) => client,
        Err(_) => return,
    };
    let _ = client
        .post(format!(
            "{}/v1/sync/spokes/observe",
            snapshot.control_plane_base_url
        ))
        .header("x-store-device-id", snapshot.hub_device_id.clone())
        .header("x-store-device-secret", snapshot.sync_access_secret.clone())
        .json(&json!({
            "spokes": [
                {
                    "spoke_device_id": session.spoke_device_id,
                    "runtime_kind": session.runtime_kind,
                    "runtime_profile": session.runtime_profile,
                    "hostname": session.hostname,
                    "operating_system": null,
                    "app_version": session.app_version,
                    "connection_state": session.connection_state,
                    "last_local_sync_at": null
                }
            ]
        }))
        .send();
}

fn map_registry_error(error: &'static str) -> String {
    match error {
        "invalid_activation_code" => "Invalid spoke activation code".to_string(),
        "runtime_profile_mismatch" => "Activation is not valid for this runtime profile".to_string(),
        "invalid_spoke_runtime_token" => "Invalid spoke runtime token".to_string(),
        _ => "Runtime spoke registry error".to_string(),
    }
}

fn write_json_response(stream: &mut TcpStream, status_code: u16, body: &str) -> Result<(), String> {
    let reason = match status_code {
        200 => "OK",
        202 => "Accepted",
        400 => "Bad Request",
        401 => "Unauthorized",
        404 => "Not Found",
        _ => "Error",
    };
    let response = format!(
        "HTTP/1.1 {status_code} {reason}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        body.len(),
        body
    );
    stream
        .write_all(response.as_bytes())
        .map_err(|err| err.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime_hub_identity::StoreRuntimeHubIdentityRecord;
    use serde_json::{json, Value};
    use std::env;
    use std::io::{Read, Write};
    struct MockControlPlaneServer {
        base_url: String,
        shutdown: Arc<AtomicBool>,
        thread: Option<JoinHandle<()>>,
    }

    impl Drop for MockControlPlaneServer {
        fn drop(&mut self) {
            self.shutdown.store(true, Ordering::Relaxed);
            let _ = TcpStream::connect(self.base_url.trim_start_matches("http://"));
            if let Some(thread) = self.thread.take() {
                let _ = thread.join();
            }
        }
    }

    #[test]
    fn runtime_hub_service_registers_heartbeats_and_disconnects_spokes() {
        let _guard = hub_service_test_guard()
            .lock()
            .expect("lock hub service test guard");
        clear_runtime_hub_service();
        let mock_control_plane = start_mock_control_plane_server();
        let previous = env::var("STORE_CONTROL_PLANE_BASE_URL").ok();
        env::set_var("STORE_CONTROL_PLANE_BASE_URL", &mock_control_plane.base_url);

        let status = ensure_runtime_hub_service(&sample_identity()).expect("start hub service");
        let activation = http_post_json(
            &status.base_url,
            "/v1/spokes/activate",
            &json!({ "runtime_profile": "desktop_spoke", "pairing_mode": "qr" }),
            None,
        );
        let activation_code = response_json_value(&activation, "activation_code");
        let register_response = http_post_json(
            &status.base_url,
            "/v1/spokes/register",
            &json!({
                "activation_code": activation_code,
                "installation_id": "store-runtime-spoke-1",
                "runtime_kind": "packaged_desktop",
                "runtime_profile": "desktop_spoke",
                "hostname": "COUNTER-02",
                "app_version": "0.1.0"
            }),
            None,
        );
        assert!(register_response.contains("\"spoke_runtime_token\""));
        let spoke_token = response_json_value(&register_response, "spoke_runtime_token");

        let heartbeat_response = http_post_json(
            &status.base_url,
            "/v1/spokes/heartbeat",
            &json!({ "spoke_runtime_token": spoke_token }),
            None,
        );
        assert!(heartbeat_response.contains("\"connected_spoke_count\":1"));

        let disconnect_response = http_post_json(
            &status.base_url,
            "/v1/spokes/disconnect",
            &json!({ "spoke_runtime_token": spoke_token }),
            None,
        );
        assert!(disconnect_response.contains("\"status\":\"disconnected\""));

        restore_control_plane_origin(previous);
        clear_runtime_hub_service();
    }

    #[test]
    fn runtime_hub_service_rejects_non_allowlisted_relay_operations() {
        let _guard = hub_service_test_guard()
            .lock()
            .expect("lock hub service test guard");
        clear_runtime_hub_service();
        let mock_control_plane = start_mock_control_plane_server();
        let previous = env::var("STORE_CONTROL_PLANE_BASE_URL").ok();
        env::set_var("STORE_CONTROL_PLANE_BASE_URL", &mock_control_plane.base_url);

        let status = ensure_runtime_hub_service(&sample_identity()).expect("start hub service");
        let activation = http_post_json(
            &status.base_url,
            "/v1/spokes/activate",
            &json!({ "runtime_profile": "desktop_spoke", "pairing_mode": "qr" }),
            None,
        );
        let activation_code = response_json_value(&activation, "activation_code");
        let register_response = http_post_json(
            &status.base_url,
            "/v1/spokes/register",
            &json!({
                "activation_code": activation_code,
                "installation_id": "store-runtime-spoke-2",
                "runtime_kind": "packaged_desktop",
                "runtime_profile": "desktop_spoke",
                "hostname": "COUNTER-03",
                "app_version": "0.1.0"
            }),
            None,
        );
        let spoke_token = response_json_value(&register_response, "spoke_runtime_token");
        let authorization = format!("Bearer {spoke_token}");
        let relay_rejection =
            http_get(&status.base_url, "/v1/relay/runtime/unknown", Some(&authorization));
        assert!(relay_rejection.contains("\"error\":\"unsupported_relay_operation\""));

        restore_control_plane_origin(previous);
        clear_runtime_hub_service();
    }

    fn sample_identity() -> StoreRuntimeHubIdentityRecord {
        StoreRuntimeHubIdentityRecord {
            schema_version: 1,
            installation_id: "store-runtime-abcd1234efgh5678".to_string(),
            tenant_id: "tenant-acme".to_string(),
            branch_id: "branch-1".to_string(),
            device_id: "device-hub-1".to_string(),
            device_code: "BLR-HUB-01".to_string(),
            sync_access_secret: "hub-secret-1".to_string(),
            issued_at: "2026-04-14T08:00:00.000Z".to_string(),
        }
    }

    fn hub_service_test_guard() -> &'static Mutex<()> {
        super::runtime_hub_service_test_guard()
    }

    fn restore_control_plane_origin(previous: Option<String>) {
        if let Some(value) = previous {
            env::set_var("STORE_CONTROL_PLANE_BASE_URL", value);
        } else {
            env::remove_var("STORE_CONTROL_PLANE_BASE_URL");
        }
    }

    fn start_mock_control_plane_server() -> MockControlPlaneServer {
        let listener = TcpListener::bind("127.0.0.1:0").expect("bind mock control-plane server");
        listener
            .set_nonblocking(true)
            .expect("configure mock control-plane server");
        let port = listener.local_addr().expect("mock control-plane addr").port();
        let shutdown = Arc::new(AtomicBool::new(false));
        let shutdown_flag = Arc::clone(&shutdown);
        let thread = thread::spawn(move || {
            while !shutdown_flag.load(Ordering::Relaxed) {
                match listener.accept() {
                    Ok((mut stream, _)) => {
                        let mut buffer = [0_u8; 4096];
                        let bytes_read = stream.read(&mut buffer).expect("read mock request");
                        let request = String::from_utf8_lossy(&buffer[..bytes_read]);
                        let request_line = request.lines().next().unwrap_or_default();
                        let path = request_line.split_whitespace().nth(1).unwrap_or("/");
                        let body = match path {
                            "/v1/sync/spokes/activate" => json!({
                                "activation_code": "ACTV-ABCD-1234",
                                "pairing_mode": "qr",
                                "runtime_profile": "desktop_spoke",
                                "hub_device_id": "device-hub-1",
                                "expires_at": "2099-01-01T00:00:00Z"
                            })
                            .to_string(),
                            "/v1/sync/spokes/observe" => json!({
                                "observed_spoke_count": 1,
                                "connected_spoke_count": 1,
                                "last_local_spoke_sync_at": null
                            })
                            .to_string(),
                            _ => json!({ "error": "not_found" }).to_string(),
                        };
                        let status = if path == "/v1/sync/spokes/activate" || path == "/v1/sync/spokes/observe" {
                            "200 OK"
                        } else {
                            "404 Not Found"
                        };
                        let response = format!(
                            "HTTP/1.1 {status}\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                            body.len(),
                            body
                        );
                        stream
                            .write_all(response.as_bytes())
                            .expect("write mock response");
                    }
                    Err(err) if err.kind() == std::io::ErrorKind::WouldBlock => {
                        thread::sleep(Duration::from_millis(20));
                    }
                    Err(_) => {
                        thread::sleep(Duration::from_millis(20));
                    }
                }
            }
        });

        MockControlPlaneServer {
            base_url: format!("http://127.0.0.1:{port}"),
            shutdown,
            thread: Some(thread),
        }
    }

    fn http_post_json(base_url: &str, path: &str, payload: &Value, authorization: Option<&str>) -> String {
        let host = base_url.trim_start_matches("http://");
        let mut stream = TcpStream::connect(host).expect("connect to hub service");
        let body = payload.to_string();
        let authorization_header = authorization
            .map(|value| format!("Authorization: {value}\r\n"))
            .unwrap_or_default();
        let request = format!(
            "POST {path} HTTP/1.1\r\nHost: {host}\r\nContent-Type: application/json\r\nContent-Length: {}\r\n{authorization_header}Connection: close\r\n\r\n{body}",
            body.len(),
        );
        stream.write_all(request.as_bytes()).expect("write request");
        let mut response = String::new();
        stream.read_to_string(&mut response).expect("read response");
        response
    }

    fn http_get(base_url: &str, path: &str, authorization: Option<&str>) -> String {
        let host = base_url.trim_start_matches("http://");
        let mut stream = TcpStream::connect(host).expect("connect to hub service");
        let authorization_header = authorization
            .map(|value| format!("Authorization: {value}\r\n"))
            .unwrap_or_default();
        let request = format!(
            "GET {path} HTTP/1.1\r\nHost: {host}\r\n{authorization_header}Connection: close\r\n\r\n"
        );
        stream.write_all(request.as_bytes()).expect("write request");
        let mut response = String::new();
        stream.read_to_string(&mut response).expect("read response");
        response
    }

    fn response_json_value(response: &str, key: &str) -> String {
        let body = response
            .split_once("\r\n\r\n")
            .map(|(_, body)| body)
            .expect("response body");
        serde_json::from_str::<Value>(body)
            .expect("response json")[key]
            .as_str()
            .expect("response string field")
            .to_string()
    }
}
