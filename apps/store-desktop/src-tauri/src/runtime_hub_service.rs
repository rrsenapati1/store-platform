use crate::runtime_hub_identity::StoreRuntimeHubIdentityRecord;
use serde::Serialize;
use serde_json::json;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex, OnceLock};
use std::thread::{self, JoinHandle};
use std::time::Duration;

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
}

#[derive(Debug, Serialize)]
struct RuntimeHubManifest<'a> {
    installation_id: &'a str,
    tenant_id: &'a str,
    branch_id: &'a str,
    hub_device_id: &'a str,
    hub_device_code: &'a str,
    auth_mode: &'a str,
    issued_at: &'a str,
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
        let shutdown = Arc::new(AtomicBool::new(false));
        let shutdown_flag = Arc::clone(&shutdown);
        let server_snapshot = snapshot.clone();
        let thread = thread::spawn(move || serve_loopback(listener, server_snapshot, shutdown_flag));

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

fn serve_loopback(listener: TcpListener, snapshot: RuntimeHubServiceSnapshot, shutdown: Arc<AtomicBool>) {
    while !shutdown.load(Ordering::Relaxed) {
        match listener.accept() {
            Ok((stream, _)) => {
                let _ = respond_to_request(stream, &snapshot);
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

fn respond_to_request(mut stream: TcpStream, snapshot: &RuntimeHubServiceSnapshot) -> Result<(), String> {
    stream
        .set_read_timeout(Some(Duration::from_millis(250)))
        .map_err(|err| err.to_string())?;
    let mut buffer = [0_u8; 2048];
    let bytes_read = stream.read(&mut buffer).map_err(|err| err.to_string())?;
    let request = String::from_utf8_lossy(&buffer[..bytes_read]);
    let request_line = request.lines().next().unwrap_or_default();
    let path = request_line.split_whitespace().nth(1).unwrap_or("/");

    match path {
        "/healthz" => write_json_response(
            &mut stream,
            200,
            &json!({
                "status": "ready",
                "service": "store-runtime-hub",
                "hub_device_id": snapshot.hub_device_id,
                "branch_id": snapshot.branch_id,
                "tenant_id": snapshot.tenant_id,
            })
            .to_string(),
        ),
        "/v1/spoke-manifest" => {
            let manifest = RuntimeHubManifest {
                installation_id: &snapshot.installation_id,
                tenant_id: &snapshot.tenant_id,
                branch_id: &snapshot.branch_id,
                hub_device_id: &snapshot.hub_device_id,
                hub_device_code: &snapshot.hub_device_code,
                auth_mode: "spoke_runtime_token_pending",
                issued_at: &snapshot.issued_at,
            };
            let body = serde_json::to_string(&manifest).map_err(|err| err.to_string())?;
            write_json_response(&mut stream, 200, &body)
        }
        _ => write_json_response(
            &mut stream,
            404,
            &json!({ "error": "not_found" }).to_string(),
        ),
    }
}

fn write_json_response(stream: &mut TcpStream, status_code: u16, body: &str) -> Result<(), String> {
    let reason = match status_code {
        200 => "OK",
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

